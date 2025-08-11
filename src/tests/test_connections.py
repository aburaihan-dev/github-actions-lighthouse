#!/usr/bin/env python3
"""
Configuration and connection tests for GitHub Actions Monitor
"""

from pathlib import Path
from .test_utils import *


def test_config_loading():
    """Test configuration loading."""
    print_subheader("Testing Configuration Loading")
    
    config_file = get_config_path("config.yaml")
    if not config_file.exists():
        print(f"❌ Config file not found: {config_file}")
        return TestResult("Config Loading", False, "Config file not found")
    
    try:
        monitor = create_monitor_instance(str(config_file), local_mode=True)
        if not monitor:
            return TestResult("Config Loading", False, "Failed to create monitor instance")
        
        print("✅ Configuration loaded successfully")
        
        # Check required fields
        required_fields = ['repositories', 'github.token']
        issues = []
        
        for field in required_fields:
            keys = field.split('.')
            value = monitor.config
            for key in keys:
                value = value.get(key, {})
            
            if not value or (isinstance(value, str) and value.startswith("${")):
                print(f"⚠️  Field not configured: {field}")
                issues.append(field)
            else:
                print(f"✅ Field configured: {field}")
                if field == 'repositories':
                    print(f"   Repositories: {', '.join(value)}")
        
        success = len(issues) == 0
        message = "All fields configured" if success else f"Missing fields: {', '.join(issues)}"
        
        return TestResult("Config Loading", success, message, {
            'repositories': monitor.config.get('repositories', []),
            'missing_fields': issues
        })
        
    except Exception as e:
        return TestResult("Config Loading", False, f"Error: {e}")


def test_github_connection():
    """Test GitHub API connection."""
    print_subheader("Testing GitHub Connection")
    
    try:
        monitor = create_monitor_instance(str(get_config_path()), local_mode=True)
        if not monitor:
            return TestResult("GitHub Connection", False, "Failed to create monitor instance")
        
        monitor._initialize_github_client()
        
        repositories = monitor.config.get('repositories', [])
        connected_repos = len(monitor.repos)
        
        print(f"✅ Connected to {connected_repos} repositories")
        
        repo_details = {}
        for repo_name, repo in monitor.repos.items():
            print(f"   - {repo_name}")
            
            try:
                workflows = list(repo.get_workflows())
                workflow_count = len(workflows)
                print(f"     Found {workflow_count} workflows")
                repo_details[repo_name] = {
                    'workflows': workflow_count,
                    'connected': True
                }
            except Exception as e:
                print(f"     ❌ Error getting workflows: {e}")
                repo_details[repo_name] = {
                    'workflows': 0,
                    'connected': False,
                    'error': str(e)
                }
        
        success = connected_repos > 0
        message = f"Connected to {connected_repos}/{len(repositories)} repositories"
        
        return TestResult("GitHub Connection", success, message, {
            'total_repos': len(repositories),
            'connected_repos': connected_repos,
            'repo_details': repo_details
        })
        
    except Exception as e:
        return TestResult("GitHub Connection", False, f"Connection failed: {e}")


def test_workflow_monitoring():
    """Test workflow monitoring functionality."""
    print_subheader("Testing Workflow Monitoring")
    
    try:
        monitor = create_monitor_instance(str(get_config_path()), local_mode=True)
        if not monitor:
            return TestResult("Workflow Monitoring", False, "Failed to create monitor instance")
        
        monitor._initialize_github_client()
        monitor.state_data = monitor._load_state()
        
        workflows_by_repo = monitor._get_workflows_to_monitor()
        total_workflows = sum(len(workflows) for workflows in workflows_by_repo.values())
        
        print(f"✅ Monitoring {total_workflows} workflows across {len(workflows_by_repo)} repositories")
        
        total_runs = 0
        workflow_details = {}
        
        for repo_name, workflows in workflows_by_repo.items():
            print(f"   Repository: {repo_name}")
            workflow_details[repo_name] = []
            
            # Test first 3 workflows for each repo
            for workflow in list(workflows)[:3]:
                try:
                    runs = list(workflow.get_runs(status='completed'))[:5]  # Last 5 runs
                    total_runs += len(runs)
                    
                    workflow_info = {
                        'name': workflow.name,
                        'id': workflow.id,
                        'runs': len(runs),
                        'recent_runs': []
                    }
                    
                    print(f"     - {workflow.name}: {len(runs)} recent completed runs")
                    
                    for run in runs[:2]:  # Show details for last 2 runs
                        run_info = {
                            'number': run.run_number,
                            'conclusion': run.conclusion,
                            'branch': run.head_branch,
                            'updated_at': run.updated_at.isoformat() if run.updated_at else None
                        }
                        workflow_info['recent_runs'].append(run_info)
                        print(f"       • Run #{run.run_number}: {run.conclusion} on {run.head_branch}")
                    
                    workflow_details[repo_name].append(workflow_info)
                    
                except Exception as e:
                    print(f"     - {workflow.name}: Error getting runs - {e}")
                    workflow_details[repo_name].append({
                        'name': workflow.name,
                        'error': str(e)
                    })
        
        print(f"✅ Found {total_runs} total completed runs")
        
        success = total_workflows > 0
        message = f"Monitoring {total_workflows} workflows, found {total_runs} runs"
        
        return TestResult("Workflow Monitoring", success, message, {
            'total_workflows': total_workflows,
            'total_runs': total_runs,
            'workflow_details': workflow_details
        })
        
    except Exception as e:
        return TestResult("Workflow Monitoring", False, f"Monitoring test failed: {e}")


