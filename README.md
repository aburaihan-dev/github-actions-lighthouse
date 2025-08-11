# GitHub Actions Monitor

A Python service that monitors GitHub Actions workflows across multiple repositories and executes shell commands when workflows complete successfully. Designed to run as a systemd service on Linux systems.

## 🚨 **IMPORTANT: Security Notice**

**Before using this repository, please read:**
- 📋 **[Quick Setup Guide](QUICK_SETUP.md)** - Get started in 5 minutes
- 🔐 **[Security Guide](SECURITY.md)** - Essential security information
- ✅ **[Pre-commit Checklist](PRE_COMMIT_CHECKLIST.md)** - Before pushing changes
- 🚀 **[Scripts Usage Guide](SCRIPTS_USAGE.md)** - How to use the management scripts

**This repository contains configuration templates that MUST be customized with your own values.**

## Features

- **Multi-Repository Monitoring**: Monitor GitHub Actions workflows across multiple repositories simultaneously
- **Parallel Processing**: Process multiple repositories concurrently for faster monitoring (configurable workers)
- **GitHub Actions Monitoring**: Poll GitHub Actions workflows at configurable intervals
- **Selective Monitoring**: Monitor specific workflows (by name or filename) and branches
- **Command Execution**: Execute shell commands when workflows complete successfully with repository and branch-specific command mapping
- **Commit Author Tracking**: Environment variables include commit author information for notifications
- **Enhanced Command Logging**: Comprehensive command execution logging with permission debugging, environment variable tracking, and detailed error analysis
- **State Persistence**: Track processed workflow runs per repository to avoid duplicates
- **Daily Log Rotation**: Automatic daily log rotation with 30-day retention and configurable timezone
- **Timezone Support**: Configurable timezone display (default: Asia/Dhaka) with IANA timezone support
- **Comprehensive Logging**: Structured logging with multiple levels and console/file output
- **Health Monitoring**: Optional health check file for service monitoring
- **Systemd Integration**: Proper systemd service with auto-restart and security features
- **Graceful Shutdown**: Handle SIGTERM/SIGINT signals properly
- **Simplified Management**: Unified scripts for deployment, testing, and troubleshooting

## Architecture

### Multi-Repository Support

The service supports monitoring multiple GitHub repositories simultaneously:

- **Centralized Monitoring**: One service instance can monitor workflows across multiple repositories
- **Per-Repository State**: Tracks workflow run state separately for each repository
- **Unified Command Execution**: Same set of commands executed regardless of which repository triggered them
- **Repository Context**: Commands receive context about which repository triggered the execution
- **Independent Filtering**: Same workflow and branch filters apply to all repositories

### Workflow Detection

The service can identify workflows by:
- **Workflow Name**: e.g., "CI/CD Pipeline", "Deploy to Staging"
- **Workflow Filename**: e.g., "docker-build-push.yml", "deploy.yml"
- **Workflow ID**: Numeric workflow identifier

### Parallel Processing

The service supports concurrent repository monitoring for improved performance:
- **Configurable Workers**: Set maximum parallel workers (default: 3)
- **Per-Repository Timeouts**: Independent timeout handling for each repository
- **Thread-Safe Operations**: Safe concurrent state management
- **Performance Improvements**: 50-85% faster monitoring with multiple repositories

```yaml
monitoring:
  enable_parallel: true
  max_parallel_workers: 3
  timeout_per_repo: 60
```

### Environment Variables

Commands receive comprehensive context information:
- `REPO_NAME`: Repository name (e.g., "owner/repo")
- `WORKFLOW_NAME`: Triggered workflow name
- `BRANCH_NAME`: Branch that triggered the workflow
- `RUN_NUMBER`: Workflow run number
- `COMMIT_SHA`: Commit SHA that triggered the workflow
- `COMMIT_MESSAGE`: Commit message
- `COMMIT_AUTHOR`: GitHub username or name of commit author

## Quick Start

**🚀 For immediate setup, see [QUICK_SETUP.md](QUICK_SETUP.md) - Get running in 5 minutes!**

**🎮 For daily operations, see [SCRIPTS_USAGE.md](SCRIPTS_USAGE.md) - Simplified management scripts**

### Prerequisites

- Linux system with systemd
- Python 3.8+
- GitHub Personal Access Token
- Access to the repositories you want to monitor

### Installation Steps

**🎯 Simplified Installation Process:**

1. **Initial Setup**:
   ```bash
   # Clone repository and enter directory
   git clone <repository-url>
   cd larms-github-k8s-staging-deployment
   
   # Copy configuration templates
   cp config.example.yaml config.yaml
   cp .env.example .env
   ```

2. **Configure Your Settings**:
   ```bash
   # Edit configuration with your repositories and settings
   nano config.yaml
   
   # Set your GitHub token
   nano .env  # Replace placeholder with your actual token
   ```

