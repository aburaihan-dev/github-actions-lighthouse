#!/bin/bash
# GitHub Actions Monitor - Unified Management Script
# Combines deployment, testing, troubleshooting, and maintenance functions

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default paths
INSTALL_DIR="/opt/github-actions-monitor"
VENV_PATH="$INSTALL_DIR/venv"
SERVICE_NAME="github-actions-monitor"

# Print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This command must be run as root (use sudo)"
        exit 1
    fi
}

# Deploy updates function
deploy_updates() {
    echo "=== GitHub Actions Monitor - Deploy Updates ==="
    echo ""
    
    check_root
    
    # Validate YAML syntax
    print_info "Validating YAML syntax..."
    if python3 -c "import yaml; yaml.safe_load(open('config.yaml')); print('YAML syntax is valid')" 2>/dev/null; then
        print_status "YAML syntax validation passed"
    else
        print_error "YAML syntax validation failed"
        exit 1
    fi
    
    # Validate Python syntax
    print_info "Validating Python syntax..."
    if python3 -m py_compile github_actions_monitor.py 2>/dev/null; then
        print_status "Python syntax validation passed"
    else
        print_warning "Python syntax validation detected issues (continuing anyway)"
    fi
    
    # Backup current files
    print_info "Backing up current files..."
    BACKUP_DIR="$INSTALL_DIR/backup/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    if [[ -f "$INSTALL_DIR/config/config.yaml" ]]; then
        cp "$INSTALL_DIR/config/config.yaml" "$BACKUP_DIR/"
        print_status "Configuration backed up"
    fi
    
    if [[ -f "$INSTALL_DIR/github_actions_monitor.py" ]]; then
        cp "$INSTALL_DIR/github_actions_monitor.py" "$BACKUP_DIR/"
        print_status "Python script backed up"
    fi
    
    # Deploy new files
    print_info "Deploying updated files..."
    cp config.yaml "$INSTALL_DIR/config/"
    cp github_actions_monitor.py "$INSTALL_DIR/"
    if [[ -f "requirements.txt" ]]; then
        cp requirements.txt "$INSTALL_DIR/"
        print_status "Requirements file deployed"
    fi
    print_status "New files deployed"
    
    # Update dependencies
    print_info "Updating Python dependencies..."
    if [[ -f "requirements.txt" ]]; then
        sudo -u github-monitor "$VENV_PATH/bin/pip" install --upgrade -r requirements.txt
        print_status "Dependencies updated"
    fi
    
    # Test imports
    print_info "Testing Python imports..."
    cd "$INSTALL_DIR"
    if sudo -u github-monitor "$VENV_PATH/bin/python" -c "import github_actions_monitor; print('Import successful')" 2>/dev/null; then
        print_status "Python import test passed"
    else
        print_error "Python import test failed"
        exit 1
    fi
    
    # Restart service
    print_info "Restarting service..."
    systemctl restart "$SERVICE_NAME"
    sleep 3
    
    # Check service status
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_status "Service is running"
    else
        print_error "Service failed to start"
        systemctl status "$SERVICE_NAME" --no-pager -l
        exit 1
    fi
    
    print_status "Deployment complete!"
}

# Test environment function
test_environment() {
    echo "=== Environment Test ==="
    echo ""
    
    # Check installation
    if [[ -d "$INSTALL_DIR" ]]; then
        print_status "Installation directory exists"
    else
        print_error "Installation directory not found. Run: sudo ./install.sh"
        exit 1
    fi
    
    # Check virtual environment
    if [[ -d "$VENV_PATH" ]]; then
        print_status "Virtual environment exists"
        
        if [[ $EUID -eq 0 ]]; then
            if sudo -u github-monitor "$VENV_PATH/bin/python" --version &>/dev/null; then
                PYTHON_VERSION=$(sudo -u github-monitor "$VENV_PATH/bin/python" --version)
                print_status "Virtual environment functional: $PYTHON_VERSION"
            else
                print_error "Virtual environment broken"
                exit 1
            fi
        fi
    else
        print_error "Virtual environment not found"
        exit 1
    fi
    
    # Check service
    if [[ $EUID -eq 0 ]]; then
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            print_status "Service is running"
        else
            print_warning "Service is not running"
        fi
    fi
    
    # Test dependencies
    if [[ $EUID -eq 0 ]]; then
        print_info "Testing dependencies..."
        
        if sudo -u github-monitor "$VENV_PATH/bin/python" -c "import github; print('PyGithub OK')" 2>/dev/null; then
            print_status "PyGithub available"
        else
            print_warning "PyGithub not available"
        fi
        
        if sudo -u github-monitor "$VENV_PATH/bin/python" -c "import yaml; print('PyYAML OK')" 2>/dev/null; then
            print_status "PyYAML available"
        else
            print_warning "PyYAML not available"
        fi
        
        if sudo -u github-monitor "$VENV_PATH/bin/python" -c "import concurrent.futures; print('concurrent.futures OK')" 2>/dev/null; then
            print_status "Parallel processing ready"
        else
            print_error "Parallel processing not available"
        fi
    fi
    
    print_status "Environment test complete"
}

