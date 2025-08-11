# Test Structure Organization

## Overview
All tests have been moved to the `src/tests/` directory for better organization and maintainability.

## Directory Structure

```
├── run_tests.py              # Main test runner (convenience script)
└── src/tests/                # All test modules
    ├── __init__.py           # Package initialization and exports
    ├── test_all.py           # Main test orchestrator
    ├── test_connections.py   # Configuration and GitHub API tests
    ├── test_system.py        # System functionality and logging tests
    └── test_utils.py         # Common utilities and helpers
```

## Usage

### Main Test Runner
```bash
# From project root - convenience script
python run_tests.py [command]

# Available commands:
python run_tests.py help      # Show help information
python run_tests.py all       # Run complete test suite (default)
python run_tests.py quick     # Run quick validation tests
python run_tests.py overview  # Show system overview
```

### Direct Module Execution
```bash
# Run complete test suite
python -m src.tests.test_all [command]

# Run individual test modules
python -m src.tests.test_connections    # Configuration and API tests
python -m src.tests.test_system         # System and logging tests
```

### For Installed Service
```bash
# After installation via install.sh
cd /opt/github-actions-monitor
sudo -u github-monitor ./venv/bin/python run_tests.py quick
```

## Test Modules

### `test_all.py`
- Main test orchestrator
- Provides unified interface for all tests
- Handles test result aggregation and reporting

### `test_connections.py`
- Configuration loading and validation
- GitHub API connection testing
- Workflow monitoring validation
- Command configuration testing
- Command execution testing

### `test_system.py`
- Log rotation configuration
- Timezone handling
- Directory structure validation
- Timing and duplicate prevention
- Execution mapping logic
- Command logging functionality

### `test_utils.py`
- Common test utilities and helpers
- Environment setup and validation
- Monitor instance creation
- Dependency checking
- Formatting utilities

## Benefits of This Structure

✅ **Organized**: All tests in dedicated directory  
✅ **Modular**: Clear separation of test responsibilities  
✅ **Maintainable**: Easy to add new test modules  
✅ **Consistent**: Standard Python package structure  
✅ **Accessible**: Simple run script for convenience  
✅ **Professional**: Follows Python testing best practices  

## Integration

The test suite is automatically included in the installation process:
- Tests are copied to `/opt/github-actions-monitor/src/tests/`
- Main runner is available as `/opt/github-actions-monitor/run_tests.py`
- Virtual environment ensures consistent execution
- Service user has proper permissions to run tests

This structure makes the testing framework more maintainable while providing multiple ways to execute tests depending on the user's needs.
