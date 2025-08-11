#!/usr/bin/env python3
"""
GitHub Actions Monitor Service

This service monitors GitHub Actions workflows and executes shell commands
when workflows complete successfully. Designed to run as a systemd service.

Author: GitHub Copilot
Date: July 2025
"""

import os
import sys
import json
import time
import signal
import logging
import subprocess
import threading
import concurrent.futures
import pwd
import grp
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
import yaml
from github import Github, GithubException

# Import timezone handling
try:
    import zoneinfo
except ImportError:
    # Fallback for Python < 3.9
    try:
        from backports import zoneinfo
    except ImportError:
        # If no timezone library available, we'll use UTC
        zoneinfo = None

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    # Look for .env file in current directory and parent directories
    env_path = Path('.env')
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded environment variables from: {env_path.absolute()}")
    else:
        # Also check in the script's directory
        script_dir = Path(__file__).parent
        env_path = script_dir / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            print(f"Loaded environment variables from: {env_path.absolute()}")
except ImportError:
    # python-dotenv not installed, skip .env file loading
    pass


class GitHubActionsMonitor:
    """Main monitor class for GitHub Actions workflows."""
    
    def __init__(self, config_path: str = "config.yaml", local_mode: bool = False):
        """Initialize the monitor with configuration."""
        self.config_path = config_path
        self.local_mode = local_mode
        self.config = self._load_config()
        self.github = None
        self.repos = {}
        self.running = False
        self.state_data = {}
        self.last_health_update = 0
        
        # Parallel processing configuration
        self.max_workers = self.config.get('monitoring', {}).get('max_parallel_workers', 3)
        self.parallel_enabled = self.config.get('monitoring', {}).get('enable_parallel', True)
        self.repo_timeout = self.config.get('monitoring', {}).get('timeout_per_repo', 60)
        self._execution_lock = threading.Lock()
        self._state_lock = threading.Lock()
        
        # Setup timezone
        self._setup_timezone()
        
        # Override paths for local mode
        if self.local_mode:
            self._setup_local_mode_paths()
        
        # Setup logging
        self._setup_logging()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        mode_str = "local" if self.local_mode else "server"
        parallel_str = f"parallel (max {self.max_workers} workers)" if self.parallel_enabled else "sequential"
        self.logger.info(f"GitHub Actions Monitor initialized in {mode_str} mode with {parallel_str} processing")
    
    def _load_config(self) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Substitute environment variables
            config = self._substitute_env_vars(config)
            return config
        except Exception as e:
            print(f"Error loading config: {e}")
            sys.exit(1)
    
    def _substitute_env_vars(self, obj):
        """Recursively substitute environment variables in config."""
        if isinstance(obj, dict):
            return {key: self._substitute_env_vars(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            env_var = obj[2:-1]
            return os.getenv(env_var, obj)
        return obj
    
    def _setup_timezone(self):
        """Setup timezone configuration."""
        # Get timezone from config, default to Asia/Dhaka
        timezone_name = self.config.get('logging', {}).get('timezone', 'Asia/Dhaka')
        
        try:
            if zoneinfo:
                self.display_timezone = zoneinfo.ZoneInfo(timezone_name)
            else:
                # Fallback to UTC if zoneinfo is not available
                self.display_timezone = timezone.utc
                if timezone_name != 'UTC':
                    print(f"Warning: zoneinfo not available, using UTC instead of {timezone_name}")
        except Exception as e:
            print(f"Warning: Invalid timezone '{timezone_name}', using UTC: {e}")
            self.display_timezone = timezone.utc
        
        # Store timezone name for logging
        self.timezone_name = timezone_name if hasattr(self, 'display_timezone') and self.display_timezone != timezone.utc else 'UTC'
    
    def _format_timestamp(self, dt):
        """Format datetime with configured timezone."""
        if dt is None:
            return "unknown"
        
        # Convert UTC datetime to display timezone
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        elif dt.tzinfo != timezone.utc:
            dt = dt.astimezone(timezone.utc)
        
        # Convert to display timezone
        display_dt = dt.astimezone(self.display_timezone)
        return display_dt.strftime(f'%Y-%m-%d %H:%M:%S {self.timezone_name}')
    
    def _get_current_time(self):
        """Get current time in UTC for internal calculations."""
        return datetime.now(timezone.utc)
    
    def _setup_local_mode_paths(self):
        """Setup local paths for development/testing mode."""
        current_dir = Path.cwd()
        
        # Override configuration with local paths
        if 'logging' not in self.config:
            self.config['logging'] = {}
        if 'file' not in self.config['logging']:
            self.config['logging']['file'] = {}
        
        # Set local log path
        self.config['logging']['file']['path'] = str(current_dir / 'logs' / 'monitor.log')
        
        # Set local state path
        if 'state' not in self.config:
            self.config['state'] = {}
        self.config['state']['state_file'] = str(current_dir / 'data' / 'state.json')
        
        # Set local health check path
        if 'health' not in self.config:
            self.config['health'] = {}
        self.config['health']['file'] = str(current_dir / 'data' / 'health')
        
        print(f"Local mode enabled - using paths relative to: {current_dir}")
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        
        # Create logger
        self.logger = logging.getLogger('github_actions_monitor')
        self.logger.setLevel(log_level)
        
        # Clear any existing handlers
        self.logger.handlers = []
        
        # Setup file logging
        file_config = log_config.get('file', {})
        if file_config:
            log_path = file_config.get('path', '/var/log/github-actions-monitor/monitor.log')
            log_dir = Path(log_path).parent
            
            try:
                log_dir.mkdir(parents=True, exist_ok=True)
                
                from logging.handlers import TimedRotatingFileHandler
                
                # Use daily rotation and keep 30 days of logs
                file_handler = TimedRotatingFileHandler(
                    log_path,
                    when='midnight',           # Rotate at midnight
                    interval=1,                # Rotate every 1 day
                    backupCount=30,            # Keep 30 days of logs
                    encoding='utf-8',          # UTF-8 encoding for log files
                    delay=False,               # Don't delay file creation
                    utc=True                   # Use UTC time for rotation
                )
                
                # Set the suffix for rotated files (YYYY-MM-DD format)
                file_handler.suffix = "%Y-%m-%d"
                
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                file_handler.setFormatter(file_formatter)
                self.logger.addHandler(file_handler)
                
                if self.local_mode:
                    print(f"Logging to file: {log_path}")
                    print(f"Daily log rotation enabled, keeping 30 days of logs")
                    
            except PermissionError:
                # If we can't write to the configured path, skip file logging
                if not self.local_mode:
                    print(f"Cannot write to log path {log_path}, skipping file logging")
                    print("Run with --local-mode for development or use sudo for production")
        
        # Setup console logging
        console_config = log_config.get('console', {})
        if console_config.get('enabled', True):
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def _load_state(self) -> Dict:
        """Load state from file."""
        state_file = self.config.get('state', {}).get('state_file', '/var/lib/github-actions-monitor/state.json')
        state_path = Path(state_file)
        
        if state_path.exists():
            try:
                with open(state_path, 'r') as f:
                    state = json.load(f)
                
                # Convert executed_runs from list to set for efficient lookups
                if 'executed_runs' in state and isinstance(state['executed_runs'], list):
                    state['executed_runs'] = set(state['executed_runs'])
                elif 'executed_runs' not in state:
                    state['executed_runs'] = set()
                
                return state
            except Exception as e:
                self.logger.warning(f"Error loading state file: {e}")
        
        return {'last_checked_runs': {}, 'executed_runs': set()}
    
    def _save_state(self):
        """Save state to file."""
        state_file = self.config.get('state', {}).get('state_file', '/var/lib/github-actions-monitor/state.json')
        state_path = Path(state_file)
        
        try:
            state_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert set to list for JSON serialization
            state_to_save = self.state_data.copy()
            if 'executed_runs' in state_to_save and isinstance(state_to_save['executed_runs'], set):
                state_to_save['executed_runs'] = list(state_to_save['executed_runs'])
            
            with open(state_path, 'w') as f:
                json.dump(state_to_save, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving state file: {e}")
    
    def _update_health_check(self):
        """Update health check file."""
        health_config = self.config.get('health', {})
        if not health_config.get('enabled', False):
            return
        
        health_file = health_config.get('file', '/var/run/github-actions-monitor/health')
        health_path = Path(health_file)
        
        try:
            health_path.parent.mkdir(parents=True, exist_ok=True)
            with open(health_path, 'w') as f:
                f.write(f"OK - {self._get_current_time().isoformat()}")
            self.last_health_update = time.time()
        except Exception as e:
            self.logger.error(f"Error updating health check file: {e}")
    
    def _initialize_github_client(self):
        """Initialize GitHub client and repositories."""
        try:
            github_config = self.config['github']
            token = github_config['token']
            
            if not token or token.startswith("${"):
                raise ValueError("GitHub token not found. Set GITHUB_TOKEN environment variable.")
            
            # Initialize GitHub client
            base_url = github_config.get('api_base_url', 'https://api.github.com')
            timeout = github_config.get('timeout', 30)
            
            self.github = Github(
                token,
                base_url=base_url,
                timeout=timeout,
                per_page=100
            )
            
            # Get repositories
            repositories = self.config.get('repositories', [])
            if not repositories:
                raise ValueError("No repositories configured for monitoring")
            
            self.repos = {}
            for repo_name in repositories:
                try:
                    repo = self.github.get_repo(repo_name)
                    self.repos[repo_name] = repo
                    self.logger.info(f"Connected to GitHub repository: {repo_name}")
                    
                    # Test API access
                    repo.get_workflows().totalCount
                    self.logger.info(f"GitHub API access verified for: {repo_name}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to connect to repository {repo_name}: {e}")
                    continue
            
            if not self.repos:
                raise ValueError("No repositories could be connected")
            
        except Exception as e:
            self.logger.error(f"Error initializing GitHub client: {e}")
            raise
    
    def _get_workflows_to_monitor(self) -> Dict[str, List]:
        """Get list of workflows to monitor for each repository based on configuration."""
        try:
            workflows_by_repo = {}
            workflows_config = self.config.get('monitoring', {}).get('workflows', [])
            
            for repo_name, repo in self.repos.items():
                try:
                    all_workflows = list(repo.get_workflows())
                    
                    if not workflows_config:
                        # Monitor all workflows
                        workflows_by_repo[repo_name] = all_workflows
                    else:
                        # Filter workflows based on configuration
                        filtered_workflows = []
                        for workflow in all_workflows:
                            # Check by name or filename
                            if (workflow.name in workflows_config or 
                                str(workflow.id) in workflows_config or
                                workflow.path.split('/')[-1] in workflows_config):
                                filtered_workflows.append(workflow)
                        workflows_by_repo[repo_name] = filtered_workflows
                    
                    self.logger.info(f"Repository {repo_name}: monitoring {len(workflows_by_repo[repo_name])} workflows")
                    
                except Exception as e:
                    self.logger.error(f"Error getting workflows for {repo_name}: {e}")
                    workflows_by_repo[repo_name] = []
            
            return workflows_by_repo
            
        except Exception as e:
            self.logger.error(f"Error getting workflows: {e}")
            return {}
    
    def _should_monitor_branch(self, branch: str) -> bool:
        """Check if branch should be monitored based on configuration."""
        branches_config = self.config.get('monitoring', {}).get('branches', [])
        
        if not branches_config:
            return True  # Monitor all branches
        
        return branch in branches_config
    
    def _get_new_successful_runs(self, repo_name: str, workflow) -> List:
        """Get new successful workflow runs for a specific repository and workflow."""
        try:
            # Get recent completed workflow runs
            runs = workflow.get_runs(status='completed')
            
            # Filter for successful runs only
            successful_runs = [run for run in runs if run.conclusion == 'success']
            
            # Get current time for 5-minute check
            current_time = self._get_current_time()
            
            # Get executed runs to avoid duplicate executions
            executed_runs = self.state_data.get('executed_runs', set())
            if isinstance(executed_runs, list):
                executed_runs = set(executed_runs)  # Convert old list format to set
            
            new_successful_runs = []
            
            for run in successful_runs:
                # Check if we've already executed commands for this run
                run_key = f"{repo_name}:{workflow.id}:{run.id}"
                if run_key in executed_runs:
                    continue
                
                # Check if branch should be monitored
                if not self._should_monitor_branch(run.head_branch):
                    continue
                
                # Check if run completed within last 5 minutes
                if run.updated_at:
                    time_diff = current_time - run.updated_at
                    if time_diff.total_seconds() > 300:  # 5 minutes = 300 seconds
                        self.logger.debug(f"Skipping old run: {repo_name}:{workflow.name} #{run.run_number} "
                                        f"(completed {time_diff.total_seconds():.0f}s ago)")
                        continue
                
                new_successful_runs.append(run)
                self.logger.debug(f"Found new run within 5min: {repo_name}:{workflow.name} #{run.run_number}")
            
            return new_successful_runs
            
        except Exception as e:
            self.logger.error(f"Error getting workflow runs for {repo_name}:{workflow.name}: {e}")
            return []
    
    def _execute_commands(self, repo_name: str, workflow, workflow_run):
        """Execute configured commands for successful workflow run."""
        # Get commands configuration
        commands_config = self.config.get('commands', {})
        
        # Check for new execution_map configuration first
        execution_map = commands_config.get('execution_map', {})
        command_definitions = commands_config.get('definitions', {})
        
        # Determine which commands to execute
        commands_to_execute = []
        
        if execution_map:
            # Use new execution_map configuration
            branch_name = workflow_run.head_branch or 'unknown'
            
            # Look for repo-specific configuration
            repo_commands = None
            if repo_name in execution_map:
                repo_config = execution_map[repo_name]
                if branch_name in repo_config:
                    repo_commands = repo_config[branch_name]
                elif '*' in repo_config:
                    repo_commands = repo_config['*']
            
            # Fall back to default configuration
            if not repo_commands and '*' in execution_map:
                default_config = execution_map['*']
                if branch_name in default_config:
                    repo_commands = default_config[branch_name]
                elif '*' in default_config:
                    repo_commands = default_config['*']
            
            if repo_commands:
                # Convert command names to command definitions
                for cmd_name in repo_commands:
                    if cmd_name in command_definitions:
                        cmd_def = command_definitions[cmd_name].copy()
                        cmd_def['name'] = cmd_name
                        commands_to_execute.append(cmd_def)
                    else:
                        self.logger.warning(f"Command definition not found: {cmd_name}")
        else:
            # Fall back to legacy on_success configuration
            legacy_commands = commands_config.get('on_success', [])
            commands_to_execute = legacy_commands
        
        if not commands_to_execute:
            self.logger.info(f"No commands configured for {repo_name} on branch {workflow_run.head_branch}")
            return
        
        # Create run key for tracking
        run_key = f"{repo_name}:{workflow.id}:{workflow_run.id}"
        
        self.logger.info(f"Executing {len(commands_to_execute)} commands for successful workflow run: "
                        f"{repo_name} - {workflow_run.name} (#{workflow_run.run_number}) on branch {workflow_run.head_branch}")
        
        # Track if any commands were executed successfully
        commands_executed = False
        
        # Set environment variables for command execution
        env_vars = self._prepare_command_environment(repo_name, workflow, workflow_run)
        
        for i, cmd_config in enumerate(commands_to_execute, 1):
            description = "Unnamed command"  # Default value
            try:
                description = cmd_config.get('description', cmd_config.get('name', 'Unnamed command'))
                command = cmd_config.get('command', '')
                working_dir = cmd_config.get('working_directory', os.getcwd())
                # Get timeout from command config, default based on command type
                timeout = cmd_config.get('timeout', self._get_default_timeout(command))
                
                if not command:
                    self.logger.warning(f"Empty command in configuration: {description}")
                    continue
                
                self.logger.info(f"[{i}/{len(commands_to_execute)}] Executing: {description}")
                
                # Log detailed command information for debugging
                self._log_command_details(command, working_dir, env_vars, description, timeout)
                
                # Execute command with enhanced logging
                result = self._execute_single_command(command, working_dir, env_vars, description, timeout)
                
                if result and result.returncode == 0:
                    self.logger.info(f"✓ Command completed successfully: {description}")
                    commands_executed = True
                else:
                    self.logger.error(f"✗ Command failed: {description}")
                    if result:
                        self.logger.error(f"Return code: {result.returncode}")
                
            except Exception as e:
                self.logger.error(f"✗ Error executing command '{description}': {e}")
        
        # Mark this run as executed to prevent duplicate executions
        if commands_executed or not commands_to_execute:
            if 'executed_runs' not in self.state_data:
                self.state_data['executed_runs'] = set()
            
            # Convert to set if it's a list (backward compatibility)
            if isinstance(self.state_data['executed_runs'], list):
                self.state_data['executed_runs'] = set(self.state_data['executed_runs'])
            
            self.state_data['executed_runs'].add(run_key)
            self.logger.debug(f"Marked run as executed: {run_key}")
    
    def _prepare_command_environment(self, repo_name: str, workflow, workflow_run) -> dict:
        """Prepare environment variables for command execution."""
        env = os.environ.copy()
        
        # Get commit author information
        commit_author = 'unknown'
        try:
            if workflow_run.head_sha:
                # Get the repository object
                repo = self.repos.get(repo_name)
                if repo:
                    commit = repo.get_commit(workflow_run.head_sha)
                    if commit.author:
                        commit_author = commit.author.login if commit.author.login else commit.author.name
                    elif commit.commit and commit.commit.author:
                        commit_author = commit.commit.author.name
        except Exception as e:
            self.logger.debug(f"Could not fetch commit author for {workflow_run.head_sha}: {e}")
        
        # Add workflow-specific environment variables
        env.update({
            'REPO_NAME': repo_name,
            'WORKFLOW_NAME': workflow.name,
            'WORKFLOW_ID': str(workflow.id),
            'BRANCH_NAME': workflow_run.head_branch or 'unknown',
            'RUN_NUMBER': str(workflow_run.run_number),
            'RUN_ID': str(workflow_run.id),
            'COMMIT_SHA': workflow_run.head_sha or 'unknown',
            'COMMIT_MESSAGE': workflow_run.display_title or 'unknown',
            'COMMIT_AUTHOR': commit_author
        })
        
        return env
    
    def _get_default_timeout(self, command: str) -> int:
        """Get appropriate timeout based on command type."""
        command_lower = command.lower()
        
        # HTTP/API requests - short timeout
        if any(keyword in command_lower for keyword in ['curl', 'wget', 'http']):
            return 60  # 1 minute for HTTP requests
        
        # Kubernetes operations - medium timeout
        if 'kubectl' in command_lower:
            return 120  # 2 minutes for kubectl commands
        
        # Git operations - medium timeout
        if any(keyword in command_lower for keyword in ['git', 'clone', 'pull', 'push']):
            return 180  # 3 minutes for git operations
        
        # Docker operations - longer timeout
        if any(keyword in command_lower for keyword in ['docker', 'podman']):
            return 300  # 5 minutes for container operations
        
        # Default timeout for other commands
        return 120  # 2 minutes default
    
    def _log_command_details(self, command: str, working_dir: str, env_vars: dict, description: str, timeout: int = 120):
        """Log detailed information about command execution for debugging."""
        # Get command logging configuration
        command_log_config = self.config.get('logging', {}).get('commands', {})
        log_permissions = command_log_config.get('log_permissions', True)
        log_environment = command_log_config.get('log_environment', True)
        
        self.logger.debug(f"=== Command Execution Details ===")
        self.logger.debug(f"Description: {description}")
        self.logger.debug(f"Command: {command}")
        self.logger.debug(f"Working directory: {working_dir}")
        self.logger.debug(f"Timeout: {timeout}s")
        
        # Check if working directory exists and is accessible
        if log_permissions:
            try:
                if os.path.exists(working_dir):
                    dir_stat = os.stat(working_dir)
                    self.logger.debug(f"Working dir exists: YES (mode: {oct(dir_stat.st_mode)[-3:]})")
                    
                    # Check if we can read/write/execute in the directory
                    permissions = []
                    if os.access(working_dir, os.R_OK):
                        permissions.append("read")
                    if os.access(working_dir, os.W_OK):
                        permissions.append("write")
                    if os.access(working_dir, os.X_OK):
                        permissions.append("execute")
                    self.logger.debug(f"Directory permissions: {', '.join(permissions) if permissions else 'NONE'}")
                else:
                    self.logger.warning(f"Working directory does not exist: {working_dir}")
            except Exception as e:
                self.logger.warning(f"Cannot check working directory: {e}")
            
            # Log current user and process info
            try:
                import pwd
                import grp
                current_user = pwd.getpwuid(os.getuid())
                current_group = grp.getgrgid(os.getgid())
                self.logger.debug(f"Running as user: {current_user.pw_name} (uid: {os.getuid()})")
                self.logger.debug(f"Running as group: {current_group.gr_name} (gid: {os.getgid()})")
            except Exception as e:
                self.logger.debug(f"Could not get user/group info: {e}")
        
        # Log workflow-specific environment variables
        if log_environment:
            workflow_env_vars = {k: v for k, v in env_vars.items() 
                               if k in ['REPO_NAME', 'WORKFLOW_NAME', 'BRANCH_NAME', 'RUN_NUMBER', 'COMMIT_SHA', 'COMMIT_MESSAGE', 'COMMIT_AUTHOR']}
            if workflow_env_vars:
                self.logger.debug(f"Workflow environment variables:")
                for k, v in workflow_env_vars.items():
                    self.logger.debug(f"  {k}={v}")
        
        self.logger.debug(f"=== End Command Details ===")
    
    def _execute_single_command(self, command: str, working_dir: str, env_vars: dict, description: str, timeout: int = 120):
        """Execute a single command with comprehensive logging and non-blocking behavior."""
        # Get command logging configuration
        command_log_config = self.config.get('logging', {}).get('commands', {})
        detailed_output = command_log_config.get('detailed_output', True)
        
        start_time = time.time()
        
        try:
            # Log command start
            self.logger.info(f"🚀 Starting command execution: {description}")
            
            # Execute command with enhanced error handling
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                env=env_vars,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False  # Don't raise exception on non-zero exit codes
            )
            
            execution_time = time.time() - start_time
            
            # Log execution results
            self.logger.debug(f"⏱️ Command execution completed in {execution_time:.2f}s")
            self.logger.debug(f"📊 Exit code: {result.returncode}")
            
            # Log stdout if present
            if result.stdout:
                stdout_content = result.stdout.strip()
                if detailed_output:
                    stdout_lines = stdout_content.split('\n')
                    self.logger.info(f"📤 Command output ({len(stdout_lines)} lines):")
                    for line in stdout_lines:
                        self.logger.info(f"  stdout: {line}")
                else:
                    # Truncate long output if detailed_output is False
                    if len(stdout_content) > 500:
                        self.logger.info(f"📤 Command output (truncated): {stdout_content[:500]}...")
                    else:
                        self.logger.info(f"📤 Command output: {stdout_content}")
            else:
                self.logger.debug("📭 No stdout output")
            
            # Log stderr if present (but not as error if command succeeded)
            if result.stderr:
                stderr_content = result.stderr.strip()
                if result.returncode == 0:
                    # Command succeeded but has stderr - log as warning
                    if detailed_output:
                        stderr_lines = stderr_content.split('\n')
                        self.logger.warning(f"⚠️ Command warning output ({len(stderr_lines)} lines):")
                        for line in stderr_lines:
                            self.logger.warning(f"  stderr: {line}")
                    else:
                        if len(stderr_content) > 500:
                            self.logger.warning(f"⚠️ Command warning output (truncated): {stderr_content[:500]}...")
                        else:
                            self.logger.warning(f"⚠️ Command warning output: {stderr_content}")
                else:
                    # Command failed - log stderr as error
                    if detailed_output:
                        stderr_lines = stderr_content.split('\n')
                        self.logger.warning(f"❌ Command error output ({len(stderr_lines)} lines):")
                        for line in stderr_lines:
                            self.logger.warning(f"  stderr: {line}")
                    else:
                        if len(stderr_content) > 500:
                            self.logger.warning(f"❌ Command error output (truncated): {stderr_content[:500]}...")
                        else:
                            self.logger.warning(f"❌ Command error output: {stderr_content}")
            
            return result
            
        except subprocess.TimeoutExpired as e:
            execution_time = time.time() - start_time
            self.logger.error(f"⏱️ Command timed out after {execution_time:.2f}s (limit: {timeout}s): {description}")
            self.logger.error(f"🔥 Command that timed out: {command}")
            
            # Log partial output if available
            if hasattr(e, 'stdout') and e.stdout:
                self.logger.warning(f"📤 Partial stdout before timeout: {e.stdout.strip()}")
            if hasattr(e, 'stderr') and e.stderr:
                self.logger.warning(f"📤 Partial stderr before timeout: {e.stderr.strip()}")
            
            # Create a mock result object for timeout
            class TimeoutResult:
                def __init__(self):
                    self.returncode = -1  # Indicate timeout
                    self.stdout = e.stdout if hasattr(e, 'stdout') and e.stdout else ""
                    self.stderr = f"Command timed out after {timeout} seconds"
            
            return TimeoutResult()
            
        except PermissionError as e:
            execution_time = time.time() - start_time
            self.logger.error(f"🔒 Permission denied executing command after {execution_time:.2f}s: {description}")
            self.logger.error(f"🔒 Permission error details: {e}")
            
            # Try to provide more helpful debugging info
            try:
                import stat
                working_dir_stat = os.stat(working_dir)
                self.logger.error(f"🔍 Working directory permissions: {oct(working_dir_stat.st_mode)[-3:]}")
                self.logger.error(f"🔍 Working directory owner: uid={working_dir_stat.st_uid}, gid={working_dir_stat.st_gid}")
            except Exception as debug_e:
                self.logger.debug(f"Could not get working directory info: {debug_e}")
            
            return None
            
        except FileNotFoundError as e:
            execution_time = time.time() - start_time
            self.logger.error(f"📁 Command not found after {execution_time:.2f}s: {description}")
            self.logger.error(f"📁 File not found error: {e}")
            return None
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"💥 Unexpected error executing command after {execution_time:.2f}s: {description}")
            self.logger.error(f"💥 Error details: {e}")
            return None
            if result.stderr:
                stderr_content = result.stderr.strip()
                if detailed_output:
                    stderr_lines = stderr_content.split('\n')
                    self.logger.warning(f"Command error output ({len(stderr_lines)} lines):")
                    for line in stderr_lines:
                        self.logger.warning(f"  stderr: {line}")
                else:
                    # Always show stderr in full for debugging
                    self.logger.warning(f"Command error output: {stderr_content}")
            
            return result
            
        except subprocess.TimeoutExpired as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Command timed out after {execution_time:.2f}s: {description}")
            self.logger.error(f"Command that timed out: {command}")
            if e.stdout:
                self.logger.error(f"Partial stdout: {e.stdout}")
            if e.stderr:
                self.logger.error(f"Partial stderr: {e.stderr}")
            return None
            
        except PermissionError as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Permission denied executing command after {execution_time:.2f}s: {description}")
            self.logger.error(f"Permission error details: {e}")
            
            # Additional permission debugging
            try:
                self.logger.error(f"Current working directory: {os.getcwd()}")
                self.logger.error(f"Attempted working directory: {working_dir}")
                self.logger.error(f"Shell command: {command}")
                
                # Check if the shell is accessible
                import shutil
                shell_path = shutil.which('sh')
                if shell_path:
                    self.logger.error(f"Shell path: {shell_path}")
                    shell_stat = os.stat(shell_path)
                    self.logger.error(f"Shell permissions: {oct(shell_stat.st_mode)[-3:]}")
                else:
                    self.logger.error("Shell not found in PATH")
                    
            except Exception as debug_e:
                self.logger.error(f"Could not gather additional permission debug info: {debug_e}")
            
            return None
            
        except FileNotFoundError as e:
            execution_time = time.time() - start_time
            self.logger.error(f"File not found executing command after {execution_time:.2f}s: {description}")
            self.logger.error(f"File not found details: {e}")
            self.logger.error(f"Command: {command}")
            self.logger.error(f"Working directory: {working_dir}")
            
            # Check if working directory exists
            if not os.path.exists(working_dir):
                self.logger.error(f"Working directory does not exist: {working_dir}")
            
            return None
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Unexpected error executing command after {execution_time:.2f}s: {description}")
            self.logger.error(f"Error details: {e}")
            self.logger.error(f"Error type: {type(e).__name__}")
            self.logger.error(f"Command: {command}")
            self.logger.error(f"Working directory: {working_dir}")
            return None
    
    def _cleanup_old_executed_runs(self):
        """Clean up executed runs older than 7 days to prevent state file bloat."""
        try:
            if 'executed_runs' not in self.state_data:
                return
            
            current_time = self._get_current_time()
            executed_runs = self.state_data['executed_runs']
            
            if isinstance(executed_runs, list):
                executed_runs = set(executed_runs)
            
            runs_to_remove = set()
            
            # Check each executed run to see if it's older than 7 days
            for run_key in executed_runs:
                try:
                    # Parse the run key: repo_name:workflow_id:run_id
                    parts = run_key.split(':')
                    if len(parts) >= 3:
                        repo_name = parts[0]
                        workflow_id = int(parts[1])
                        run_id = int(parts[2])
                        
                        # Get the actual run to check its date
                        if repo_name in self.repos:
                            repo = self.repos[repo_name]
                            try:
                                run = repo.get_workflow_run(run_id)
                                if run.updated_at:
                                    age = current_time - run.updated_at
                                    if age.total_seconds() > 604800:  # 7 days = 604800 seconds
                                        runs_to_remove.add(run_key)
                            except Exception:
                                # If we can't fetch the run, it might be deleted, so remove it
                                runs_to_remove.add(run_key)
                except Exception:
                    # If we can't parse the run key, remove it
                    runs_to_remove.add(run_key)
            
            # Remove old runs
            if runs_to_remove:
                self.state_data['executed_runs'] -= runs_to_remove
                self.logger.info(f"Cleaned up {len(runs_to_remove)} old executed run records")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old executed runs: {e}")
    
    def _monitor_workflows(self):
        """Main monitoring loop for workflows across all repositories."""
        try:
            workflows_by_repo = self._get_workflows_to_monitor()
            
            if not workflows_by_repo:
                self.logger.warning("No workflows found to monitor")
                return
            
            total_workflows = sum(len(workflows) for workflows in workflows_by_repo.values())
            current_time = self._get_current_time()
            self.logger.info(f"Starting monitoring check at {self._format_timestamp(current_time)} - "
                           f"{total_workflows} workflows across {len(workflows_by_repo)} repositories")
            
            for repo_name, workflows in workflows_by_repo.items():
                if not self.running:
                    break
                
                self.logger.debug(f"Checking repository: {repo_name}")
                
                for workflow in workflows:
                    if not self.running:
                        break
                    
                    try:
                        new_runs = self._get_new_successful_runs(repo_name, workflow)
                        
                        # Log last 2 workflow runs for this workflow
                        self._log_recent_workflow_runs(repo_name, workflow)
                        
                        for run in new_runs:
                            if not self.running:
                                break
                            
                            self.logger.info(
                                f"New successful workflow run detected: "
                                f"{repo_name} - {workflow.name} - {run.name} (#{run.run_number}) "
                                f"on branch {run.head_branch}"
                            )
                            
                            # Execute commands
                            self._execute_commands(repo_name, workflow, run)
                        
                    except Exception as e:
                        self.logger.error(f"Error monitoring workflow {repo_name}:{workflow.name}: {e}")
            
            # Save state after each monitoring cycle
            self._save_state()
            
            # Log completion time
            end_time = self._get_current_time()
            duration = (end_time - current_time).total_seconds()
            self.logger.info(f"Monitoring check completed at {self._format_timestamp(end_time)} "
                           f"(took {duration:.1f}s)")
            
        except Exception as e:
            self.logger.error(f"Error in monitoring cycle: {e}")
    
    def _monitor_workflows_parallel(self):
        """Parallel monitoring loop for workflows across all repositories."""
        try:
            workflows_by_repo = self._get_workflows_to_monitor()
            
            if not workflows_by_repo:
                self.logger.warning("No workflows found to monitor")
                return
            
            total_workflows = sum(len(workflows) for workflows in workflows_by_repo.values())
            current_time = self._get_current_time()
            self.logger.info(f"🔄 Starting parallel monitoring check at {self._format_timestamp(current_time)} - "
                           f"{total_workflows} workflows across {len(workflows_by_repo)} repositories")
            
            # Process repositories in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all repository checks
                future_to_repo = {
                    executor.submit(self._monitor_single_repository, repo_name, workflows): repo_name 
                    for repo_name, workflows in workflows_by_repo.items()
                }
                
                # Collect results as they complete
                completed_repos = []
                for future in concurrent.futures.as_completed(future_to_repo, timeout=self.repo_timeout * 2):
                    repo_name = future_to_repo[future]
                    try:
                        result = future.result(timeout=self.repo_timeout)
                        completed_repos.append(repo_name)
                        self.logger.debug(f"✅ Repository {repo_name} check completed")
                    except concurrent.futures.TimeoutError:
                        self.logger.error(f"⏱️ Timeout checking repository {repo_name}")
                    except Exception as e:
                        self.logger.error(f"❌ Error checking repository {repo_name}: {e}")
            
            # Thread-safe state saving
            with self._state_lock:
                self._save_state()
            
            # Log completion time
            end_time = self._get_current_time()
            duration = (end_time - current_time).total_seconds()
            self.logger.info(f"🎯 Parallel monitoring check completed at {self._format_timestamp(end_time)} "
                           f"(took {duration:.1f}s) - {len(completed_repos)}/{len(workflows_by_repo)} repos processed")
            
        except Exception as e:
            self.logger.error(f"❌ Error in parallel monitoring cycle: {e}")
    
    def _monitor_single_repository(self, repo_name: str, workflows: List[Any]) -> bool:
        """Monitor workflows for a single repository (thread-safe)."""
        try:
            thread_id = threading.current_thread().ident
            self.logger.debug(f"🧵 Thread {thread_id}: Checking repository {repo_name}")
            
            for workflow in workflows:
                if not self.running:
                    break
                
                try:
                    new_runs = self._get_new_successful_runs(repo_name, workflow)
                    
                    # Log recent runs
                    self._log_recent_workflow_runs(repo_name, workflow)
                    
                    for run in new_runs:
                        if not self.running:
                            break
                        
                        self.logger.info(
                            f"🔔 New successful workflow run detected: "
                            f"{repo_name} - {workflow.name} - {run.name} (#{run.run_number}) "
                            f"on branch {run.head_branch}"
                        )
                        
                        # Execute commands (with execution lock to prevent conflicts)
                        with self._execution_lock:
                            self._execute_commands(repo_name, workflow, run)
                    
                except Exception as e:
                    self.logger.error(f"❌ Error monitoring workflow {repo_name}:{workflow.name}: {e}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Thread error for {repo_name}: {e}")
            return False
    
    def _log_recent_workflow_runs(self, repo_name: str, workflow):
        """Log information about the last 2 workflow runs for debugging."""
        try:
            # Get recent runs (limit to 2 for logging)
            recent_runs = list(workflow.get_runs())[:2]
            
            if not recent_runs:
                self.logger.debug(f"No recent runs found for {repo_name}:{workflow.name}")
                return
            
            self.logger.info(f"Last 2 runs for {repo_name}:{workflow.name}:")
            for i, run in enumerate(recent_runs, 1):
                status_info = f"{run.status}"
                if run.conclusion:
                    status_info += f"/{run.conclusion}"
                
                run_time = "unknown"
                if run.updated_at:
                    run_time = self._format_timestamp(run.updated_at)
                
                age_info = ""
                if run.updated_at:
                    current_time = self._get_current_time()
                    age_seconds = (current_time - run.updated_at).total_seconds()
                    if age_seconds < 3600:  # Less than 1 hour
                        age_info = f" ({age_seconds/60:.0f}m ago)"
                    elif age_seconds < 86400:  # Less than 1 day
                        age_info = f" ({age_seconds/3600:.1f}h ago)"
                    else:  # More than 1 day
                        age_info = f" ({age_seconds/86400:.0f}d ago)"
                
                self.logger.info(f"  {i}. Run #{run.run_number}: {status_info} on {run.head_branch} "
                                f"at {run_time}{age_info}")
                
        except Exception as e:
            self.logger.debug(f"Error logging recent runs for {repo_name}:{workflow.name}: {e}")
    
    def run(self):
        """Main service loop with parallel processing support."""
        try:
            self.logger.info("🚀 Starting GitHub Actions Monitor Service")
            
            # Initialize GitHub client
            self._initialize_github_client()
            
            # Load state
            self.state_data = self._load_state()
            
            # Set running flag
            self.running = True
            
            # Update health check
            self._update_health_check()
            
            # Get polling interval
            poll_interval = self.config.get('monitoring', {}).get('poll_interval', 60)
            health_interval = self.config.get('health', {}).get('update_interval', 300)
            cleanup_interval = 3600  # Clean up old executed runs every hour
            last_cleanup = 0
            
            # Log configuration
            self.logger.info(f"📊 Monitoring {len(self.repos)} repositories")
            self.logger.info(f"🔧 Parallel processing: {'enabled' if self.parallel_enabled else 'disabled'}")
            if self.parallel_enabled:
                self.logger.info(f"👥 Max parallel workers: {self.max_workers}")
                self.logger.info(f"⏱️ Repository timeout: {self.repo_timeout}s")
            self.logger.info(f"🔄 Starting monitoring loop with {poll_interval}s interval")
            
            while self.running:
                try:
                    cycle_start = time.time()
                    
                    # Calculate and log next check time
                    next_check_time = self._get_current_time() + timedelta(seconds=poll_interval)
                    next_check_str = self._format_timestamp(next_check_time)
                    
                    # Monitor workflows with parallel processing
                    if self.parallel_enabled and len(self.repos) > 1:
                        self._monitor_workflows_parallel()
                    else:
                        self._monitor_workflows()
                    
                    # Calculate cycle duration
                    cycle_duration = time.time() - cycle_start
                    self.logger.info(f"⏱️ Monitoring cycle completed in {cycle_duration:.2f} seconds")
                    
                    # Update health check if needed
                    if (time.time() - self.last_health_update) >= health_interval:
                        self._update_health_check()
                    
                    # Clean up old executed runs periodically
                    if (time.time() - last_cleanup) >= cleanup_interval:
                        self._cleanup_old_executed_runs()
                        last_cleanup = time.time()
                    
                    # Log next check time
                    if self.running:  # Only log if we're still running
                        self.logger.info(f"Next monitoring check scheduled for: {next_check_str}")
                    
                    # Sleep until next poll
                    for _ in range(poll_interval):
                        if not self.running:
                            break
                        time.sleep(1)
                    
                except KeyboardInterrupt:
                    self.logger.info("Received keyboard interrupt")
                    break
                except Exception as e:
                    self.logger.error(f"Error in main loop: {e}")
                    time.sleep(poll_interval)
            
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            sys.exit(1)
        finally:
            self.logger.info("GitHub Actions Monitor Service stopped")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='GitHub Actions Monitor Service')
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Configuration file path (default: config.yaml)'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Override log level from config'
    )
    parser.add_argument(
        '--local-mode',
        action='store_true',
        help='Run in local mode (use local directories for logs/state instead of system paths)'
    )
    parser.add_argument(
        '--server-mode',
        action='store_true',
        help='Run in server mode (use system paths - this is the default)'
    )
    
    args = parser.parse_args()
    
    # Determine mode (local_mode takes precedence, server_mode is default)
    local_mode = args.local_mode
    if args.server_mode and args.local_mode:
        print("Warning: Both --local-mode and --server-mode specified. Using --local-mode.")
    
    # Show mode information
    mode_str = "local" if local_mode else "server"
    print(f"GitHub Actions Monitor starting in {mode_str} mode")
    
    if local_mode:
        print("Local mode: Using current directory for logs and state files")
    else:
        print("Server mode: Using system paths (/var/log, /var/lib, etc.)")
    
    # Create and run monitor
    monitor = GitHubActionsMonitor(config_path=args.config, local_mode=local_mode)
    
    # Override log level if specified
    if args.log_level:
        monitor.logger.setLevel(getattr(logging, args.log_level))
    
    monitor.run()


if __name__ == "__main__":
    main()
