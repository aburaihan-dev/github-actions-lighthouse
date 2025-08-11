#!/bin/bash
set -e

# GitHub Actions Monitor Service Installation Script

SERVICE_NAME="github-actions-monitor"
SERVICE_USER="github-monitor"
SERVICE_GROUP="github-monitor"
INSTALL_DIR="/opt/github-actions-monitor"

# Legacy directories to clean up
LEGACY_CONFIG_DIR="/etc/github-actions-monitor"
LEGACY_LOG_DIR="/var/log/github-actions-monitor"
LEGACY_LIB_DIR="/var/lib/github-actions-monitor"
LEGACY_RUN_DIR="/var/run/github-actions-monitor"

echo "=== GitHub Actions Monitor Service Installation ==="

# Function to remove previous installations
remove_previous_installation() {
    echo "Checking for previous installations..."
    
    # Stop service if running
    if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        echo "Stopping existing service..."
        systemctl stop "$SERVICE_NAME"
    fi
    
    # Disable service if enabled
    if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
        echo "Disabling existing service..."
        systemctl disable "$SERVICE_NAME"
    fi
    
    # Remove systemd service file
    if [[ -f "/etc/systemd/system/$SERVICE_NAME.service" ]]; then
        echo "Removing systemd service file..."
        rm -f "/etc/systemd/system/$SERVICE_NAME.service"
        systemctl daemon-reload
    fi
    
    # Remove legacy directories
    for dir in "$LEGACY_CONFIG_DIR" "$LEGACY_LOG_DIR" "$LEGACY_LIB_DIR" "$LEGACY_RUN_DIR"; do
        if [[ -d "$dir" ]]; then
            echo "Removing legacy directory: $dir"
            rm -rf "$dir"
        fi
    done
    
    # Remove logrotate configuration
    if [[ -f "/etc/logrotate.d/github-actions-monitor" ]]; then
        echo "Removing logrotate configuration..."
        rm -f "/etc/logrotate.d/github-actions-monitor"
    fi
    
    # Clean up existing installation directory
    if [[ -d "$INSTALL_DIR" ]]; then
        echo "Removing existing installation directory: $INSTALL_DIR"
        rm -rf "$INSTALL_DIR"
    fi
    
    echo "✅ Previous installation cleanup completed"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root (use sudo)"
    exit 1
fi

# Remove any previous installations first
remove_previous_installation

# Detect package manager
if command -v apt-get &> /dev/null; then
    PACKAGE_MANAGER="apt"
elif command -v yum &> /dev/null; then
    PACKAGE_MANAGER="yum"
elif command -v dnf &> /dev/null; then
    PACKAGE_MANAGER="dnf"
else
    echo "Unsupported package manager. Please install Python 3.8+ and pip manually."
    exit 1
fi

echo "Detected package manager: $PACKAGE_MANAGER"

# Install system dependencies
echo "Installing system dependencies..."
case $PACKAGE_MANAGER in
    apt)
        apt-get update
        apt-get install -y python3 python3-venv python3-pip git curl
        ;;
    yum)
        yum install -y python3 python3-venv python3-pip git curl
        ;;
    dnf)
        dnf install -y python3 python3-venv python3-pip git curl
        ;;
esac

# Create service user and group
echo "Creating service user and group..."
if ! getent group "$SERVICE_GROUP" &>/dev/null; then
    groupadd --system "$SERVICE_GROUP"
    echo "Created group: $SERVICE_GROUP"
else
    echo "Group $SERVICE_GROUP already exists"
fi

if ! getent passwd "$SERVICE_USER" &>/dev/null; then
    useradd --system --gid "$SERVICE_GROUP" --home-dir "$INSTALL_DIR" \
            --shell /bin/false --create-home "$SERVICE_USER"
    echo "Created user: $SERVICE_USER"
else
    echo "User $SERVICE_USER already exists"
fi

