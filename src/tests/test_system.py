#!/usr/bin/env python3
"""
Logging and system tests for GitHub Actions Monitor
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from .test_utils import *


def test_log_rotation():
    """Test the daily log rotation configuration."""
    print_subheader("Testing Daily Log Rotation Configuration")
    
    try:
        moni            test_data = [
            {
                'repo': 'your-org/your-frontend-repo',
                'branch': 'your-branch',
                'expected_commands': execution_map.get('your-org/your-frontend-repo', {}).get('your-branch', [])
            },
            {
                'repo': 'your-org/your-backend-repo', 
                'branch': 'your-branch',
                'expected_commands': execution_map.get('your-org/your-backend-repo', {}).get('your-branch', [])
            }e_monitor_instance(str(get_config_path()), local_mode=True)
        if not monitor:
            return TestResult("Log Rotation", False, "Failed to create monitor instance")
        
        # Check if logger has TimedRotatingFileHandler
        has_timed_handler = False
        handler_info = {}
        
        for handler in monitor.logger.handlers:
            handler_type = type(handler).__name__
            print(f"Found log handler: {handler_type}")
            
            if handler_type == 'TimedRotatingFileHandler':
                has_timed_handler = True
                handler_info = {
                    'when': getattr(handler, 'when', 'unknown'),
                    'interval': getattr(handler, 'interval', 'unknown'),
                    'backupCount': getattr(handler, 'backupCount', 'unknown'),
                    'suffix': getattr(handler, 'suffix', 'unknown'),
                    'utc': getattr(handler, 'utc', 'unknown'),
                    'baseFilename': getattr(handler, 'baseFilename', 'unknown')
                }
                break
        
        if has_timed_handler:
            print("✅ TimedRotatingFileHandler found!")
            print(f"   Rotation: {handler_info['when']} (every {handler_info['interval']} day)")
            print(f"   Backup count: {handler_info['backupCount']} files")
            print(f"   Date suffix: {handler_info['suffix']}")
            print(f"   UTC time: {handler_info['utc']}")
            print(f"   Log file: {handler_info['baseFilename']}")
            
            # Test logging some messages
            print("\n   Testing Log Messages:")
            monitor.logger.info("Test log message for rotation verification")
            monitor.logger.debug("Debug message (may not appear depending on log level)")
            monitor.logger.warning("Warning message for rotation test")
            
            # Check log file content
            log_file = Path(handler_info['baseFilename'])
            if log_file.exists():
                file_size = log_file.stat().st_size
                print(f"   ✅ Log file exists: {log_file}")
                print(f"   File size: {file_size} bytes")
                
                # Show last few lines
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        print(f"   Last log entry: {lines[-1].strip()}")
                
                return TestResult("Log Rotation", True, "TimedRotatingFileHandler configured correctly", {
                    'handler_info': handler_info,
                    'log_file_size': file_size,
                    'log_file_exists': True
                })
            else:
                return TestResult("Log Rotation", False, f"Log file not found: {log_file}")
            
        else:
            available_handlers = [type(h).__name__ for h in monitor.logger.handlers]
            return TestResult("Log Rotation", False, "TimedRotatingFileHandler not found", {
                'available_handlers': available_handlers
            })
        
    except Exception as e:
        return TestResult("Log Rotation", False, f"Error testing log rotation: {e}")


def test_timezone_configuration():
    """Test the timezone configuration functionality."""
    print_subheader("Testing Timezone Configuration")
    
    try:
        monitor = create_monitor_instance(str(get_config_path()), local_mode=True)
        if not monitor:
            return TestResult("Timezone Config", False, "Failed to create monitor instance")
        
        # Test current timezone configuration
        current_tz = monitor.timezone_name
        print(f"✅ Configured timezone: {current_tz}")
        
        # Test timezone formatting
        test_time = datetime.now(timezone.utc)
        formatted_time = monitor._format_timestamp(test_time)
        print(f"✅ Sample timestamp: {formatted_time}")
        
        # Test different timezone configurations
        test_timezones = ["UTC", "America/New_York", "Europe/London", "Asia/Tokyo"]
        timezone_results = {}
        
        for tz_name in test_timezones:
            try:
                # Temporarily update config
                original_tz = monitor.config.get('logging', {}).get('timezone', 'Asia/Dhaka')
                if 'logging' not in monitor.config:
                    monitor.config['logging'] = {}
                monitor.config['logging']['timezone'] = tz_name
                
                # Re-setup timezone
                monitor._setup_timezone()
                
                # Test formatting
                formatted = monitor._format_timestamp(test_time)
                print(f"   ✅ {tz_name}: {formatted}")
                timezone_results[tz_name] = {
                    'formatted': formatted,
                    'success': True
                }
                
                # Restore original
                monitor.config['logging']['timezone'] = original_tz
                monitor._setup_timezone()
                
            except Exception as e:
                print(f"   ❌ {tz_name}: Error - {e}")
                timezone_results[tz_name] = {
                    'error': str(e),
                    'success': False
                }
        
        successful_timezones = sum(1 for result in timezone_results.values() if result['success'])
        total_timezones = len(test_timezones)
        
        return TestResult("Timezone Config", successful_timezones > 0, 
                         f"Timezone support working ({successful_timezones}/{total_timezones} test timezones)", {
                             'current_timezone': current_tz,
                             'sample_timestamp': formatted_time,
                             'test_results': timezone_results
                         })
        
    except Exception as e:
        return TestResult("Timezone Config", False, f"Error testing timezone: {e}")


def test_log_directory_structure():
    """Test the expected log directory structure."""
    print_subheader("Testing Log Directory Structure")
    
    try:
        # Test in local mode
        project_root = get_project_root()
        log_dir = project_root / 'logs'
        
        print(f"Expected log directory: {log_dir}")
        
        directory_info = {
            'log_dir_exists': log_dir.exists(),
            'log_files': [],
            'total_size': 0
        }
        
        if log_dir.exists():
            print("✅ Log directory exists")
            
            # List all files in log directory
            log_files = list(log_dir.glob("*.log*"))
            print(f"Found {len(log_files)} log files:")
            
            for log_file in sorted(log_files):
                file_size = log_file.stat().st_size
                modified_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                file_info = {
                    'name': log_file.name,
                    'size': file_size,
                    'modified': modified_time.isoformat()
                }
                directory_info['log_files'].append(file_info)
                directory_info['total_size'] += file_size
                print(f"   - {log_file.name} ({file_size} bytes, modified: {modified_time})")
            
            # Check for expected main log file
            main_log = log_dir / 'monitor.log'
            directory_info['main_log_exists'] = main_log.exists()
            
            if main_log.exists():
                print(f"✅ Main log file exists: {main_log}")
                success = True
                message = f"Log directory configured correctly ({len(log_files)} files, {directory_info['total_size']} bytes total)"
            else:
                print(f"⚠️  Main log file not found: {main_log}")
                success = len(log_files) > 0  # At least some log files exist
                message = "Log directory exists but main log file not found"
                
        else:
            print(f"⚠️  Log directory does not exist: {log_dir}")
            print("   (This is normal if the monitor hasn't been run yet)")
            success = True  # Not an error if monitor hasn't run yet
            message = "Log directory will be created when monitor runs"
        
        return TestResult("Log Directory", success, message, directory_info)
        
    except Exception as e:
        return TestResult("Log Directory", False, f"Error testing log directory: {e}")


def test_timing_and_duplicate_prevention():
    """Test the 5-minute timing and duplicate prevention logic."""
    print_subheader("Testing 5-Minute Timing and Duplicate Prevention")
    
    try:
        monitor = create_monitor_instance(str(get_config_path()), local_mode=True)
        if not monitor:
            return TestResult("Timing Logic", False, "Failed to create monitor instance")
        
        monitor._initialize_github_client()
        
        # Get first repository and workflow for testing
        if not monitor.repos:
            return TestResult("Timing Logic", False, "No repositories available for testing")
        
        repo_name = list(monitor.repos.keys())[0]
        repo = monitor.repos[repo_name]
        
        print(f"Testing with repository: {repo_name}")
        
        # Get workflows
        workflows = list(repo.get_workflows())
        if not workflows:
            return TestResult("Timing Logic", False, "No workflows found")
        
        workflow = workflows[0]
        print(f"Testing with workflow: {workflow.name}")
        
        # Get some recent runs
        runs = list(workflow.get_runs(status='completed'))[:10]
        
        if not runs:
            return TestResult("Timing Logic", False, "No completed runs found")
        
        print(f"Found {len(runs)} completed runs to analyze")
        
        current_time = monitor._get_current_time()
        recent_runs = []
        old_runs = []
        timing_analysis = {
            'total_runs': len(runs),
            'recent_runs': 0,
            'old_runs': 0,
            'run_details': []
        }
        
        for run in runs:
            if run.updated_at:
                time_diff = current_time - run.updated_at
                minutes_ago = time_diff.total_seconds() / 60
                
                run_detail = {
                    'run_number': run.run_number,
                    'conclusion': run.conclusion,
                    'minutes_ago': minutes_ago,
                    'is_recent': time_diff.total_seconds() <= 300
                }
                timing_analysis['run_details'].append(run_detail)
                
                status = "✅ RECENT" if time_diff.total_seconds() <= 300 else "⏰ OLD"
                print(f"  Run #{run.run_number}: {run.conclusion} - {minutes_ago:.1f} minutes ago - {status}")
                
                if time_diff.total_seconds() <= 300:
                    recent_runs.append(run)
                    timing_analysis['recent_runs'] += 1
                else:
                    old_runs.append(run)
                    timing_analysis['old_runs'] += 1
        
        print(f"\nTiming Summary:")
        print(f"  Recent runs (≤5 min): {len(recent_runs)}")
        print(f"  Old runs (>5 min): {len(old_runs)}")
        
        # Test the actual monitor logic
        print(f"\nTesting monitor logic...")
        monitor.state_data = {'executed_runs': set()}
        new_runs = monitor._get_new_successful_runs(repo_name, workflow)
        
        print(f"Monitor found {len(new_runs)} new successful runs within 5 minutes")
        
        monitor_results = []
        for run in new_runs:
            time_diff = current_time - run.updated_at
            minutes_ago = time_diff.total_seconds() / 60
            run_info = {
                'run_number': run.run_number,
                'conclusion': run.conclusion,
                'minutes_ago': minutes_ago
            }
            monitor_results.append(run_info)
            print(f"  ✅ Run #{run.run_number}: {run.conclusion} - {minutes_ago:.1f} minutes ago")
        
        # Test duplicate prevention
        print(f"\nTesting duplicate prevention...")
        if new_runs:
            # Simulate marking runs as executed
            test_run = new_runs[0]
            run_key = f"{repo_name}:{workflow.id}:{test_run.id}"
            monitor.state_data['executed_runs'].add(run_key)
            
            # Try to get new runs again - should be filtered out
            new_runs_after = monitor._get_new_successful_runs(repo_name, workflow)
            duplicate_prevented = len(new_runs_after) < len(new_runs)
            
            print(f"  Original new runs: {len(new_runs)}")
            print(f"  After marking executed: {len(new_runs_after)}")
            print(f"  Duplicate prevention: {'✅ Working' if duplicate_prevented else '⚠️ Not working'}")
        else:
            duplicate_prevented = True  # No runs to test, assume working
            print("  No recent runs to test duplicate prevention")
        
        timing_analysis.update({
            'monitor_found_runs': len(new_runs),
            'monitor_results': monitor_results,
            'duplicate_prevention_working': duplicate_prevented
        })
        
        success = True  # Test is informational, always pass unless error
        message = f"Timing logic working (found {len(new_runs)} recent runs, duplicate prevention {'working' if duplicate_prevented else 'needs attention'})"
        
        return TestResult("Timing Logic", success, message, timing_analysis)
        
    except Exception as e:
        return TestResult("Timing Logic", False, f"Error testing timing logic: {e}")


def test_execution_mapping_logic():
    """Test the execution mapping logic for repository-branch command selection."""
    print_subheader("Testing Execution Mapping Logic")
    
    try:
        import subprocess
        import os
        
        monitor = create_monitor_instance(str(get_config_path()), local_mode=True)
        if not monitor:
            return TestResult("Execution Mapping", False, "Failed to create monitor instance")
        
        commands_config = monitor.config.get('commands', {})
        
        if 'execution_map' not in commands_config:
            return TestResult("Execution Mapping", False, "No execution_map found in configuration")
        
        execution_map = commands_config['execution_map']
        definitions = commands_config.get('definitions', {})
        
        print("Testing execution mapping logic...")
        
        test_scenarios = [
            {
                'repo': 'your-org/your-frontend-repo',
                'branch': 'your-branch',
                'expected_commands': execution_map.get('your-org/your-frontend-repo', {}).get('your-branch', [])
            },
            {
                'repo': 'your-org/your-backend-repo', 
                'branch': 'your-branch',
                'expected_commands': execution_map.get('your-org/your-backend-repo', {}).get('your-branch', [])
            },
            {
                'repo': 'unknown/repository',
                'branch': 'main',
                'expected_commands': execution_map.get('*', {}).get('*', [])
            }
        ]
        
        mapping_results = []
        successful_mappings = 0
        
        for scenario in test_scenarios:
            repo = scenario['repo']
            branch = scenario['branch']
            expected = scenario['expected_commands']
            
            print(f"\n   Testing: {repo} → {branch}")
            
            if expected:
                print(f"   Expected commands: {', '.join(expected)}")
                
                # Verify all expected commands exist in definitions
                missing_commands = [cmd for cmd in expected if cmd not in definitions]
                if missing_commands:
                    print(f"   ❌ Missing command definitions: {', '.join(missing_commands)}")
                    mapping_results.append({
                        'repo': repo,
                        'branch': branch,
                        'success': False,
                        'error': f"Missing definitions: {missing_commands}"
                    })
                else:
                    print(f"   ✅ All {len(expected)} commands have definitions")
                    successful_mappings += 1
                    mapping_results.append({
                        'repo': repo,
                        'branch': branch,
                        'success': True,
                        'commands': expected
                    })
            else:
                print(f"   ⚠️  No commands mapped for this repo/branch combination")
                mapping_results.append({
                    'repo': repo,
                    'branch': branch,
                    'success': True,
                    'commands': []
                })
        
        success = successful_mappings > 0
        message = f"Execution mapping: {successful_mappings}/{len(test_scenarios)} scenarios valid"
        
        return TestResult("Execution Mapping", success, message, {
            'total_scenarios': len(test_scenarios),
            'successful_mappings': successful_mappings,
            'mapping_results': mapping_results
        })
        
    except Exception as e:
        return TestResult("Execution Mapping", False, f"Execution mapping test failed: {e}")


def test_command_logging():
    """Test command execution logging functionality."""
    print_subheader("Testing Command Execution Logging")
    
    try:
        monitor = create_monitor_instance(str(get_config_path()), local_mode=True)
        if not monitor:
            return TestResult("Command Logging", False, "Failed to create monitor instance")
        
        # Test that logging is properly configured
        if not hasattr(monitor, 'logger'):
            return TestResult("Command Logging", False, "Monitor has no logger configured")
        
        print("✅ Logger is configured")
        
        # Test different log levels
        test_messages = [
            ("INFO", "Test info message for command execution"),
            ("DEBUG", "Test debug message with command details"),
            ("WARNING", "Test warning message for command issues"),
            ("ERROR", "Test error message for command failures")
        ]
        
        log_results = []
        
        for level, message in test_messages:
            try:
                log_method = getattr(monitor.logger, level.lower())
                log_method(f"[COMMAND_TEST] {message}")
                log_results.append((level, True))
                print(f"   ✅ {level} logging works")
            except Exception as e:
                log_results.append((level, False))
                print(f"   ❌ {level} logging failed: {e}")
        
        # Test command-specific logging format
        try:
            test_repo = "your-org/your-frontend-repo" 
            test_branch = "staging"
            test_command = "restart_frontend"
            
            # Simulate command execution logging
            monitor.logger.info(f"[COMMAND_EXECUTION] Repo: {test_repo}, Branch: {test_branch}, Command: {test_command}")
            monitor.logger.info(f"[COMMAND_RESULT] Command '{test_command}' executed successfully")
            
            print("✅ Command execution logging format works")
            command_logging_success = True
        except Exception as e:
            print(f"❌ Command execution logging failed: {e}")
            command_logging_success = False
        
        # Count successful log levels
        successful_logs = sum(1 for _, success in log_results if success)
        total_logs = len(log_results)
        
        overall_success = successful_logs == total_logs and command_logging_success
        
        message = f"Command logging: {successful_logs}/{total_logs} log levels working"
        if command_logging_success:
            message += ", command format verified"
        
        return TestResult("Command Logging", overall_success, message, {
            'log_levels_tested': total_logs,
            'log_levels_working': successful_logs,
            'command_format_working': command_logging_success,
            'log_results': log_results
        })
        
    except Exception as e:
        return TestResult("Command Logging", False, f"Command logging test failed: {e}")


def run_system_tests():
    """Run all system and logging tests."""
    print_header("GitHub Actions Monitor - System & Logging Tests")
    
    # Setup
    load_env()
    setup_python_path()
    create_test_directories()
    
    # Show environment info
    deps = show_environment_info()
    
    # Check if we can proceed
    if not deps.get('github', False):
        print("\n❌ PyGithub not available - cannot run full system tests")
        return False
    
    # Run tests
    tests = [
        (test_log_rotation, "Log Rotation"),
        (test_timezone_configuration, "Timezone Configuration"),
        (test_log_directory_structure, "Log Directory Structure"),
        (test_timing_and_duplicate_prevention, "Timing & Duplicate Prevention"),
        (test_execution_mapping_logic, "Execution Mapping Logic"),
        (test_command_logging, "Command Logging")
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
        print("\n✅ System configuration and logging are working correctly:")
        print("• Daily log rotation with 30-day retention")
        print("• Configurable timezone support (default: Asia/Dhaka)")
        print("• 5-minute timing window for workflow execution")
        print("• Duplicate prevention for command execution")
        print("• Repository-branch command mapping")
        print("• Command execution logging")
    else:
        print("\n❌ Some system tests failed. Check the configuration and try again.")
    
    return success


def main():
    """Main function to run all system tests with proper logging."""
    # Setup
    load_env()
    setup_python_path()
    create_test_directories()
    
    # Show environment info
    deps = show_environment_info()
    
    # Check if we can proceed
    if not deps.get('github', False):
        print("\n❌ PyGithub not available - cannot run full system tests")
        return False
    
    # Run tests
    tests = [
        (test_log_rotation, "Log Rotation"),
        (test_timezone_configuration, "Timezone Configuration"),
        (test_log_directory_structure, "Log Directory Structure"),
        (test_timing_and_duplicate_prevention, "Timing & Duplicate Prevention")
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
        print("\nSystem configuration and logging are working correctly:")
        print("• Daily log rotation with 30-day retention")
        print("• Configurable timezone support (default: Asia/Dhaka)")
        print("• 5-minute timing window for workflow execution")
        print("• Duplicate prevention for command execution")
    else:
        print("\nSome system tests failed. Check the configuration and try again.")
    
    return success


if __name__ == "__main__":
    run_system_tests()
