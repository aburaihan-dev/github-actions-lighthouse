# 📋 Pre-Commit Checklist

## ✅ Before Committing to GitHub

**ALWAYS** run this checklist before pushing code to ensure no sensitive data is exposed:

### 🔍 **1. Sensitive Data Check**
```bash
# Check for sensitive patterns in all files
find . -name "*.yaml" -o -name "*.yml" -o -name "*.py" -o -name "*.sh" -o -name "*.md" -o -name "*.env" | \
xargs grep -l "SENSITIVE_PATTERN\|API_SERVER_IP\|GITHUB_TOKEN_PATTERN\|GROUP_ID_PATTERN" 2>/dev/null || echo "✅ No sensitive data found"
```

### 🛡️ **2. Environment File Check**
```bash
# Verify .env contains only placeholders
grep -q "your_github_personal_access_token_here" .env && echo "✅ .env is safe" || echo "❌ .env contains real token!"
```

### 📁 **3. File Structure Check**
```bash
# Verify required files exist
ls config.example.yaml >/dev/null 2>&1 && echo "✅ Example config exists" || echo "❌ Missing config.example.yaml"
ls .gitignore >/dev/null 2>&1 && echo "✅ .gitignore exists" || echo "❌ Missing .gitignore"
ls docs/SECURITY.md >/dev/null 2>&1 && echo "✅ Security notice exists" || echo "❌ Missing SECURITY.md"
```

### 🧹 **4. Cleanup Check**
```bash
# Verify no cache or log files
find . -name "__pycache__" -o -name "*.pyc" -o -name "*.log" | grep -q . && echo "❌ Cache/log files found!" || echo "✅ No cache/log files"
```

### 📦 **5. Configuration Validation**
```bash
# Verify example config has placeholders
grep -q "YOUR_WHATSAPP_GROUP_ID" config.example.yaml && echo "✅ Config has placeholders" || echo "❌ Config missing placeholders!"
grep -q "YOUR_WHATSAPP_API_SERVER" config.example.yaml && echo "✅ API server placeholder found" || echo "❌ Missing API server placeholder!"
```

### 🔐 **6. Repository-Specific Check**
```bash
# Check for specific organization/repository names that should be generic
grep -q "your-org/" config.example.yaml && echo "✅ Generic org names used" || echo "❌ Real org names found!"
```

---

## 🚨 **If ANY Check Fails:**

1. **STOP** - Do not commit
2. Fix the identified issues
3. Re-run the checklist
4. Only commit when ALL checks pass

## ✅ **Safe to Commit Files:**

- `config.example.yaml` (with placeholders)
- `.env.example` (with placeholders) 
- `github_actions_monitor.py`
- All shell scripts (`.sh`)
- All documentation in `docs/`
- `.gitignore`
- Installation and test files

## ❌ **NEVER Commit:**

- `config.yaml` (your actual config)
- `.env` (your actual environment)
- `logs/*` (log files)
- `data/*` (state files)
- Any files with real tokens, IPs, or group IDs