def test_command_configuration():
    """Test command execution configuration."""
    print_subheader("Testing Command Configuration")
    
    try:
        monitor = create_monitor_instance(str(get_config_path()), local_mode=True)
        if not monitor:
            return TestResult("Command Config", False, "Failed to create monitor instance")
        
        commands_config = monitor.config.get('commands', {})
        
        # Check for new command structure
        if 'definitions' in commands_config and 'execution_map' in commands_config:
            print("✅ New command structure detected")
            return test_new_command_structure(monitor, commands_config)
        else:
            print("⚠️  Legacy command structure detected")
            return test_legacy_command_structure(monitor, commands_config)
        
    except Exception as e:
        return TestResult("Command Config", False, f"Command test failed: {e}")


def test_new_command_structure(monitor, commands_config):
    """Test the new named command structure."""
    definitions = commands_config.get('definitions', {})
    execution_map = commands_config.get('execution_map', {})
    
    if not definitions:
        return TestResult("Command Config", False, "No command definitions found")
    
    print(f"✅ Found {len(definitions)} command definitions:")
    
    definition_details = []
    issues = []
    
    # Test command definitions
    for cmd_name, cmd_config in definitions.items():
        description = cmd_config.get('description', 'No description')
        command = cmd_config.get('command', '')
        working_dir = cmd_config.get('working_directory', '/tmp')
        
        cmd_info = {
            'name': cmd_name,
            'description': description,
            'command': command[:100] + '...' if len(command) > 100 else command,
            'working_directory': working_dir,
            'issues': []
        }
        
        print(f"   • {cmd_name}: {description}")
        print(f"     Command: {command[:60]}{'...' if len(command) > 60 else ''}")
        print(f"     Working dir: {working_dir}")
        
        # Validate command
        if not command:
            issue = f"Command '{cmd_name}': Empty command"
            print(f"     ⚠️  {issue}")
            issues.append(issue)
            cmd_info['issues'].append(issue)
        
        # Check if working directory exists (skip for /tmp and variables)
        if working_dir and working_dir not in ['/tmp', 'current'] and not working_dir.startswith('$'):
            if Path(working_dir).exists():
                print(f"     ✅ Working directory exists")
            else:
                issue = f"Command '{cmd_name}': Working directory not found: {working_dir}"
                print(f"     ⚠️  {issue}")
                issues.append(issue)
                cmd_info['issues'].append(issue)
        
        definition_details.append(cmd_info)
    
    # Test execution mapping
    print(f"\n✅ Found execution mappings for {len(execution_map)} repository patterns:")
    
    execution_details = {}
    for repo_pattern, branch_map in execution_map.items():
        print(f"   Repository: {repo_pattern}")
        execution_details[repo_pattern] = {}
        
        for branch_pattern, command_list in branch_map.items():
            print(f"     Branch: {branch_pattern} → {len(command_list)} commands")
            execution_details[repo_pattern][branch_pattern] = command_list
            
            # Validate that referenced commands exist
            for cmd_name in command_list:
                if cmd_name not in definitions:
                    issue = f"Repository '{repo_pattern}', branch '{branch_pattern}': Unknown command '{cmd_name}'"
                    print(f"       ⚠️  {issue}")
                    issues.append(issue)
                else:
                    print(f"       ✅ {cmd_name}")
    
    success = len(issues) == 0
    message = f"{len(definitions)} commands defined, {len(execution_map)} repo patterns mapped" + (f", {len(issues)} issues" if issues else "")
    
    return TestResult("Command Config", success, message, {
        'command_count': len(definitions),
        'execution_patterns': len(execution_map),
        'issues': issues,
        'definition_details': definition_details,
        'execution_details': execution_details
    })


def test_legacy_command_structure(monitor, commands_config):
    """Test the legacy command structure."""
    commands = commands_config.get('on_success', [])
    
    if not commands:
        return TestResult("Command Config", True, "No legacy commands configured (valid)", {
            'command_count': 0
        })
    
    print(f"✅ Found {len(commands)} legacy commands:")
    
    command_details = []
    issues = []
    
    for i, cmd in enumerate(commands, 1):
        description = cmd.get('description', 'Unnamed command')
        command = cmd.get('command', '')
        working_dir = cmd.get('working_directory', 'current')
        
        cmd_info = {
            'index': i,
            'description': description,
            'command': command,
            'working_directory': working_dir,
            'issues': []
        }
        
        print(f"   {i}. {description}")
        print(f"      Command: {command}")
        print(f"      Working dir: {working_dir}")
        
        # Validate command
        if not command:
            issue = f"Command {i}: Empty command"
            print(f"      ⚠️  {issue}")
            issues.append(issue)
            cmd_info['issues'].append(issue)
        
        # Check if working directory exists
        if working_dir and working_dir != 'current':
            if Path(working_dir).exists():
                print(f"      ✅ Working directory exists")
            else:
                issue = f"Command {i}: Working directory not found"
                print(f"      ⚠️  {issue}")
                issues.append(issue)
                cmd_info['issues'].append(issue)
        
        command_details.append(cmd_info)
    
    success = len(issues) == 0
    message = f"{len(commands)} legacy commands configured" + (f", {len(issues)} issues" if issues else "")
    
    return TestResult("Command Config", success, message, {
        'command_count': len(commands),
        'issues': issues,
        'command_details': command_details
    })


