#!/usr/bin/env python3
"""
Test runner for GitHub Actions Monitor
Convenience script to run tests from project root
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run tests
try:
    from src.tests.test_all import show_help, test_overview, run_quick_test, run_all_tests
    
    # Parse command line arguments
    command = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if command == "help" or command == "-h" or command == "--help":
        print("GitHub Actions Monitor - Test Runner")
        print("="*50)
        print()
        print("This is a convenience script that runs the test suite.")
        print("You can also run tests directly using:")
        print("  python -m src.tests.test_all [command]")
        print()
        show_help()
    elif command == "overview":
        test_overview()
    elif command == "quick":
        success = run_quick_test()
        sys.exit(0 if success else 1)
    elif command == "all":
        success = run_all_tests()
        sys.exit(0 if success else 1)
    else:
        print(f"Unknown command: {command}")
        print("Use 'python run_tests.py help' for usage information")
        sys.exit(1)
        
except ImportError as e:
    print(f"❌ Error importing test modules: {e}")
    print("\nMake sure you're running this from the project root directory.")
    print("The test files should be in src/tests/")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error running tests: {e}")
    sys.exit(1)
