# Enhanced Command Execution Logging

This document describes the enhanced command execution logging features added to the GitHub Actions Monitor to help debug permission and execution issues with CLI commands.

## Features Added

### 1. Comprehensive Command Logging

The monitor now provides detailed logging for every command execution, including:

- **Command Details**: Full command text, description, and working directory
- **Permission Information**: User/group context, directory permissions, and access rights
- **Environment Variables**: Workflow-specific environment variables passed to commands
- **Execution Timing**: Start time, end time, and total execution duration
- **Output Capture**: Detailed stdout and stderr with line-by-line logging
- **Error Analysis**: Enhanced error reporting with context and debugging information

### 2. Execution Map Support

The monitor now supports the modern `execution_map` configuration from `config.yaml`:

- Repository-specific command execution
- Branch-specific command selection
- Named command definitions with reusable configurations
- Fallback to wildcard (`*`) patterns for default behavior

### 3. Configurable Logging Levels

New logging configuration options in `config.yaml`:

```yaml
logging:
  # Command execution logging
  commands:
    # Log level for command execution details (DEBUG, INFO, WARNING, ERROR)
    log_level: "DEBUG"
    
    # Log command output to separate lines (easier to read)
    detailed_output: true
    
    # Log environment variables passed to commands
    log_environment: true
    
    # Log permission and user context information
    log_permissions: true
```

## Example Log Output

When a command is executed, you'll see detailed logging like this:

```
2025-08-03 11:21:53,632 - INFO - [1/3] Executing: Restart frontend service
2025-08-03 11:21:53,632 - DEBUG - === Command Execution Details ===
2025-08-03 11:21:53,632 - DEBUG - Description: Restart frontend service
2025-08-03 11:21:53,632 - DEBUG - Command: kubectl rollout restart deployment/your-frontend -n your-namespace
2025-08-03 11:21:53,632 - DEBUG - Working directory: /tmp
2025-08-03 11:21:53,633 - DEBUG - Working dir exists: YES (mode: 777)
2025-08-03 11:21:53,633 - DEBUG - Directory permissions: read, write, execute
2025-08-03 11:21:53,635 - DEBUG - Running as user: monitor (uid: 1001)
2025-08-03 11:21:53,635 - DEBUG - Running as group: monitor (gid: 1001)
2025-08-03 11:21:53,635 - DEBUG - Workflow environment variables:
2025-08-03 11:21:53,635 - DEBUG -   REPO_NAME=your-org/your-frontend-repo
2025-08-03 11:21:53,635 - DEBUG -   WORKFLOW_NAME=your-workflow.yml
2025-08-03 11:21:53,635 - DEBUG -   BRANCH_NAME=your-branch
2025-08-03 11:21:53,635 - DEBUG -   RUN_NUMBER=42
2025-08-03 11:21:53,635 - DEBUG -   COMMIT_SHA=abc123def456
2025-08-03 11:21:53,635 - DEBUG -   COMMIT_MESSAGE=Fix frontend deployment
2025-08-03 11:21:53,635 - DEBUG - === End Command Details ===
2025-08-03 11:21:53,635 - INFO - Starting command execution: Restart frontend service
2025-08-03 11:21:53,639 - DEBUG - Command execution completed in 0.85s
2025-08-03 11:21:53,639 - DEBUG - Exit code: 0
2025-08-03 11:21:53,639 - INFO - Command output (1 lines):
2025-08-03 11:21:53,639 - INFO -   stdout: deployment.apps/your-frontend restarted
2025-08-03 11:21:53,639 - INFO - ✓ Command completed successfully: Restart frontend service
```

## Error Debugging

The enhanced logging helps identify common issues:

### Permission Errors
```
2025-08-03 11:21:53,691 - ERROR - Permission denied executing command after 0.02s: Restart backend service
2025-08-03 11:21:53,691 - ERROR - Permission error details: [Errno 13] Permission denied
2025-08-03 11:21:53,691 - ERROR - Current working directory: /home/monitor
2025-08-03 11:21:53,691 - ERROR - Attempted working directory: /var/deployment
2025-08-03 11:21:53,691 - ERROR - Shell command: kubectl rollout restart deployment/your-backend -n your-namespace
2025-08-03 11:21:53,691 - ERROR - Shell path: /bin/sh
2025-08-03 11:21:53,691 - ERROR - Shell permissions: 755
```

### Missing Directories
```
2025-08-03 11:21:53,691 - WARNING - Working directory does not exist: /nonexistent/directory
2025-08-03 11:21:53,692 - ERROR - File not found executing command after 0.00s: Git pull command
2025-08-03 11:21:53,692 - ERROR - Working directory does not exist: /nonexistent/directory
```

### Command Not Found
```
2025-08-03 11:21:53,697 - DEBUG - Exit code: 127
2025-08-03 11:21:53,697 - WARNING -   stderr: /bin/sh: kubectl: command not found
2025-08-03 11:21:53,697 - ERROR - ✗ Command failed: Restart frontend service
```

## Environment Variables

The following environment variables are automatically set for each command:

- `REPO_NAME`: Repository name (e.g., "your-org/your-frontend-repo")
- `WORKFLOW_NAME`: Workflow name (e.g., "your-workflow.yml")
- `WORKFLOW_ID`: Workflow ID number
- `BRANCH_NAME`: Branch name (e.g., "your-branch")
- `RUN_NUMBER`: Workflow run number
- `RUN_ID`: Workflow run ID
- `COMMIT_SHA`: Commit SHA hash
- `COMMIT_MESSAGE`: Commit message

These can be used in your commands for dynamic behavior.

## Troubleshooting Common Issues

### 1. Permission Issues
- Check the user/group shown in the logs
- Verify directory permissions (shown in octal format)
- Ensure the monitor user has necessary permissions for kubectl, docker, etc.

### 2. Command Not Found
- Check if the command is in the PATH
- Verify the command is installed on the system
- Consider using full paths to executables

### 3. Working Directory Issues
- Ensure the working directory exists
- Check directory permissions
- Consider using absolute paths

### 4. Environment Issues
- Check if required environment variables are set
- Verify kubeconfig, docker credentials, etc.
- Check the environment variables logged by the monitor

## Configuration Examples

### Minimal Logging (Production)
```yaml
logging:
  level: "INFO"
  commands:
    log_level: "INFO"
    detailed_output: false
    log_environment: false
    log_permissions: false
```

### Full Debugging (Development)
```yaml
logging:
  level: "DEBUG"
  commands:
    log_level: "DEBUG"
    detailed_output: true
    log_environment: true
    log_permissions: true
```

## Migration from Legacy Configuration

If you're still using the legacy `on_success` configuration, consider migrating to the new `execution_map` format:

### Old Format (Deprecated)
```yaml
commands:
  on_success:
    - description: "Restart frontend"
      command: "kubectl rollout restart deployment/your-frontend -n your-namespace"
      working_directory: "/tmp"
```

### New Format (Recommended)
```yaml
commands:
  definitions:
    restart_frontend:
      description: "Restart frontend service"
      command: "kubectl rollout restart deployment/your-frontend -n your-namespace"
      working_directory: "/tmp"
  
  execution_map:
    "your-org/your-frontend-repo":
      "your-branch":
        - "restart_frontend"
```

The new format provides better organization, reusability, and flexibility for different repositories and branches.
