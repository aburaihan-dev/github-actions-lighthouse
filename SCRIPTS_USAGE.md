# 🚀 Scripts Usage Guide

## 📋 **Simplified Script Structure**

The GitHub Actions Monitor now uses **only 3 main scripts** instead of 12+ individual scripts:

### 🎯 **Main Scripts**

| Script | Purpose | Usage |
|--------|---------|-------|
| **`install.sh`** | 🔧 **Initial Setup** | First-time installation and setup |
| **`manage.sh`** | 🎮 **Service Management** | Deploy, test, troubleshoot, control service |
| **`utils.sh`** | 🛠️ **Utilities & Fixes** | Dependencies, fixes, security checks |

---

## 🔧 **1. install.sh - Initial Setup**

**Use once for initial installation:**

```bash
# First-time setup (creates service, user, virtual environment)
sudo ./install.sh
```

**What it does:**
- Creates `github-monitor` service user
- Sets up virtual environment
- Installs Python dependencies  
- Creates systemd service
- Configures permissions and directories

---

## 🎮 **2. manage.sh - Service Management**

**Daily operations and management:**

### **Deploy Updates**
```bash
sudo ./manage.sh deploy
```
- Validates configuration and code
- Backs up existing files
- Deploys new files
- Updates dependencies
- Restarts service

### **Test Environment**
```bash
sudo ./manage.sh test
```
- Checks installation integrity
- Tests dependencies
- Verifies service status

### **Troubleshoot Issues**
```bash
sudo ./manage.sh troubleshoot
```
- Shows system information
- Displays service status
- Shows recent logs
- Checks configuration files

### **View Logs**
```bash
sudo ./manage.sh logs          # Recent logs
sudo ./manage.sh logs follow   # Real-time logs
```

### **Service Control**
```bash
sudo ./manage.sh start         # Start service
sudo ./manage.sh stop          # Stop service  
sudo ./manage.sh restart       # Restart service
sudo ./manage.sh status        # Show status
```

### **Quick Fixes**
```bash
sudo ./manage.sh fix           # Apply common fixes
```

---

## 🛠️ **3. utils.sh - Utilities & Fixes**

**Specialized utilities and fixes:**

### **Install Dependencies**
```bash
./utils.sh deps                # Install Python dependencies
```

### **Fix Common Issues**
```bash
sudo ./utils.sh kubectl        # Fix kubectl access
sudo ./utils.sh sudo           # Fix sudo privileges
sudo ./utils.sh yaml           # Deploy YAML config
sudo ./utils.sh fix-all        # Apply all fixes
```

### **Security Check**
```bash
./utils.sh security            # Check for sensitive data
```

---

## 🎯 **Common Workflows**

### **🔄 First Time Setup**
```bash
# 1. Initial installation
sudo ./install.sh

# 2. Configure your settings
cp config.example.yaml config.yaml
cp .env.example .env
# Edit config.yaml and .env with your values

# 3. Deploy configuration
sudo ./manage.sh deploy

# 4. Check status
sudo ./manage.sh status
```

### **📦 Deploy Updates**
```bash
# 1. Update code/config files
# 2. Deploy changes
sudo ./manage.sh deploy

# 3. Check logs
sudo ./manage.sh logs
```

### **🔧 Fix Issues**
```bash
# 1. Run diagnostics
sudo ./manage.sh troubleshoot

# 2. Apply fixes
sudo ./utils.sh fix-all

# 3. Test environment
sudo ./manage.sh test
```

### **📊 Daily Monitoring**
```bash
# Check service status
sudo ./manage.sh status

# View recent activity
sudo ./manage.sh logs

# Follow logs in real-time
sudo ./manage.sh logs follow
```

---

## 🗂️ **Legacy Scripts**

Old individual scripts are preserved in `scripts-legacy/` for reference:

```
scripts-legacy/
├── apply-fixes.sh              # → use: utils.sh fix-all
├── check-environment.sh        # → use: manage.sh test  
├── deploy-parallel-updates.sh  # → use: manage.sh deploy
├── fix-kubeconfig.sh           # → use: utils.sh kubectl
├── fix-sudo-privileges.sh      # → use: utils.sh sudo
├── install-dependencies.sh     # → use: utils.sh deps
├── troubleshoot.sh             # → use: manage.sh troubleshoot
└── ... (other legacy scripts)
```

---

## 💡 **Quick Reference**

### **Most Common Commands**
```bash
# Deploy updates
sudo ./manage.sh deploy

# Check status  
sudo ./manage.sh status

# View logs
sudo ./manage.sh logs

# Fix issues
sudo ./utils.sh fix-all

# Run security check
./utils.sh security
```

### **Get Help**
```bash
./manage.sh help               # Management commands
./utils.sh help                # Utility commands
```

---

## ✅ **Benefits of New Structure**

✅ **Simplified** - 3 scripts instead of 12+  
✅ **Consistent** - Unified interface and error handling  
✅ **Comprehensive** - All functionality preserved  
✅ **User-friendly** - Clear command structure  
✅ **Maintainable** - Less duplication, easier updates  
✅ **Safe** - Better error handling and validation  

The new script structure makes the GitHub Actions Monitor much easier to use while preserving all functionality! 🎉
