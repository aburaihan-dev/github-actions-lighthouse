#!/usr/bin/env python3
"""
Test script to verify enhanced command execution logging.
This simulates what happens when the monitor executes commands.
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, '.')

from github_actions_monitor import GitHubActionsMonitor

def create_test_config():
    """Create a test configuration with various command scenarios."""
    config = {
        'github': {
            'token': 'fake-token-for-testing'
        },
        'repositories': ['test/repo'],
        'monitoring': {
            'poll_interval': 60,
            'workflows': [],
            'branches': []
        },
        'commands': {
            'definitions': {
                'test_echo': {
                    'description': 'Simple echo command',
                    'command': 'echo "Hello from test command!"',
                    'working_directory': '/tmp'
                },
                'test_ls': {
                    'description': 'List current directory',
                    'command': 'ls -la',
                    'working_directory': '.'
                },
                'test_permission_error': {
                    'description': 'Command that might fail due to permissions',
                    'command': 'touch /root/test_file.txt',
                    'working_directory': '/tmp'
                },
                'test_nonexistent_dir': {
                    'description': 'Command with nonexistent working directory',
                    'command': 'echo "This should fail"',
                    'working_directory': '/nonexistent/directory'
                },
                'test_invalid_command': {
                    'description': 'Command that does not exist',
                    'command': 'nonexistent_command_12345',
                    'working_directory': '/tmp'
                }
            },
            'execution_map': {
                'test/repo': {
                    'main': [
                        'test_echo',
                        'test_ls',
                        'test_permission_error',
                        'test_nonexistent_dir',
                        'test_invalid_command'
                    ]
                }
            }
        },
        'logging': {
            'level': 'DEBUG',
            'console': {'enabled': True},
            'commands': {
                'log_level': 'DEBUG',
                'detailed_output': True,
                'log_environment': True,
                'log_permissions': True
            }
        },
        'state': {
            'state_file': './test_state.json'
        },
        'health': {
            'enabled': False
        }
    }
    return config

def create_mock_workflow_run():
    """Create a mock workflow run object for testing."""
    class MockWorkflowRun:
        def __init__(self):
            self.id = 12345
            self.run_number = 42
            self.name = "Test Workflow"
            self.head_branch = "main"
            self.head_sha = "abc123def456"
            self.display_title = "Test commit message"
    
    class MockWorkflow:
        def __init__(self):
            self.id = 67890
            self.name = "test-workflow"
    
    return MockWorkflow(), MockWorkflowRun()

def test_command_execution():
    """Test the enhanced command execution logging."""
    print("Testing Enhanced Command Execution Logging")
    print("=" * 50)
    
    # Create test config
    config = create_test_config()
    
    # Write config to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        import yaml
        yaml.dump(config, f)
        config_path = f.name
    
    try:
        # Create monitor instance in local mode
        monitor = GitHubActionsMonitor(config_path=config_path, local_mode=True)
        
        # Create mock workflow and run
        workflow, workflow_run = create_mock_workflow_run()
        
        print(f"\nTesting command execution for repo: test/repo")
        print(f"Branch: {workflow_run.head_branch}")
        print(f"Run: {workflow_run.name} (#{workflow_run.run_number})")
        print("-" * 50)
        
        # Test the command execution
        monitor._execute_commands("test/repo", workflow, workflow_run)
        
        print("\n" + "=" * 50)
        print("Command execution test completed!")
        print("Check the logs above to see the enhanced logging output.")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up temporary files
        try:
            os.unlink(config_path)
            if os.path.exists('./test_state.json'):
                os.unlink('./test_state.json')
        except Exception:
            pass

if __name__ == "__main__":
    test_command_execution()