3. **Install and Deploy**:
   ```bash
   # One-time installation (creates service, user, virtual environment)
   sudo ./install.sh
   
   # Deploy your configuration
   sudo ./manage.sh deploy
   ```

4. **Verify Installation**:
   ```bash
   # Check service status
   sudo ./manage.sh status
   
   # View logs
   sudo ./manage.sh logs
   
   # Run environment test
   sudo ./manage.sh test
   ```

**📚 For detailed setup instructions, see [QUICK_SETUP.md](QUICK_SETUP.md)**

## Configuration

### GitHub Token Setup

You need a GitHub Personal Access Token with the following permissions:
- `repo` (for private repositories) or `public_repo` (for public repositories only)
- `actions:read` (to read workflow runs)

Create a token at: https://github.com/settings/tokens

Set the token using one of these methods (in order of precedence):

**Option 1: .env file (recommended for development)**
```bash
# Copy the example file
cp .env.example .env

# Edit the .env file
nano .env
```
Add to `.env`:
```bash
GITHUB_TOKEN=your_github_personal_access_token_here
```

**Option 2: Environment file (recommended for production)**
```bash
sudo nano /etc/github-actions-monitor/environment
```
Add:
```bash
GITHUB_TOKEN=your_github_personal_access_token_here
```

**Option 3: Environment variable**
```bash
export GITHUB_TOKEN="your_github_personal_access_token_here"
```

**Option 4: Direct in config.yaml (not recommended)**
```bash
sudo nano /etc/github-actions-monitor/config.yaml
```
Update the token field:
```yaml
github:
  token: "your_github_personal_access_token_here"
```

### Main Configuration

Edit `/etc/github-actions-monitor/config.yaml`:

```yaml
# GitHub Repository Configuration
github:
  token: "${GITHUB_TOKEN}"  # Or set directly

# Multiple repositories to monitor
repositories:
  - "owner/repository-name-1"
  - "owner/repository-name-2"
  - "organization/project-repo"

# Monitoring Configuration
monitoring:
  poll_interval: 60  # Check every 60 seconds
  workflows:
    - "docker-build-push.yml"  # Monitor specific workflow files
    - "CI/CD Pipeline"          # Or by workflow name
  branches:
    - "main"                    # Monitor specific branches
    - "staging"

# Commands to execute on success
commands:
  on_success:
    - description: "Deploy application"
      command: "kubectl apply -f deployment.yaml"
      working_directory: "/path/to/k8s/manifests"
    
    - description: "Restart service"
      command: "sudo systemctl restart my-app"
```

### Example Configurations

**Monitor multiple repositories with specific workflows**:
```yaml
repositories:
  - "company/frontend-app"
  - "company/backend-api"
  - "company/mobile-app"

monitoring:
  workflows:
    - "docker-build-push.yml"
    - "deploy-to-staging.yml"
    - "CI/CD Pipeline"
```

**Monitor specific branches across all repositories**:
```yaml
monitoring:
  branches:
    - "main"
    - "staging" 
    - "release/*"
```

**Execute different commands based on repository context**:
```yaml
commands:
  on_success:
    - description: "Pull latest code"
      command: "git pull origin main"
      working_directory: "/opt/myapp"
    
    - description: "Update Kubernetes deployment"
      command: "kubectl set image deployment/myapp myapp=myapp:latest"
    
    - description: "Send Slack notification with repo info"
      command: "curl -X POST 'https://hooks.slack.com/webhook' -d '{\"text\":\"Deployment completed for repository: $REPO_NAME\"}'"
    
    - description: "Clear cache"
      command: "redis-cli FLUSHALL"
```

**Real-world example for staging deployment**:
```yaml
repositories:
  - "DDCl-BD/larms-fronted"
  - "DDCl-BD/Infyom_L10"

monitoring:
  poll_interval: 30  # Faster polling for staging
  workflows:
    - "docker-build-push.yml"
  branches:
    - "bcc-staging"

commands:
  on_success:
    - description: "Deploy to staging environment"
      command: "kubectl apply -f /opt/k8s-manifests/staging/"
      working_directory: "/opt/deployments"
    
    - description: "Wait for rollout completion"
      command: "kubectl rollout status deployment/app --timeout=300s"
    
    - description: "Run health check"
      command: "curl -f http://staging.example.com/health"
    
    - description: "Notify team"
      command: "curl -X POST 'https://hooks.slack.com/webhook' -d '{\"text\":\"✅ Staging deployment completed\"}'"
```

## Testing

The project includes a comprehensive test suite to validate configuration, connections, and system functionality.

### Test Structure

```
src/tests/
├── __init__.py          # Test package initialization
├── test_utils.py        # Common utilities and helpers
├── test_connections.py  # Configuration and GitHub API tests
├── test_system.py       # Logging, timing, and system tests
└── test_all.py          # Main test runner
```