# Setup kubectl access for github-monitor user
echo "Setting up kubectl access for $SERVICE_USER..."

# Check if kubectl is installed
if command -v kubectl &> /dev/null; then
    echo "kubectl found, setting up access..."
    
    # Create sudoers file for kubectl access
    cat > "/etc/sudoers.d/$SERVICE_USER" << EOF
# Allow $SERVICE_USER to run kubectl commands without password
$SERVICE_USER ALL=(root) NOPASSWD: /usr/local/bin/kubectl, /usr/bin/kubectl
EOF
    
    # Set proper permissions on sudoers file
    chmod 440 "/etc/sudoers.d/$SERVICE_USER"
    echo "✅ kubectl sudo access configured for $SERVICE_USER"
    
    # Setup kubeconfig if available
    if [[ -f /root/.kube/config ]]; then
        echo "Setting up kubeconfig access for $SERVICE_USER..."
        # Instead of copying to user home, use root's kubeconfig directly
        # The systemd service will be configured to use /root/.kube/config
        echo "✅ Will use root's kubeconfig: /root/.kube/config"
        
        # Ensure the github-monitor user can read the root kubeconfig
        # Add github-monitor to root group or create a kubectl group
        if ! getent group kubectl &>/dev/null; then
            groupadd kubectl
            echo "Created kubectl group"
        fi
        
        # Add github-monitor to kubectl group
        usermod -a -G kubectl "$SERVICE_USER"
        
        # Set group ownership on kubeconfig to allow kubectl group access
        chgrp kubectl /root/.kube/config
        chmod 640 /root/.kube/config
        echo "✅ kubeconfig access configured for $SERVICE_USER via kubectl group"
        
    elif [[ -f /etc/kubernetes/admin.conf ]]; then
        echo "Setting up kubeconfig from admin.conf for $SERVICE_USER..."
        # Use admin.conf directly instead of copying
        echo "✅ Will use admin.conf: /etc/kubernetes/admin.conf"
        
        # Ensure the github-monitor user can read admin.conf
        if ! getent group kubectl &>/dev/null; then
            groupadd kubectl
            echo "Created kubectl group"
        fi
        
        usermod -a -G kubectl "$SERVICE_USER"
        chgrp kubectl /etc/kubernetes/admin.conf
        chmod 640 /etc/kubernetes/admin.conf
        echo "✅ admin.conf access configured for $SERVICE_USER via kubectl group"
        
    else
        echo "⚠️  No kubeconfig found at /root/.kube/config or /etc/kubernetes/admin.conf"
        echo "    You may need to manually configure kubeconfig access"
    fi
    
    # Test kubectl access
    echo "Testing kubectl access..."
    if sudo -u "$SERVICE_USER" kubectl version --client &>/dev/null; then
        echo "✅ kubectl client access working"
    else
        echo "⚠️  kubectl client test failed"
    fi
    
else
    echo "⚠️  kubectl not found. Install kubectl first if you need Kubernetes integration."
    echo "    The service will still work for other commands."
fi

# Create single installation directory with all subdirectories
echo "Creating installation directory structure..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/config"
mkdir -p "$INSTALL_DIR/logs"
mkdir -p "$INSTALL_DIR/data"
mkdir -p "$INSTALL_DIR/run"

# Set ownership and permissions for the entire directory
chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"
chmod -R 755 "$INSTALL_DIR"
chmod 750 "$INSTALL_DIR/logs" "$INSTALL_DIR/data" "$INSTALL_DIR/run"

# Copy application files
echo "Installing application files..."
cp github_actions_monitor.py "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/"

# Copy test suite for validation
if [[ -d "src/tests" ]]; then
    echo "Installing test suite..."
    mkdir -p "$INSTALL_DIR/src"
    cp -r src/tests "$INSTALL_DIR/src/"
    if [[ -f "run_tests.py" ]]; then
        cp run_tests.py "$INSTALL_DIR/"
        echo "Test suite and runner installed for validation"
    else
        echo "Test suite installed (run_tests.py not found)"
    fi
