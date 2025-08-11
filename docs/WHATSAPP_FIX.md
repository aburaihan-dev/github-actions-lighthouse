# WhatsApp Notification Command Fixes

## 🚨 **Issues Found and Fixed**

### **Problem 1: Command Timeout (300 seconds)**
- **Issue**: curl command taking too long and timing out after 5 minutes
- **Root Cause**: Default timeout was too high for HTTP requests
- **Fix**: Added intelligent timeout management based on command type

### **Problem 2: JSON Formatting Issues**
- **Issue**: Unescaped quotes and newlines in JSON payload
- **Root Cause**: Single quotes around JSON, causing parsing issues
- **Fix**: Properly escaped JSON with double quotes

### **Problem 3: Variable Substitution**
- **Issue**: Environment variables not being expanded
- **Root Cause**: Single quotes prevent shell variable expansion
- **Fix**: Used double quotes and proper shell variable syntax `${VAR_NAME}`

### **Problem 4: Network Connectivity**
- **Issue**: Possible network issues to WhatsApp API server
- **Root Cause**: No connection testing or debugging
- **Fix**: Added connection test command and better error handling

## ✅ **Fixes Applied**

### **1. Intelligent Timeout Management**
```python
def _get_default_timeout(self, command: str) -> int:
    """Get appropriate timeout based on command type."""
    # HTTP/API requests - 60 seconds
    # Kubernetes operations - 120 seconds  
    # Git operations - 180 seconds
    # Docker operations - 300 seconds
    # Default - 120 seconds
```

### **2. Fixed WhatsApp Command**
```yaml
whatsapp_notify:
  description: "Send WhatsApp notification"
  command: |
    echo "Sending WhatsApp notification..." && \
    curl --connect-timeout 10 --max-time 30 -X POST \
      'http://YOUR_WHATSAPP_API_SERVER:3000/api/sendText' \
      -H 'Accept: application/json' \
      -H 'Content-Type: application/json' \
      -d "{
        \"chatId\": \"YOUR_WHATSAPP_GROUP_ID@g.us\",
        \"reply_to\": null,
        \"text\": \"🚀 Deployment completed successfully!\\n\\nRepository: ${REPO_NAME}\\nWorkflow: ${WORKFLOW_NAME}\\nBranch: ${BRANCH_NAME}\\nRun #: ${RUN_NUMBER}\\nCommit: ${COMMIT_MESSAGE}\\nTime: $(date)\",
        \"linkPreview\": true,
        \"linkPreviewHighQuality\": false,
        \"session\": \"default\"
      }" && \
    echo "WhatsApp notification sent successfully"
  working_directory: "/tmp"
  timeout: 45
```

### **3. Added Connection Test Command**
```yaml
test_whatsapp_connection:
  description: "Test WhatsApp API connectivity"
  command: |
    echo "Testing WhatsApp API connection..." && \
    curl --connect-timeout 5 --max-time 15 -v \
      -X GET 'http://YOUR_WHATSAPP_API_SERVER:3000/api/health' || \
    curl --connect-timeout 5 --max-time 15 -v \
      -X GET 'http://YOUR_WHATSAPP_API_SERVER:3000/' || \
    echo "WhatsApp API not reachable - check network connectivity"
  working_directory: "/tmp"
  timeout: 30
```

### **4. Enhanced Logging**
- Added timeout information to command execution logs
- Shows actual timeout value being used for each command
- Better error reporting for timeout issues

## 🔧 **Key Improvements**

1. **Shorter Timeouts**: 
   - HTTP requests: 60s default, 45s for WhatsApp
   - Connection timeout: 10s
   - Max time: 30s

2. **Proper JSON Escaping**:
   - Double quotes for JSON
   - Escaped internal quotes
   - Proper newline escaping (`\\n`)

3. **Environment Variable Expansion**:
   - Changed `$REPO_NAME` to `${REPO_NAME}`
   - Used double quotes to allow shell expansion

4. **Network Debugging**:
   - Added test command to verify API connectivity
   - Verbose curl output for debugging
   - Fallback connection attempts

5. **Better Error Handling**:
   - Echo statements for progress tracking
   - Success confirmation messages
   - Graceful failure with informative messages

## 🧪 **Testing the Fix**

After updating your installation, the enhanced logging will show:

```
2025-08-03 13:00:00 - INFO - [3/4] Executing: Test WhatsApp API connectivity
2025-08-03 13:00:00 - DEBUG - Timeout: 30s
2025-08-03 13:00:00 - INFO - Starting command execution: Test WhatsApp API connectivity
2025-08-03 13:00:05 - INFO - Command output (1 lines):
2025-08-03 13:00:05 - INFO -   stdout: Testing WhatsApp API connection...
2025-08-03 13:00:05 - INFO - ✓ Command completed successfully: Test WhatsApp API connectivity

2025-08-03 13:00:05 - INFO - [4/4] Executing: Send WhatsApp notification  
2025-08-03 13:00:05 - DEBUG - Timeout: 45s
2025-08-03 13:00:05 - INFO - Starting command execution: Send WhatsApp notification
2025-08-03 13:00:10 - INFO - Command output (2 lines):
2025-08-03 13:00:10 - INFO -   stdout: Sending WhatsApp notification...
2025-08-03 13:00:10 - INFO -   stdout: WhatsApp notification sent successfully
2025-08-03 13:00:10 - INFO - ✓ Command completed successfully: Send WhatsApp notification
```

## 🚀 **Deployment Steps**

1. **Update the configuration**:
   ```bash
   sudo cp config.yaml /opt/github-actions-monitor/config/
   ```

2. **Update the Python script**:
   ```bash
   sudo cp github_actions_monitor.py /opt/github-actions-monitor/
   ```

3. **Restart the service**:
   ```bash
   sudo systemctl restart github-actions-monitor
   ```

4. **Monitor the logs**:
   ```bash
   sudo journalctl -u github-actions-monitor -f
   sudo tail -f /opt/github-actions-monitor/logs/monitor.log
   ```

The WhatsApp notifications should now work reliably with proper timeouts and error handling!
