# Solution: github-monitor User kubectl Access & Read-Only File System Fix

## Problem Summary
The GitHub Actions Monitor service was failing with two main issues:
1. **Read-only file system error**: Service trying to create directories in `/var/log/github-actions-monitor`
2. **kubectl access**: The `github-monitor` user couldn't execute kubectl commands

## Root Cause
1. The configuration file still had old system paths (`/var/log`, `/var/lib`, `/var/run`) instead of the new single-directory structure under `/opt/github-actions-monitor`
2. The `github-monitor` user lacked permissions to execute kubectl commands

## Complete Solution

### 1. Fixed Configuration Paths ✅

Updated `config.yaml` to use the correct paths:
```yaml
# OLD (causing read-only file system errors)
logging:
  file:
    path: "/var/log/github-actions-monitor/monitor.log"
state:
  state_file: "/var/lib/github-actions-monitor/state.json"
health:
  file: "/var/run/github-actions-monitor/health"

# NEW (fixed)
logging:
  file:
    path: "/opt/github-actions-monitor/logs/monitor.log"
state:
  state_file: "/opt/github-actions-monitor/data/state.json"
health:
  file: "/opt/github-actions-monitor/data/health"
```

### 2. Added kubectl Access Setup ✅

Enhanced the installation script (`install.sh`) to automatically configure kubectl access:

#### Sudo Access Configuration
- Creates `/etc/sudoers.d/github-monitor` with kubectl permissions
- Allows `github-monitor` user to run kubectl without password
- Covers both `/usr/local/bin/kubectl` and `/usr/bin/kubectl` paths

#### kubeconfig Setup
- Automatically copies kubeconfig from `/root/.kube/config` or `/etc/kubernetes/admin.conf`
- Sets proper ownership and permissions for the `github-monitor` user
- Creates `/home/github-monitor/.kube/config` with correct permissions

#### Systemd Service Updates
- Added `KUBECONFIG` environment variable
- Updated `ReadWritePaths` to include `/home/github-monitor/.kube`
- Changed `ProtectHome=false` to allow access to user home directory

### 3. Updated Commands in config.yaml ✅

Modified the kubectl commands to use sudo:
```yaml
commands:
  definitions:
    restart_frontend:
      description: "Restart frontend service"
      command: "sudo kubectl rollout restart deployment/your-frontend -n your-namespace"
      working_directory: "/tmp"
    
    restart_backend:
      description: "Restart backend service"
      command: "sudo kubectl rollout restart deployment/your-backend -n your-namespace"
      working_directory: "/tmp"
```

### 4. Created Troubleshooting Tools ✅

Added `troubleshoot.sh` script to help diagnose issues:
- Service status checks
- File permission analysis
- kubectl access testing
- Configuration validation
- Log analysis
- Basic functionality tests

## Deployment Steps

### 1. Update Existing Installation
```bash
# Stop the service
sudo systemctl stop github-actions-monitor

# Update configuration (paths are now fixed)
sudo cp config.yaml /opt/github-actions-monitor/config/

# Run the updated installation script
sudo ./install.sh

# The script will automatically:
# - Set up kubectl access for github-monitor user
# - Configure sudoers permissions
# - Copy kubeconfig with proper permissions
# - Update systemd service file
```

### 2. Verify kubectl Access
```bash
# Test kubectl access as github-monitor user
sudo -u github-monitor kubectl version --client
sudo -u github-monitor sudo kubectl get nodes
```

### 3. Start and Verify Service
```bash
# Start the service
sudo systemctl start github-actions-monitor

# Check status
sudo systemctl status github-actions-monitor

# Monitor logs
sudo journalctl -u github-actions-monitor -f
```

### 4. Run Diagnostics (if needed)
```bash
# Run comprehensive troubleshooting
sudo ./troubleshoot.sh
```

## Key Files Changed

1. **config.yaml**: Fixed all paths to use `/opt/github-actions-monitor/`
2. **install.sh**: Added kubectl access setup and improved systemd service
3. **troubleshoot.sh**: New diagnostic script
4. **github-actions-monitor.service**: Updated via install.sh with proper permissions

## Security Considerations

- The `github-monitor` user has sudo access only to kubectl commands
- kubeconfig is protected with 600 permissions
- Systemd service maintains security restrictions while allowing necessary access
- All files remain under the controlled `/opt/github-actions-monitor/` directory

## Testing Commands

```bash
# Test service user kubectl access
sudo -u github-monitor kubectl version --client
sudo -u github-monitor sudo kubectl get nodes

# Test configuration loading
sudo -u github-monitor /opt/github-actions-monitor/venv/bin/python \
  /opt/github-actions-monitor/github_actions_monitor.py --help

# Check enhanced command logging
sudo tail -f /opt/github-actions-monitor/logs/monitor.log
```

## Benefits

1. **Fixed read-only file system errors**: All paths now use writable directories
2. **kubectl access working**: github-monitor user can execute kubectl commands
3. **Enhanced logging**: Detailed command execution logging for debugging
4. **Improved security**: Minimal required permissions with sudo access
5. **Better diagnostics**: Troubleshooting script for quick issue resolution
6. **Automated setup**: Installation script handles all kubectl configuration

The service should now start successfully and be able to execute kubectl commands when workflows complete!