### Running Tests

**Quick validation** (basic setup check):
```bash
python3 run_tests.py quick
```

**Complete test suite** (comprehensive testing):
```bash
python3 run_tests.py all
```

**System overview** (configuration summary):
```bash
python3 run_tests.py overview
```

**Individual test modules**:
```bash
python3 -m src.tests.test_connections  # Configuration and connection tests
python3 -m src.tests.test_system       # System and logging tests
```

### Test Categories

1. **Configuration Tests**:
   - YAML configuration loading
   - Repository setup validation
   - Command configuration verification

2. **Connection Tests**:
   - GitHub API authentication
   - Repository access validation
   - Workflow discovery

3. **System Tests**:
   - Log rotation configuration
   - Timezone handling
   - 5-minute timing window
   - Duplicate prevention logic

### Test Requirements

- GitHub Personal Access Token (set in `.env` file)
- Access to configured repositories
- Python dependencies: `PyGithub`, `PyYAML`, `python-dotenv`

## Service Management

### 🎮 **Simplified Management Scripts**

The service includes unified management scripts for easy operation:

```bash
# Deploy updates
sudo ./manage.sh deploy

# Service control
sudo ./manage.sh start
sudo ./manage.sh stop  
sudo ./manage.sh restart
sudo ./manage.sh status

# Monitoring and debugging
sudo ./manage.sh logs           # Recent logs
sudo ./manage.sh logs follow    # Real-time logs
sudo ./manage.sh troubleshoot   # Run diagnostics
sudo ./manage.sh test           # Test environment

# Utilities and fixes
sudo ./utils.sh fix-all         # Apply common fixes
sudo ./utils.sh kubectl         # Fix kubectl access
sudo ./utils.sh deps            # Install dependencies
./utils.sh security            # Security check
```

**📚 For complete script documentation, see [SCRIPTS_USAGE.md](SCRIPTS_USAGE.md)**

### 🔧 **Direct systemctl Commands**

```bash
# Start service
sudo systemctl start github-actions-monitor

# Stop service
sudo systemctl stop github-actions-monitor

# Restart service
sudo systemctl restart github-actions-monitor

# Enable auto-start on boot
sudo systemctl enable github-actions-monitor

# Disable auto-start
sudo systemctl disable github-actions-monitor

# Check status
sudo systemctl status github-actions-monitor

# View logs
sudo journalctl -u github-actions-monitor -f
```

## Monitoring and Debugging

### Logs

- **Service logs**: `sudo journalctl -u github-actions-monitor`
- **Application logs**: `/var/log/github-actions-monitor/monitor.log`
- **Real-time monitoring**: `sudo journalctl -u github-actions-monitor -f`

#### Log Rotation
- **Daily rotation**: Log files rotate automatically at midnight UTC
- **Retention**: Keeps 30 days of log history
- **Format**: Rotated files are named `monitor.log.YYYY-MM-DD`
- **Automatic cleanup**: Logs older than 30 days are automatically deleted

Example log files:
```
/var/log/github-actions-monitor/
├── monitor.log              # Current log file
├── monitor.log.2025-07-22   # Yesterday's log
├── monitor.log.2025-07-21   # 2 days ago
└── monitor.log.2025-06-23   # 30 days ago (oldest kept)
```

### Log Levels

Set in config.yaml:
```yaml
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  timezone: "Asia/Dhaka"  # IANA timezone for timestamp display
```

#### Timezone Configuration
- **Default**: Asia/Dhaka
- **Supported**: Any IANA timezone (UTC, America/New_York, Europe/London, Asia/Tokyo, etc.)
- **Display**: All timestamps in logs are shown in the configured timezone
- **Internal**: Calculations still use UTC for accuracy
- **Fallback**: Automatically uses UTC if invalid timezone specified

Example timestamp formats:
```
2025-07-23 14:43:56 Asia/Dhaka - Starting monitoring check
2025-07-23 08:43:56 UTC - Starting monitoring check
2025-07-23 04:43:56 America/New_York - Starting monitoring check
```

Or override temporarily:
```bash
/opt/github-actions-monitor/venv/bin/python \
  /opt/github-actions-monitor/github_actions_monitor.py \
  --config /etc/github-actions-monitor/config.yaml \
  --log-level DEBUG
```

### Health Check

Enable health monitoring:
```yaml
health:
  enabled: true
  file: "/var/run/github-actions-monitor/health"
  update_interval: 300
```

Check health:
```bash
cat /var/run/github-actions-monitor/health
```

### State File

The service tracks processed workflows per repository in:
```
/var/lib/github-actions-monitor/state.json
```

State file format:
```json
{
  "last_checked_runs": {
    "owner/repo1:workflow_id": 12345678,
    "owner/repo2:workflow_id": 87654321
  }
}
```