def test_command_execution():
    """Test command execution functionality with safe test commands."""
    print_subheader("Testing Command Execution")
    
    try:
        import subprocess
        import os
        
        monitor = create_monitor_instance(str(get_config_path()), local_mode=True)
        if not monitor:
            return TestResult("Command Execution", False, "Failed to create monitor instance")
        
        # Test safe commands that don't modify the system
        safe_test_commands = [
            {
                'name': 'test_echo',
                'description': 'Test echo command',
                'command': 'echo "Test command execution successful"',
                'working_directory': '/tmp'
            },
            {
                'name': 'test_date',
                'description': 'Test date command',
                'command': 'date',
                'working_directory': '/tmp'
            },
            {
                'name': 'test_env',
                'description': 'Test environment variables',
                'command': 'echo "Repository: $REPO_NAME, Branch: $BRANCH_NAME"',
                'working_directory': '/tmp'
            }
        ]
        
        execution_results = []
        successful_executions = 0
        
        print("Testing safe command execution...")
        
        for test_cmd in safe_test_commands:
            print(f"\n   Testing: {test_cmd['name']}")
            print(f"   Command: {test_cmd['command']}")
            
            try:
                # Set up test environment variables
                test_env = os.environ.copy()
                test_env.update({
                    'REPO_NAME': 'test/repository',
                    'BRANCH_NAME': 'test-branch',
                    'WORKFLOW_NAME': 'test-workflow',
                    'RUN_NUMBER': '123',
                    'COMMIT_MESSAGE': 'Test commit message'
                })
                
                # Execute the command
                result = subprocess.run(
                    test_cmd['command'],
                    shell=True,
                    cwd=test_cmd['working_directory'],
                    env=test_env,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                cmd_result = {
                    'name': test_cmd['name'],
                    'return_code': result.returncode,
                    'stdout': result.stdout.strip(),
                    'stderr': result.stderr.strip(),
                    'success': result.returncode == 0
                }
                
                if result.returncode == 0:
                    print(f"   ✅ Success: {result.stdout.strip()}")
                    successful_executions += 1
                else:
                    print(f"   ❌ Failed (exit code {result.returncode}): {result.stderr.strip()}")
                
                execution_results.append(cmd_result)
                
            except subprocess.TimeoutExpired:
                print(f"   ⚠️  Command timed out")
                execution_results.append({
                    'name': test_cmd['name'],
                    'error': 'timeout',
                    'success': False
                })
            except Exception as e:
                print(f"   ❌ Error executing command: {e}")
                execution_results.append({
                    'name': test_cmd['name'],
                    'error': str(e),
                    'success': False
                })
        
        success = successful_executions > 0
        message = f"Command execution test: {successful_executions}/{len(safe_test_commands)} commands succeeded"
        
        return TestResult("Command Execution", success, message, {
            'total_commands': len(safe_test_commands),
            'successful_executions': successful_executions,
            'execution_results': execution_results
        })
        
    except Exception as e:
        return TestResult("Command Execution", False, f"Command execution test failed: {e}")


def run_connection_tests():
    """Run all connection and configuration tests."""
    print_header("GitHub Actions Monitor - Connection & Configuration Tests")
    
    # Setup
    load_env()
    setup_python_path()
    create_test_directories()
    
    # Show environment info
    deps = show_environment_info()
    
    # Check if we can proceed
    if not deps.get('github', False):
        print("\n❌ PyGithub not available - cannot run connection tests")
        return False
    
    if not check_github_token():
        print("\n❌ GitHub token not available - cannot run connection tests")
        return False
    
    # Run tests
    tests = [
        (test_config_loading, "Configuration Loading"),
        (test_github_connection, "GitHub Connection"),
        (test_workflow_monitoring, "Workflow Monitoring"),
        (test_command_configuration, "Command Configuration"),
        (test_command_execution, "Command Execution")
    ]
    
    results = []
    test_names = []
    
    for test_func, test_name in tests:
        result = run_test_safely(test_func, test_name)
        results.append(bool(result))
        test_names.append(test_name)
    
    # Summary
    success = print_summary(results, test_names)
    
    if success:
        print("\nYour GitHub Actions Monitor is ready to run.")
        print("Use 'sudo ./install.sh' to install as a systemd service.")
    else:
        print("\nPlease fix the issues above before running the service.")
    
    return success


if __name__ == "__main__":
    run_connection_tests()
