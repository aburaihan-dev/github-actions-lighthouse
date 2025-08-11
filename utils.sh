#!/bin/bash
# GitHub Actions Monitor - Utilities and Fixes
# Combines various utility functions and fixes into one script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This command must be run as root (use sudo)"
        exit 1
    fi
}

# Install Python dependencies
install_dependencies() {
    echo "=== Installing Python Dependencies ==="
    echo ""
    
    print_info "Updating package list..."
    if [[ $EUID -eq 0 ]]; then
        apt update
        print_status "Package list updated"
    else
        print_warning "Skipping package update (requires root)"
    fi
    
    # Install pip if not available
    print_info "Checking for pip..."
    if command -v pip3 &> /dev/null; then
        print_status "pip3 is available"
    elif command -v pip &> /dev/null; then
        print_status "pip is available"
    else
        print_info "Installing pip..."
        if [[ $EUID -eq 0 ]]; then
            apt install -y python3-pip
            print_status "pip3 installed"
        else
            print_error "Cannot install pip without root permissions"
            exit 1
        fi
    fi
    
    # Install dependencies
    print_info "Installing Python dependencies..."
    if [[ -f "requirements.txt" ]]; then
        if command -v pip3 &> /dev/null; then
            pip3 install -r requirements.txt --user
        elif command -v pip &> /dev/null; then
            pip install -r requirements.txt --user
        fi
        print_status "Dependencies installed from requirements.txt"
    else
        # Install core dependencies individually
        if command -v pip3 &> /dev/null; then
            pip3 install PyGithub PyYAML --user
        elif command -v pip &> /dev/null; then
            pip install PyGithub PyYAML --user
        fi
        print_status "Core dependencies installed"
    fi
    
    # Test imports
    print_info "Testing imports..."
    if python3 -c "import github, yaml, concurrent.futures; print('All imports successful')" 2>/dev/null; then
        print_status "All required dependencies are working"
    else
        print_error "Some dependencies failed to import"
        exit 1
    fi
}

# Fix kubectl access issues
fix_kubectl() {
    echo "=== Fixing kubectl Access ==="
    echo ""
    
    check_root
    
    print_info "Checking kubectl configuration..."
    
    # Check if kubectl is installed
    if ! command -v kubectl &>/dev/null; then
        print_error "kubectl is not installed"
        print_info "Install kubectl first, then re-run this script"
        exit 1
    fi
    
    # Fix kubeconfig permissions
    print_info "Fixing kubeconfig permissions..."
    
    # Try different kubeconfig locations
    if [[ -f "/etc/kubernetes/admin.conf" ]]; then
        chmod 644 /etc/kubernetes/admin.conf
        print_status "Fixed /etc/kubernetes/admin.conf permissions"
        
        # Test kubectl access
        if kubectl --kubeconfig=/etc/kubernetes/admin.conf version --client &>/dev/null; then
            print_status "kubectl access working"
        else
            print_warning "kubectl still has issues"
        fi
    elif [[ -f "/root/.kube/config" ]]; then
        chmod 644 /root/.kube/config
        print_status "Fixed /root/.kube/config permissions"
    else
        print_error "No kubeconfig file found"
        print_info "Expected locations:"
        print_info "  - /etc/kubernetes/admin.conf"
        print_info "  - /root/.kube/config"
        exit 1
    fi
    
    # Create kubectl wrapper for service user
    print_info "Setting up kubectl access for github-monitor user..."
    
    # Ensure service user exists
    if id github-monitor &>/dev/null; then
        print_status "github-monitor user exists"
        
        # Add to sudoers for kubectl
        SUDOERS_FILE="/etc/sudoers.d/github-monitor"
        cat > "$SUDOERS_FILE" << 'EOF'
# Allow github-monitor user to run kubectl
github-monitor ALL=(ALL) NOPASSWD: /usr/bin/kubectl
EOF
        chmod 440 "$SUDOERS_FILE"
        print_status "Sudoers configured for kubectl access"
    else
        print_error "github-monitor user not found"
        print_info "Run the main install.sh script first"
        exit 1
    fi
    
    print_status "kubectl access configured"
}

# Fix sudo privileges issue
fix_sudo() {
    echo "=== Fixing Sudo Privileges ==="
    echo ""
    
    check_root
    
    print_info "Fixing 'no new privileges' sudo issue..."
    
    # Update systemd service to allow privilege escalation
    SERVICE_FILE="/etc/systemd/system/github-actions-monitor.service"
    
    if [[ -f "$SERVICE_FILE" ]]; then
        # Check if NoNewPrivileges is set to true
        if grep -q "NoNewPrivileges=true" "$SERVICE_FILE"; then
            print_info "Updating service configuration..."
            sed -i 's/NoNewPrivileges=true/NoNewPrivileges=false/' "$SERVICE_FILE"
            systemctl daemon-reload
            print_status "Service configuration updated"
        else
            print_status "Service configuration already correct"
        fi
    else
        print_error "Service file not found: $SERVICE_FILE"
        exit 1
    fi
    
    # Restart service to apply changes
    print_info "Restarting service..."
    systemctl restart github-actions-monitor
    sleep 2
    
    if systemctl is-active --quiet github-actions-monitor; then
        print_status "Service restarted successfully"
    else
        print_error "Service restart failed"
        systemctl status github-actions-monitor --no-pager -l
        exit 1
    fi
    
    print_status "Sudo privileges fixed"
}