To reset state (reprocess all workflows):
```bash
sudo systemctl stop github-actions-monitor
sudo rm /var/lib/github-actions-monitor/state.json
sudo systemctl start github-actions-monitor
```

## Security

The service runs with minimal privileges:
- Dedicated `github-monitor` user/group
- No shell access for service user
- Protected directories with appropriate permissions
- systemd security features enabled

## File Locations

- **Application**: `/opt/github-actions-monitor/`
- **Configuration**: `/opt/github-actions-monitor/config/config.yaml`
- **Environment**: `/opt/github-actions-monitor/.env`
- **Virtual Environment**: `/opt/github-actions-monitor/venv/`
- **Logs**: `/opt/github-actions-monitor/logs/monitor.log`
- **State**: `/opt/github-actions-monitor/data/state.json`
- **Health**: `/opt/github-actions-monitor/data/health`
- **Service**: `/etc/systemd/system/github-actions-monitor.service`
- **Backups**: `/opt/github-actions-monitor/backup/`

## Troubleshooting

### 🎮 **Quick Troubleshooting with Management Scripts**

```bash
# Run comprehensive diagnostics
sudo ./manage.sh troubleshoot

# Apply common fixes
sudo ./utils.sh fix-all

# Test environment and dependencies
sudo ./manage.sh test

# View real-time logs
sudo ./manage.sh logs follow
```

### Command Execution Debugging

For detailed information about debugging command execution issues, including permission problems, see the [Enhanced Command Logging Documentation](docs/COMMAND_LOGGING.md).

The service now provides comprehensive logging for command execution that includes:
- Permission and user context information
- Directory access checks
- Environment variable logging (including commit author information)
- Detailed error analysis with context
- Execution timing and output capture

### Common Issues

1. **Authentication Error**:
   - Check GitHub token is set correctly
   - Verify token has required permissions
   - Check repository name format (owner/repo)

2. **Permission Denied**:
   - Ensure service user has required permissions
   - Check directory ownership and permissions
   - Review enhanced command logs for detailed permission analysis

3. **Command Execution Fails**:
   - Check command syntax in config.yaml
   - Verify working_directory exists and is accessible
   - Check command timeouts (default: 5 minutes)
   - Enable DEBUG logging for detailed command execution analysis

4. **No Workflows Detected**:
   - Verify repository has GitHub Actions workflows
   - Check workflow name filters in config
   - Ensure monitored branches have workflow runs

### Testing Configuration

Use the management scripts for easy testing:
```bash
# Quick environment test
sudo ./manage.sh test

# Run comprehensive diagnostics
sudo ./manage.sh troubleshoot

# Test specific components with legacy test suite
python3 run_tests.py quick     # Quick validation
python3 run_tests.py all       # Full test suite
```

### Manual Testing

Run the service manually for debugging:
```bash
# Stop the systemd service first
sudo systemctl stop github-actions-monitor

# Run manually with debug logging
sudo -u github-monitor /opt/github-actions-monitor/venv/bin/python \
  /opt/github-actions-monitor/github_actions_monitor.py \
  --config /opt/github-actions-monitor/config/config.yaml \
  --log-level DEBUG
```

### Checking GitHub API

Test GitHub connection for multiple repositories:
```bash
# Test access to specific repository
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/repos/owner/repo/actions/workflows

# Replace these examples with your actual repositories
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/repos/your-org/your-frontend-repo/actions/workflows
```

## Management Scripts

The GitHub Actions Monitor includes simplified management scripts for easy operation:

### 📋 **Available Scripts**

| Script | Purpose | Key Commands |
|--------|---------|--------------|
| **`install.sh`** | Initial setup | `sudo ./install.sh` |
| **`manage.sh`** | Daily operations | `deploy`, `test`, `logs`, `troubleshoot` |
| **`utils.sh`** | Utilities & fixes | `fix-all`, `kubectl`, `security` |

### 🎯 **Common Workflows**

```bash
# Initial setup
sudo ./install.sh

# Deploy updates
sudo ./manage.sh deploy

# Monitor service  
sudo ./manage.sh logs follow

# Fix issues
sudo ./utils.sh fix-all

# Security check
./utils.sh security
```

**📚 Complete documentation: [SCRIPTS_USAGE.md](SCRIPTS_USAGE.md)**

## Requirements

- Linux system with systemd
- Python 3.8+
- Internet access to GitHub API
- GitHub Personal Access Token

## Dependencies

The installation script automatically creates a virtual environment and installs:

- PyGithub==1.59.1 (GitHub API interactions)
- PyYAML==6.0.1 (Configuration file parsing)
- python-dotenv (Environment variable management)

**Dependencies are automatically managed** - no manual installation required when using `./install.sh`.

For manual dependency installation: `./utils.sh deps`

## License

This project is provided as-is. Modify and use according to your needs.