else
    echo "⚠️  Test suite not found - skipping test installation"
fi

# Set ownership for application files
chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"/*

# Create Python virtual environment
echo "Creating Python virtual environment..."
if [[ -d "$INSTALL_DIR/venv" ]]; then
    echo "Virtual environment already exists at $INSTALL_DIR/venv"
    echo "Checking if it's functional..."
    
    # Test if existing venv is working
    if sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/python" --version &>/dev/null; then
        echo "✅ Existing virtual environment is functional"
        VENV_EXISTS=true
    else
        echo "⚠️  Existing virtual environment appears broken, recreating..."
        sudo -u "$SERVICE_USER" rm -rf "$INSTALL_DIR/venv"
        VENV_EXISTS=false
    fi
else
    echo "Creating new virtual environment..."
    VENV_EXISTS=false
fi

if [[ "$VENV_EXISTS" != "true" ]]; then
    sudo -u "$SERVICE_USER" python3 -m venv "$INSTALL_DIR/venv"
    echo "✅ Virtual environment created successfully"
fi

# Verify venv creation
if [[ ! -f "$INSTALL_DIR/venv/bin/python" ]]; then
    echo "❌ Error: Virtual environment creation failed"
    exit 1
fi

# Install Python dependencies
echo "Installing Python dependencies..."

# Always upgrade pip first
echo "Upgrading pip..."
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip

# Check if requirements are already installed
echo "Checking existing Python packages..."
if sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" list | grep -E "(PyGithub|PyYAML|python-dotenv)" &>/dev/null; then
    echo "Some Python packages already installed, checking versions..."
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" list | grep -E "(PyGithub|PyYAML|python-dotenv)" || true
    echo "Installing/upgrading from requirements.txt..."
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade -r "$INSTALL_DIR/requirements.txt"
else
    echo "Installing Python packages from requirements.txt..."
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"
fi

# Verify critical packages are installed
echo "Verifying installation..."
if sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/python" -c "import github, yaml; print('✅ Critical packages verified')" 2>/dev/null; then
    echo "✅ Python dependencies installed successfully"
else
    echo "⚠️  Some Python dependencies may have installation issues"
    echo "You can manually verify with:"
    echo "  sudo -u $SERVICE_USER $INSTALL_DIR/venv/bin/pip list"
fi

# Copy and customize configuration
echo "Installing configuration..."
if [[ ! -f "$INSTALL_DIR/config/config.yaml" ]]; then
    cp config.yaml "$INSTALL_DIR/config/"
    chown "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/config/config.yaml"
    chmod 640 "$INSTALL_DIR/config/config.yaml"
    echo "Configuration file installed: $INSTALL_DIR/config/config.yaml"
    echo "*** IMPORTANT: Edit $INSTALL_DIR/config/config.yaml with your GitHub repository and token settings ***"
    
    # Validate configuration structure
    echo "Validating configuration structure..."
    if python3 -c "import yaml; config = yaml.safe_load(open('$INSTALL_DIR/config/config.yaml')); print('✅ YAML syntax valid')" 2>/dev/null; then
        echo "✅ Configuration file has valid YAML syntax"
        
        # Check for new command structure
        if python3 -c "import yaml; config = yaml.safe_load(open('$INSTALL_DIR/config/config.yaml')); assert 'commands' in config and 'definitions' in config['commands'] and 'execution_map' in config['commands']; print('✅ New command structure detected')" 2>/dev/null; then
            echo "✅ Configuration uses new command structure with named commands"
        else
            echo "⚠️  Configuration may be using legacy command structure"
        fi
    else
        echo "⚠️  Configuration file may have YAML syntax issues"
    fi
