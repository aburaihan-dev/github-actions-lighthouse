"""
GitHub Actions Monitor - Test Suite

This package contains comprehensive tests for the GitHub Actions Monitor service.

Test modules:
- test_utils: Common utilities and helpers for all tests
- test_connections: Configuration and GitHub API connection tests
- test_system: System functionality, logging, and timing tests
- test_all: Main test runner and orchestrator

Usage:
    python -m src.tests.test_all       # Run all tests
    python -m src.tests.test_all quick # Quick validation
    python src/tests/test_all.py       # Direct execution
"""

__version__ = "1.0.0"
__author__ = "GitHub Actions Monitor"

# Make test utilities available at package level
from .test_utils import (
    TestResult,
    load_env,
    setup_python_path,
    create_test_directories,
    check_dependencies,
    show_environment_info,
    create_monitor_instance,
    print_header,
    print_subheader,
    print_summary,
    run_test_safely
)

__all__ = [
    'TestResult',
    'load_env',
    'setup_python_path', 
    'create_test_directories',
    'check_dependencies',
    'show_environment_info',
    'create_monitor_instance',
    'print_header',
    'print_subheader', 
    'print_summary',
    'run_test_safely'
]
