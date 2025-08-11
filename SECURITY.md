# 🔐 SECURITY NOTICE

## ⚠️ Before Using This Repository

This repository contains configuration templates that **MUST** be customized with your own values before use.

### 🛡️ Required Security Steps

#### 1. **Environment Variables** 
- Copy `.env.example` to `.env`
- Replace `your_github_personal_access_token_here` with your actual GitHub token
- **NEVER** commit the real `.env` file

#### 2. **Configuration File**
- Copy `config.example.yaml` to `config.yaml` 
- Replace all placeholder values:
  - `YOUR_WHATSAPP_GROUP_ID@g.us` → Your actual WhatsApp group ID
  - `YOUR_WHATSAPP_API_SERVER` → Your WhatsApp API server IP/domain
  - `your-org/your-frontend-repo` → Your actual repository names
  - `your-branch` → Your actual branch names
  - `your-workflow.yml` → Your actual workflow file names

#### 3. **Service Configuration**
- Update namespace names (`your-namespace` → your actual namespace)
- Update deployment names (`your-frontend`, `your-backend` → your actual deployments)
- Update kubectl configuration paths if needed

### 🚨 Sensitive Information

The following information should **NEVER** be committed to version control:
- GitHub personal access tokens
- WhatsApp group IDs
- WhatsApp API server IPs
- Internal server IPs or hostnames
- Any production credentials

### ✅ Safe to Commit

These files are safe to commit:
- `config.example.yaml` (with placeholders)
- `.env.example` (with placeholders)
- All Python scripts
- Documentation files
- Installation scripts

### 🔒 .gitignore Protection

The included `.gitignore` file prevents accidental commits of:
- `.env` files
- Log files
- State files
- Cache directories
- Backup files

**Always verify your changes before committing!**
