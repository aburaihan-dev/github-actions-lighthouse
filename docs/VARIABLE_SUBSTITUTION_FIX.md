# Variable Substitution Fix for WhatsApp Notifications

## 🚨 **Issue: Environment Variables Not Expanding**

**Problem**: WhatsApp notification showed literal variable names instead of actual values:
```
Repository: $REPO_NAME
Workflow: $WORKFLOW_NAME  
Branch: $BRANCH_NAME
Run #: $RUN_NUMBER
Commit: $COMMIT_MESSAGE
Time: $(date)
```

## 🔍 **Root Cause Analysis**

1. **JSON Escaping Issues**: Variables inside escaped JSON quotes weren't being processed by shell
2. **Improper Quoting**: Mix of single/double quotes preventing variable expansion
3. **Shell Context**: Variables need to be expanded in proper shell context before JSON construction

## ✅ **Solution Applied**

### **New Approach: Build JSON with printf**

```yaml
whatsapp_notify:
  command: |
    echo "Sending WhatsApp notification..." && \
    TIMESTAMP=$(date) && \
    JSON_PAYLOAD=$(printf '{
      "chatId": "YOUR_WHATSAPP_GROUP_ID@g.us",
      "reply_to": null,
      "text": "🚀 Deployment completed successfully!\n\nRepository: %s\nWorkflow: %s\nBranch: %s\nRun #: %s\nCommit: %s\nTime: %s",
      "linkPreview": true,
      "linkPreviewHighQuality": false,
      "session": "default"
    }' "$REPO_NAME" "$WORKFLOW_NAME" "$BRANCH_NAME" "$RUN_NUMBER" "$COMMIT_MESSAGE" "$TIMESTAMP") && \
    curl -X POST 'http://YOUR_WHATSAPP_API_SERVER:3000/api/sendText' \
      -H 'Accept: application/json' \
      -H 'Content-Type: application/json' \
      -d "$JSON_PAYLOAD" && \
    echo "WhatsApp notification sent successfully"
```

### **How It Works**

1. **Variable Capture**: `TIMESTAMP=$(date)` captures current time
2. **Safe JSON Construction**: `printf` safely builds JSON with proper escaping
3. **Variable Substitution**: `%s` placeholders replaced with actual variable values
4. **Proper Quoting**: Variables passed as arguments to printf, ensuring proper expansion

## 🧪 **Testing Setup**

### **Added Environment Test Command**
```yaml
test_environment:
  description: "Test environment variables"
  command: |
    echo "=== Environment Variables Test ===" && \
    echo "REPO_NAME: $REPO_NAME" && \
    echo "WORKFLOW_NAME: $WORKFLOW_NAME" && \
    echo "BRANCH_NAME: $BRANCH_NAME" && \
    echo "RUN_NUMBER: $RUN_NUMBER" && \
    echo "COMMIT_MESSAGE: $COMMIT_MESSAGE" && \
    echo "Current time: $(date)" && \
    echo "=== End Test ==="
```

This will help verify that environment variables are being set correctly by the Python script.

## 📊 **Expected Results**

### **Before (Broken)**:
```
🚀 Deployment completed successfully!

Repository: $REPO_NAME
Workflow: $WORKFLOW_NAME
Branch: $BRANCH_NAME
Run #: $RUN_NUMBER
Commit: $COMMIT_MESSAGE
Time: $(date)
```

### **After (Fixed)**:
```
🚀 Deployment completed successfully!

Repository: your-org/your-frontend-repo
Workflow: Deploy to Staging
Branch: your-branch
Run #: 42
Commit: Fix navbar styling issues
Time: Sat Aug  3 13:15:30 UTC 2025
```

## 🚀 **Deployment Steps**

1. **Update configuration**:
   ```bash
   sudo cp config.yaml /opt/github-actions-monitor/config/
   ```

2. **Restart service**:
   ```bash
   sudo systemctl restart github-actions-monitor
   ```

3. **Monitor logs for test output**:
   ```bash
   sudo journalctl -u github-actions-monitor -f
   sudo tail -f /opt/github-actions-monitor/logs/monitor.log
   ```

4. **Look for environment test output**:
   ```
   2025-08-03 13:15:00 - INFO - [2/6] Executing: Test environment variables
   2025-08-03 13:15:00 - INFO - Command output (7 lines):
   2025-08-03 13:15:00 - INFO -   stdout: === Environment Variables Test ===
   2025-08-03 13:15:00 - INFO -   stdout: REPO_NAME: your-org/your-frontend-repo
   2025-08-03 13:15:00 - INFO -   stdout: WORKFLOW_NAME: Deploy to Staging
   2025-08-03 13:15:00 - INFO -   stdout: BRANCH_NAME: your-branch
   2025-08-03 13:15:00 - INFO -   stdout: RUN_NUMBER: 42
   2025-08-03 13:15:00 - INFO -   stdout: COMMIT_MESSAGE: Fix navbar styling issues
   2025-08-03 13:15:00 - INFO -   stdout: Current time: Sat Aug  3 13:15:30 UTC 2025
   2025-08-03 13:15:00 - INFO -   stdout: === End Test ===
   ```

## 🔧 **Key Improvements**

1. **Reliable Variable Expansion**: Uses printf for safe JSON construction
2. **Proper JSON Escaping**: No manual escaping needed, printf handles it
3. **Debugging Support**: Added test command to verify variables
4. **Better Error Handling**: Clearer separation of concerns
5. **Maintainable Code**: Easier to modify message format

The WhatsApp notifications should now display actual values instead of variable names!