# Validate and deploy YAML configuration
deploy_yaml() {
    echo "=== Deploy YAML Configuration ==="
    echo ""
    
    check_root
    
    # Validate YAML syntax
    print_info "Validating YAML syntax..."
    if python3 -c "import yaml; yaml.safe_load(open('config.yaml')); print('YAML syntax is valid')" 2>/dev/null; then
        print_status "YAML syntax validation passed"
    else
        print_error "YAML syntax validation failed"
        python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"
        exit 1
    fi
    
    # Check for placeholder values
    print_info "Checking for placeholder values..."
    if grep -q "YOUR_WHATSAPP_GROUP_ID" config.yaml; then
        print_warning "Configuration contains placeholder values"
        print_info "Please update config.yaml with your actual values"
        print_info "Replace: YOUR_WHATSAPP_GROUP_ID@g.us"
        print_info "Replace: YOUR_WHATSAPP_API_SERVER"
        print_info "Replace: your-org/your-repo"
    fi
    
    # Deploy configuration
    print_info "Deploying configuration..."
    INSTALL_DIR="/opt/github-actions-monitor"
    
    if [[ -d "$INSTALL_DIR" ]]; then
        # Backup existing config
        if [[ -f "$INSTALL_DIR/config/config.yaml" ]]; then
            cp "$INSTALL_DIR/config/config.yaml" "$INSTALL_DIR/config/config.yaml.backup.$(date +%Y%m%d_%H%M%S)"
            print_status "Existing configuration backed up"
        fi
        
        # Deploy new config
        cp config.yaml "$INSTALL_DIR/config/"
        chown github-monitor:github-monitor "$INSTALL_DIR/config/config.yaml"
        print_status "Configuration deployed"
        
        # Restart service
        print_info "Restarting service to apply changes..."
        systemctl restart github-actions-monitor
        sleep 2
        
        if systemctl is-active --quiet github-actions-monitor; then
            print_status "Service restarted successfully"
        else
            print_error "Service restart failed"
            exit 1
        fi
    else
        print_error "Installation directory not found: $INSTALL_DIR"
        print_info "Run ./install.sh first"
        exit 1
    fi
    
    print_status "YAML configuration deployed"
}

# Apply all common fixes
apply_all_fixes() {
    echo "=== Applying All Common Fixes ==="
    echo ""
    
    check_root
    
    print_info "This will apply all common fixes in sequence..."
    echo ""
    
    # Fix kubectl access
    print_info "1. Fixing kubectl access..."
    fix_kubectl
    echo ""
    
    # Fix sudo privileges
    print_info "2. Fixing sudo privileges..."
    fix_sudo
    echo ""
    
    # Final service restart
    print_info "3. Final service restart..."
    systemctl restart github-actions-monitor
    sleep 3
    
    if systemctl is-active --quiet github-actions-monitor; then
        print_status "All fixes applied successfully"
        print_info "Service is running normally"
    else
        print_error "Service failed to start after fixes"
        systemctl status github-actions-monitor --no-pager -l
        exit 1
    fi
    
    print_status "All common fixes applied"
}

# Pre-commit security check
security_check() {
    echo "=== Security Check ==="
    echo ""
    
    print_info "Checking for sensitive data..."
    
    # Check .env file
    if [[ -f ".env" ]]; then
        if grep -q "your_github_personal_access_token_here" .env; then
            print_status ".env file is safe (contains placeholder)"
        else
            print_warning ".env file may contain real token"
        fi
    else
        print_info ".env file not found"
    fi
    
    # Check config files for placeholders
    if [[ -f "config.yaml" ]]; then
        if grep -q "YOUR_WHATSAPP_GROUP_ID" config.yaml; then
            print_status "config.yaml contains safe placeholders"
        else
            print_warning "config.yaml may contain real values"
        fi
    fi
    
    # Check for sensitive patterns
    print_info "Scanning for sensitive patterns..."
    if find . -name "*.yaml" -o -name "*.py" -o -name "*.sh" -o -name "*.md" | \
       xargs grep -l "github_pat_\|120363\|172\.16" 2>/dev/null; then
        print_error "Sensitive data found in files!"
        print_info "Review the above files before committing"
    else
        print_status "No sensitive data patterns found"
    fi
    
    # Check .gitignore
    if [[ -f ".gitignore" ]]; then
        print_status ".gitignore file exists"
    else
        print_warning ".gitignore file missing"
    fi
    
    print_status "Security check complete"
}

# Show usage
show_usage() {
    echo "GitHub Actions Monitor Utilities"
    echo ""
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  deps           Install Python dependencies"
    echo "  kubectl        Fix kubectl access issues"
    echo "  sudo           Fix sudo privileges issues"
    echo "  yaml           Validate and deploy YAML config"
    echo "  fix-all        Apply all common fixes"
    echo "  security       Run security check for sensitive data"
    echo "  help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 deps              # Install Python dependencies"
    echo "  sudo $0 kubectl      # Fix kubectl access (requires root)"
    echo "  sudo $0 fix-all      # Apply all fixes (requires root)"
    echo "  $0 security          # Check for sensitive data"
}

# Main script logic
case "${1:-help}" in
    "deps"|"dependencies")
        install_dependencies
        ;;
    "kubectl")
        fix_kubectl
        ;;
    "sudo")
        fix_sudo
        ;;
    "yaml"|"config")
        deploy_yaml
        ;;
    "fix-all"|"fixall")
        apply_all_fixes
        ;;
    "security"|"check")
        security_check
        ;;
    "help"|"--help"|"-h")
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac
