# JSON Control Character Fix for WhatsApp Notifications

## 🚨 **Issue: Bad Control Character in JSON**

**Error Message**: 
```
"Bad control character in string literal in JSON at position 109 (line 4 column 49)"
```

**Root Cause**: The `printf` approach was creating literal newlines in the JSON instead of proper JSON escape sequences (`\n`), causing the WhatsApp API to reject the malformed JSON.

## ✅ **Solution Applied**

### **New Approach: Using jq for Safe JSON Generation**

```yaml
whatsapp_notify:
  command: |
    if command -v jq &> /dev/null; then
      # Use jq for safe JSON generation (preferred)
      MESSAGE_TEXT="🚀 Deployment completed successfully!

Repository: $REPO_NAME
Workflow: $WORKFLOW_NAME
Branch: $BRANCH_NAME
Run #: $RUN_NUMBER
Commit: $COMMIT_MESSAGE
Time: $(date)" && \
      JSON_PAYLOAD=$(jq -n \
        --arg chatId "YOUR_WHATSAPP_GROUP_ID@g.us" \
        --arg text "$MESSAGE_TEXT" \
        '{
          chatId: $chatId,
          reply_to: null,
          text: $text,
          linkPreview: true,
          linkPreviewHighQuality: false,
          session: "default"
        }')
    else
      # Fallback for systems without jq
      JSON_PAYLOAD="{\"chatId\":\"YOUR_WHATSAPP_GROUP_ID@g.us\",\"text\":\"🚀 Deployment...\n\n...\"}"
    fi
```

### **How This Fixes the Issue**

1. **Safe JSON Construction**: `jq` properly escapes all special characters including newlines
2. **Variable Substitution**: Variables are expanded before being passed to `jq`
3. **Fallback Support**: Works even if `jq` is not installed
4. **Proper Escaping**: Newlines become `\n`, quotes become `\"`, etc.

## 🧪 **Added JSON Testing**

### **New Test Command**: `test_json_generation`
```yaml
test_json_generation:
  description: "Test JSON payload generation for WhatsApp"
  command: |
    echo "Testing JSON payload generation..." && \
    # Generate and display the JSON payload
    # Shows exactly what will be sent to WhatsApp API
```

This helps debug JSON generation issues before sending to the API.

## 📊 **Expected Results**

### **Before (Broken JSON)**:
```json
{
  "chatId": "YOUR_WHATSAPP_GROUP_ID@g.us",
  "text": "🚀 Deployment completed successfully!

Repository: your-org/your-frontend-repo
..."
}
```
*❌ Contains literal newlines (invalid JSON)*

### **After (Valid JSON)**:
```json
{
  "chatId": "YOUR_WHATSAPP_GROUP_ID@g.us",
  "text": "🚀 Deployment completed successfully!\\n\\nRepository: your-org/your-frontend-repo\\n..."
}
```
*✅ Properly escaped newlines (valid JSON)*

## 🚀 **Deployment Steps**

1. **Update configuration**:
   ```bash
   sudo cp config.yaml /opt/github-actions-monitor/config/
   ```

2. **Install jq if not available** (optional but recommended):
   ```bash
   # Ubuntu/Debian
   sudo apt-get install jq
   
   # RHEL/CentOS/Rocky
   sudo yum install jq
   # or
   sudo dnf install jq
   ```

3. **Restart service**:
   ```bash
   sudo systemctl restart github-actions-monitor
   ```

4. **Monitor logs**:
   ```bash
   sudo journalctl -u github-actions-monitor -f
   ```

## 🔍 **What You'll See in Logs**

### **JSON Generation Test**:
```
2025-08-03 15:30:00 - INFO - [5/8] Executing: Test JSON payload generation for WhatsApp
2025-08-03 15:30:00 - INFO -   stdout: Using jq for JSON generation
2025-08-03 15:30:00 - INFO -   stdout: Generated JSON:
2025-08-03 15:30:00 - INFO -   stdout: {
2025-08-03 15:30:00 - INFO -   stdout:   "chatId": "YOUR_WHATSAPP_GROUP_ID@g.us",
2025-08-03 15:30:00 - INFO -   stdout:   "text": "🚀 Test message\\n\\nRepository: your-org/your-frontend-repo\\n..."
2025-08-03 15:30:00 - INFO -   stdout: }
```

### **WhatsApp Notification Success**:
```
2025-08-03 15:30:05 - INFO - [8/8] Executing: Send WhatsApp notification
2025-08-03 15:30:05 - INFO -   stdout: Sending WhatsApp notification...
2025-08-03 15:30:05 - INFO -   stdout: WhatsApp notification sent successfully
2025-08-03 15:30:05 - INFO - ✓ Command completed successfully: Send WhatsApp notification
```

## 🎯 **Key Improvements**

1. **Robust JSON Generation**: Uses `jq` for safe JSON construction
2. **Proper Character Escaping**: All newlines, quotes, and special characters handled correctly
3. **Fallback Support**: Works with or without `jq` installed
4. **Debug Support**: JSON test command shows exactly what's being generated
5. **Variable Substitution**: All environment variables properly expanded

The WhatsApp notifications should now work perfectly with properly formatted JSON and expanded variables!