# Troubleshoot function
troubleshoot() {
    echo "=== GitHub Actions Monitor Troubleshoot ==="
    echo ""
    
    print_info "System Information:"
    echo "Date: $(date)"
    echo "User: $(whoami)"
    echo "OS: $(lsb_release -d 2>/dev/null | cut -f2 || echo "Unknown")"
    echo ""
    
    # Check service status
    print_info "Service Status:"
    if [[ $EUID -eq 0 ]]; then
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            print_status "Service is running"
            systemctl status "$SERVICE_NAME" --no-pager -l | head -10
        else
            print_warning "Service is not running"
            systemctl status "$SERVICE_NAME" --no-pager -l
        fi
        echo ""
        
        print_info "Recent logs (last 20 lines):"
        journalctl -u "$SERVICE_NAME" --no-pager -n 20
    else
        print_warning "Need root access to check service status"
    fi
    
    echo ""
    print_info "Configuration files:"
    
    if [[ -f "$INSTALL_DIR/config/config.yaml" ]]; then
        print_status "Config file exists"
        echo "Repositories configured: $(grep -A 10 'repositories:' "$INSTALL_DIR/config/config.yaml" | grep -E '^\s*-' | wc -l || echo "0")"
    else
        print_error "Config file missing"
    fi
    
    if [[ -f "$INSTALL_DIR/.env" ]]; then
        print_status ".env file exists"
        if grep -q "your_github_personal_access_token_here" "$INSTALL_DIR/.env" 2>/dev/null; then
            print_warning ".env file contains placeholder token"
        else
            print_status ".env file appears configured"
        fi
    else
        print_warning ".env file missing"
    fi
    
    # Check kubectl access
    print_info "kubectl access test:"
    if command -v kubectl &>/dev/null; then
        if sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf version --client &>/dev/null; then
            print_status "kubectl access working"
        else
            print_warning "kubectl access issues detected"
        fi
    else
        print_warning "kubectl not installed"
    fi
}

# Fix common issues function
fix_issues() {
    echo "=== Fix Common Issues ==="
    echo ""
    
    check_root
    
    print_info "Applying common fixes..."
    
    # Fix kubeconfig access
    print_info "Fixing kubectl access..."
    if [[ -f "/etc/kubernetes/admin.conf" ]]; then
        chmod 644 /etc/kubernetes/admin.conf
        print_status "kubectl permissions fixed"
    else
        print_warning "Kubernetes admin.conf not found"
    fi
    
    # Fix service permissions
    print_info "Fixing service permissions..."
    if id github-monitor &>/dev/null; then
        chown -R github-monitor:github-monitor "$INSTALL_DIR" 2>/dev/null || true
        print_status "Service permissions fixed"
    else
        print_error "github-monitor user not found"
    fi
    
    # Restart service
    print_info "Restarting service..."
    systemctl restart "$SERVICE_NAME"
    sleep 3
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_status "Service restarted successfully"
    else
        print_error "Service restart failed"
        systemctl status "$SERVICE_NAME" --no-pager -l
    fi
    
    print_status "Common fixes applied"
}

# Show logs function
show_logs() {
    echo "=== GitHub Actions Monitor Logs ==="
    echo ""
    
    if [[ $EUID -eq 0 ]]; then
        if [[ "$1" == "follow" ]] || [[ "$1" == "-f" ]]; then
            print_info "Following logs (Ctrl+C to stop)..."
            journalctl -u "$SERVICE_NAME" -f
        else
            print_info "Recent logs (last 50 lines):"
            journalctl -u "$SERVICE_NAME" --no-pager -n 50
        fi
    else
        print_error "Need root access to view service logs"
        print_info "Try: sudo $0 logs"
    fi
}

# Service control functions
start_service() {
    check_root
    print_info "Starting service..."
    systemctl start "$SERVICE_NAME"
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_status "Service started"
    else
        print_error "Failed to start service"
    fi
}

stop_service() {
    check_root
    print_info "Stopping service..."
    systemctl stop "$SERVICE_NAME"
    print_status "Service stopped"
}

restart_service() {
    check_root
    print_info "Restarting service..."
    systemctl restart "$SERVICE_NAME"
    sleep 2
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_status "Service restarted"
    else
        print_error "Failed to restart service"
    fi
}

# Service status
service_status() {
    if [[ $EUID -eq 0 ]]; then
        systemctl status "$SERVICE_NAME" --no-pager -l
    else
        print_warning "Need root access for detailed status"
        systemctl status "$SERVICE_NAME" --no-pager -l 2>/dev/null || print_error "Cannot access service status"
    fi
}

# Show usage
show_usage() {
    echo "GitHub Actions Monitor Management Script"
    echo ""
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  deploy         Deploy updates to the service"
    echo "  test           Test environment and dependencies"
    echo "  troubleshoot   Run troubleshooting diagnostics"
    echo "  fix            Apply common fixes"
    echo "  logs [follow]  Show service logs (use 'follow' for real-time)"
    echo "  start          Start the service"
    echo "  stop           Stop the service"
    echo "  restart        Restart the service"
    echo "  status         Show service status"
    echo "  help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  sudo $0 deploy           # Deploy updates"
    echo "  sudo $0 test             # Test environment"
    echo "  sudo $0 troubleshoot     # Run diagnostics"
    echo "  sudo $0 logs follow      # Follow logs in real-time"
    echo "  sudo $0 restart          # Restart service"
}

# Main script logic
case "${1:-help}" in
    "deploy")
        deploy_updates
        ;;
    "test")
        test_environment
        ;;
    "troubleshoot"|"diagnose")
        troubleshoot
        ;;
    "fix")
        fix_issues
        ;;
    "logs")
        show_logs "$2"
        ;;
    "start")
        start_service
        ;;
    "stop")
        stop_service
        ;;
    "restart")
        restart_service
        ;;
    "status")
        service_status
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
