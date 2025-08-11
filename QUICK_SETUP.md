# 🚀 Quick Setup Guide

## Getting Started with GitHub Actions Monitor

### 📋 **Prerequisites**

- Ubuntu/Debian Linux server
- Python 3.8+ installed
- `sudo` access for installation
- GitHub personal access token
- WhatsApp API server (optional)

### ⚡ **Quick Setup (5 minutes)**

#### 1. **Clone and Enter Directory**
```bash
git clone <your-repository-url>
cd github-actions-lighthouse
```

#### 2. **Create Your Configuration**
```bash
# Copy example files
cp .env.example .env
cp config.example.yaml config.yaml
```

#### 3. **Configure Your Settings**

**Edit `.env`:**
```bash
nano .env
# Replace: your_github_personal_access_token_here
# With: your actual GitHub token
```

**Edit `config.yaml`:**
```bash
nano config.yaml
# Replace these placeholders:
# - YOUR_WHATSAPP_GROUP_ID@g.us → your WhatsApp group ID  
# - YOUR_WHATSAPP_API_SERVER → your API server IP/domain
# - your-org/your-frontend-repo → your repository names
# - your-branch → your branch names
# - your-workflow.yml → your workflow file names
```

#### 4. **Install and Run**
```bash
# Install the service
sudo ./install.sh

# Check status
sudo systemctl status github-actions-monitor

# View logs
sudo journalctl -u github-actions-monitor -f
```

### 🔧 **Advanced Configuration**

#### **Repository-Specific Commands**
Update the `execution_map` section in `config.yaml`:

```yaml
execution_map:
  "your-org/frontend-repo":
    "main":
      - "echo_status"
      - "restart_frontend" 
      - "whatsapp_notify"
  
  "your-org/backend-repo":
    "production":
      - "echo_status"
      - "restart_backend"
      - "whatsapp_notify"
```

#### **Custom Commands**
Add your own commands in the `definitions` section:

```yaml
definitions:
  your_custom_command:
    description: "Your custom deployment step"
    command: "your-deployment-script.sh"
    working_directory: "/path/to/your/scripts"
    timeout: 300
```

### 🔍 **Monitoring and Troubleshooting**

#### **Check Service Status**
```bash
sudo systemctl status github-actions-monitor
```

#### **View Logs**
```bash
# Real-time logs
sudo journalctl -u github-actions-monitor -f

# Recent logs
sudo journalctl -u github-actions-monitor --since "1 hour ago"
```

#### **Test Configuration**
```bash
# Quick test
sudo -u github-monitor /opt/github-actions-monitor/venv/bin/python \
  /opt/github-actions-monitor/run_tests.py quick

# Full test
sudo -u github-monitor /opt/github-actions-monitor/venv/bin/python \
  /opt/github-actions-monitor/run_tests.py all
```

### 🛠️ **Common Issues**

#### **GitHub API Rate Limits**
- Increase `poll_interval` in config (default: 60 seconds)
- Check your token has correct permissions

#### **kubectl Access Issues**
- Verify kubeconfig path in commands
- Ensure service user has access to kubectl
- Check namespace and deployment names

#### **WhatsApp Notifications Not Working**
- Verify API server is accessible
- Check group ID format  
- Test API connectivity manually

### 📚 **Additional Documentation**

- **Security Guide:** `SECURITY.md`
- **Pre-commit Checklist:** `PRE_COMMIT_CHECKLIST.md`
- **Scripts Usage:** `SCRIPTS_USAGE.md`
- **Installation Changes:** `docs/INSTALL_CHANGES.md`
- **Parallel Processing:** `docs/PARALLEL_PROCESSING_UPDATE.md`

### 💡 **Tips**

1. **Start with minimal configuration** - Enable only basic commands first
2. **Test thoroughly** - Use the test commands before production deployment  
3. **Monitor logs** - Watch for any errors or issues
4. **Gradual rollout** - Add repositories one at a time
5. **Keep backups** - The installer creates automatic backups

### 🆘 **Getting Help**

If you encounter issues:
1. Check the logs: `sudo journalctl -u github-actions-monitor`
2. Run the test suite: `sudo ./run_tests.py quick`
3. Review the main documentation and scripts usage guide
4. Check technical documentation in `docs/` for specific issues
5. Verify your configuration against the examples