else
    echo "Configuration file already exists: $INSTALL_DIR/config/config.yaml"
    echo "*** Checking if upgrade is needed for new command structure ***"
    
    # Check if existing config needs upgrading
    if python3 -c "import yaml; config = yaml.safe_load(open('$INSTALL_DIR/config/config.yaml')); assert 'commands' in config and 'definitions' in config['commands']" 2>/dev/null; then
        echo "✅ Configuration already uses new command structure"
    else
        echo "⚠️  Configuration may need upgrading to new command structure"
        echo "    Backup existing config and compare with new format in:"
        echo "    $(pwd)/config.yaml"
    fi
fi

# Create environment file template
if [[ ! -f "$INSTALL_DIR/config/environment" ]]; then
    cat > "$INSTALL_DIR/config/environment" << 'EOF'
# GitHub Actions Monitor Environment Variables
# Uncomment and set your GitHub token here, or set it in config.yaml
# GITHUB_TOKEN=your_github_personal_access_token_here
EOF
    chown "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/config/environment"
    chmod 600 "$INSTALL_DIR/config/environment"
    echo "Environment file template created: $INSTALL_DIR/config/environment"
fi

# Copy .env example file to installation directory
if [[ -f ".env.example" ]]; then
    cp .env.example "$INSTALL_DIR/.env.example"
    chown "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/.env.example"
    echo ".env example file copied to: $INSTALL_DIR/.env.example"
fi

# Install systemd service
echo "Installing systemd service..."

# Create updated systemd service file
cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=GitHub Actions Monitor
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/github_actions_monitor.py --config $INSTALL_DIR/config/config.yaml
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Environment - Use root's kubeconfig or admin.conf
Environment=PYTHONPATH=$INSTALL_DIR
Environment=KUBECONFIG=/root/.kube/config:/etc/kubernetes/admin.conf
EnvironmentFile=-$INSTALL_DIR/config/environment
EnvironmentFile=-$INSTALL_DIR/.env

# Security settings
NoNewPrivileges=false
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$INSTALL_DIR/logs $INSTALL_DIR/data $INSTALL_DIR/run
SupplementaryGroups=kubectl
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

# Create log rotation configuration
echo "Setting up log rotation..."
cat > /etc/logrotate.d/github-actions-monitor << EOF
$INSTALL_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    su $SERVICE_USER $SERVICE_GROUP
}
EOF

echo ""
echo "=== Installation Complete ==="
echo ""
echo "✅ Single-directory installation completed at: $INSTALL_DIR"
echo ""
echo "Directory structure:"
echo "  $INSTALL_DIR/                 # Main installation directory"
echo "  ├── config/                   # Configuration files"
echo "  │   ├── config.yaml          # Main configuration"
echo "  │   └── environment          # Environment variables"
echo "  ├── logs/                     # Log files"
echo "  ├── data/                     # Application data and state"
echo "  ├── run/                      # Runtime files"
echo "  ├── venv/                     # Python virtual environment"
echo "  ├── src/tests/                # Test suite"
echo "  └── *.py                      # Application files"
echo ""
echo "Next steps:"
echo "1. Edit the configuration file:"
echo "   sudo nano $INSTALL_DIR/config/config.yaml"
echo ""
echo "2. Set your GitHub token (choose one method):"
echo "   a) Create a .env file in the application directory:"
echo "      sudo cp $INSTALL_DIR/.env.example $INSTALL_DIR/.env"
echo "      sudo nano $INSTALL_DIR/.env"
echo "   b) Set GITHUB_TOKEN environment variable in:"
echo "      sudo nano $INSTALL_DIR/config/environment"
echo "   c) Or edit the token directly in config.yaml (not recommended)"
echo ""
echo "3. Customize the commands to execute on successful workflows in config.yaml"
echo "   The new format supports named commands and repository-branch mapping:"
echo "   - Define commands in 'commands.definitions'"
echo "   - Map commands to repositories/branches in 'commands.execution_map'"
echo ""
echo "   Note: kubectl commands are configured to use 'sudo kubectl' for security."
echo "   The $SERVICE_USER user has been granted sudo access to kubectl commands."
echo ""
echo "4. Test kubectl access (if using Kubernetes commands):"
echo "   sudo -u $SERVICE_USER sudo kubectl version --client"
echo "   sudo -u $SERVICE_USER sudo kubectl get nodes"
echo ""
echo "   Note: $SERVICE_USER uses root's kubeconfig via kubectl group membership"
echo ""
echo "5. Test your configuration (recommended):"
echo "   cd $INSTALL_DIR && sudo -u $SERVICE_USER ./venv/bin/python run_tests.py quick"
echo ""
echo "6. Enable and start the service:"
echo "   sudo systemctl enable $SERVICE_NAME"
echo "   sudo systemctl start $SERVICE_NAME"
echo ""
echo "7. Check service status:"
echo "   sudo systemctl status $SERVICE_NAME"
echo ""
echo "8. View logs:"
echo "   sudo journalctl -u $SERVICE_NAME -f"
echo "   sudo tail -f $INSTALL_DIR/logs/monitor.log"
echo ""
echo "Testing and Validation:"
echo "  - Quick test: cd $INSTALL_DIR && sudo -u $SERVICE_USER ./venv/bin/python run_tests.py quick"
echo "  - Full tests: cd $INSTALL_DIR && sudo -u $SERVICE_USER ./venv/bin/python run_tests.py all"
echo "  - System overview: cd $INSTALL_DIR && sudo -u $SERVICE_USER ./venv/bin/python run_tests.py overview"
echo ""
echo "Configuration files:"
echo "  - Service config: $INSTALL_DIR/config/config.yaml"
echo "  - Environment: $INSTALL_DIR/config/environment"
echo "  - Application .env: $INSTALL_DIR/.env"
echo ""
echo "Data and logs:"
echo "  - Logs: $INSTALL_DIR/logs/monitor.log"
echo "  - State: $INSTALL_DIR/data/state.json"
echo "  - Health: $INSTALL_DIR/run/health"
echo ""
echo "Service management:"
echo "  - Start: sudo systemctl start $SERVICE_NAME"
echo "  - Stop: sudo systemctl stop $SERVICE_NAME"
echo "  - Restart: sudo systemctl restart $SERVICE_NAME"
echo "  - Status: sudo systemctl status $SERVICE_NAME"
echo "  - Logs: sudo journalctl -u $SERVICE_NAME"
echo ""

# Make script executable
chmod +x "$INSTALL_DIR/github_actions_monitor.py"

# Optional: Run a quick validation test
echo ""
echo "=== Running Configuration Validation ==="
if [[ -f "$INSTALL_DIR/run_tests.py" ]]; then
    echo "Testing basic configuration..."
    cd "$INSTALL_DIR"
    
    # Test using the virtual environment
    if sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/python" -c "import sys; sys.path.insert(0, '.'); from src.tests.test_utils import check_dependencies; deps = check_dependencies(); print('Dependencies check completed')" 2>/dev/null; then
        echo "✅ Dependencies validation completed"
        echo "✅ Virtual environment and test suite are working"
    else
        echo "⚠️  Some dependencies may need attention"
        echo "You can manually test with:"
        echo "  cd $INSTALL_DIR && sudo -u $SERVICE_USER ./venv/bin/python run_tests.py quick"
    fi
    
    echo ""
    echo "To run full validation after configuring GitHub token:"
    echo "  cd $INSTALL_DIR && sudo -u $SERVICE_USER ./venv/bin/python run_tests.py quick"
else
    echo "Test suite not available - manual testing required"
    echo "You can test the basic installation with:"
    echo "  sudo -u $SERVICE_USER $INSTALL_DIR/venv/bin/python $INSTALL_DIR/github_actions_monitor.py --help"
fi

echo ""
echo "🎉 Single-directory installation completed!"
echo "   Everything is contained in: $INSTALL_DIR"
echo "   Previous installations have been cleaned up."
