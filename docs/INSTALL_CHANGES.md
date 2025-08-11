# Install Script Changes - Single Directory Setup

## Overview
The install script has been updated to use a single directory structure instead of spreading files across multiple system directories. This simplifies installation, maintenance, and removal.

## Key Changes

### 🧹 Previous Installation Cleanup
- **New function**: `remove_previous_installation()` 
- Automatically stops and disables existing service
- Removes all legacy directories:
  - `/etc/github-actions-monitor`
  - `/var/log/github-actions-monitor` 
  - `/var/lib/github-actions-monitor`
  - `/var/run/github-actions-monitor`
- Cleans up systemd service files and logrotate configuration
- Removes existing installation directory completely

### 📁 Single Directory Structure
All files are now contained within `/opt/github-actions-monitor/`:

```
/opt/github-actions-monitor/
├── config/                   # Configuration files
│   ├── config.yaml          # Main configuration
│   └── environment          # Environment variables
├── logs/                     # Log files (was /var/log/github-actions-monitor)
├── data/                     # Application data and state (was /var/lib/github-actions-monitor)
├── run/                      # Runtime files (was /var/run/github-actions-monitor)
├── venv/                     # Python virtual environment
├── src/tests/                # Test suite
├── .env.example             # Environment template
├── github_actions_monitor.py # Main application
├── requirements.txt         # Python dependencies
└── run_tests.py            # Test runner
```

### 🔧 Updated System Integration

#### Systemd Service
- **Updated paths**: All paths now point to subdirectories within `/opt/github-actions-monitor/`
- **Enhanced security**: `ReadWritePaths` limited to `logs/`, `data/`, and `run/` subdirectories
- **Environment loading**: Supports both `config/environment` and `.env` files
- **PYTHONPATH**: Added to ensure proper module loading

#### Log Rotation
- **Updated path**: Now monitors `/opt/github-actions-monitor/logs/*.log`
- **Consistent ownership**: Uses the service user for all operations

### 🚀 Installation Benefits

#### Simplified Management
- **Single location**: Everything in one directory
- **Easy backup**: Just backup `/opt/github-actions-monitor/`
- **Clean removal**: Remove one directory to uninstall completely
- **Portable**: Self-contained installation

#### Improved Security
- **Contained permissions**: All files owned by service user
- **Restricted access**: Only necessary directories are writable
- **Environment isolation**: Virtual environment contained within installation

#### Better Maintenance
- **Clear structure**: Organized subdirectories for different purposes
- **Version control friendly**: Easier to track changes
- **Testing integration**: Test suite included in installation

### 🛠️ Usage Changes

#### Configuration
**Before**: `/etc/github-actions-monitor/config.yaml`
**After**: `/opt/github-actions-monitor/config/config.yaml`

#### Logs
**Before**: `/var/log/github-actions-monitor/monitor.log`
**After**: `/opt/github-actions-monitor/logs/monitor.log`

#### Environment
**Before**: `/etc/github-actions-monitor/environment`
**After**: `/opt/github-actions-monitor/config/environment` or `/opt/github-actions-monitor/.env`

#### Testing
**Before**: `cd /opt/github-actions-monitor && sudo -u github-monitor python3 run_tests.py`
**After**: `cd /opt/github-actions-monitor && sudo -u github-monitor ./venv/bin/python run_tests.py`

### 🔄 Upgrade Process
1. **Automatic cleanup**: Previous installations are automatically detected and removed
2. **Fresh installation**: Clean installation in the new structure
3. **Configuration migration**: Manual step to migrate configuration if needed
4. **Service registration**: Updated systemd service with new paths

### ✅ Validation Features
- **Dependency check**: Validates Python packages are properly installed
- **Configuration validation**: Checks YAML syntax and command structure
- **Test suite integration**: Built-in testing capabilities
- **Service verification**: Confirms systemd service is properly configured

## Migration Notes

### For Existing Installations
1. **Backup important data**: Configuration and any custom modifications
2. **Run new installer**: It will automatically clean up and reinstall
3. **Restore configuration**: Copy your settings to the new location
4. **Verify functionality**: Run tests to ensure everything works

### For New Installations
- Simply run the installer - no additional steps needed
- Everything is contained and organized in a single directory
- Follow the post-installation instructions for configuration

## Benefits Summary
✅ **Cleaner**: Single directory structure  
✅ **Safer**: Automatic cleanup of old installations  
✅ **Simpler**: Easier to manage and maintain  
✅ **Portable**: Self-contained installation  
✅ **Secure**: Improved permission model  
✅ **Testable**: Integrated validation and testing  
