#!/usr/bin/env python3
"""
Complete test suite for GitHub Actions Monitor
Consolidates all test modules into a unified testing interface
"""

import sys
from pathlib import Path
from .test_utils import *


def test_overview():
    """Display an overview of the monitoring system."""
    print_header("GitHub Actions Monitor - System Overview")
    
    # Show system info
    show_environment_info()
    
    # Show configuration summary
    print_subheader("Configuration Summary")
    
    try:
        config_file = get_config_path()
        if config_file.exists():
            with open(config_file, 'r') as f:
                import yaml
                config = yaml.safe_load(f)
                
            print("✅ Configuration file found")
            
            # Show repos
            repos = config.get('repositories', {})
            print(f"📁 Repositories configured: {len(repos)}")
            for repo_name in repos:
                print(f"   • {repo_name}")
            
            # Show timezone
            timezone = config.get('logging', {}).get('timezone', 'Asia/Dhaka')
            print(f"🌍 Timezone: {timezone}")
            
            # Show check interval
            check_interval = config.get('check_interval', 60)
            print(f"⏰ Check interval: {check_interval} seconds")
            
            # Show log configuration
            log_level = config.get('logging', {}).get('level', 'INFO')
            print(f"📋 Log level: {log_level}")
            
        else:
            print("❌ Configuration file not found: config.yaml")
            
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")
    
    # Show environment status
    print_subheader("Environment Status")
    
    project_root = get_project_root()
    env_file = project_root / ".env"
    if env_file.exists():
        print("✅ Environment file found: .env")
        # Don't read the actual content for security
        file_size = env_file.stat().st_size
        print(f"   File size: {file_size} bytes")
    else:
        print("⚠️  Environment file not found: .env")
        print("   Create .env with GITHUB_TOKEN=your_token")
    
    # Show log directory status
    log_dir = project_root / "logs"
    if log_dir.exists():
        log_files = list(log_dir.glob("*.log*"))
        print(f"📁 Log directory: {len(log_files)} files")
        for log_file in sorted(log_files)[-3:]:  # Show last 3 files
            file_size = log_file.stat().st_size
            print(f"   • {log_file.name} ({file_size} bytes)")
    else:
        print("📁 Log directory: Will be created on first run")


def run_all_tests():
    """Run all test modules and provide comprehensive results."""
    print_header("GitHub Actions Monitor - Complete Test Suite")
    
    # Setup
    load_env()
    setup_python_path()
    create_test_directories()
    
    # Test modules to run
    test_modules = [
        ("test_connections", "Configuration & GitHub Connection Tests"),
        ("test_system", "System & Logging Tests")
    ]
    
    all_results = {}
    overall_success = True
    
    for module_name, description in test_modules:
        print_header(f"Running {description}")
        
        try:
            # Import and run the test module
            if module_name == "test_connections":
                from .test_connections import run_connection_tests
                success = run_connection_tests()
            elif module_name == "test_system":
                from .test_system import run_system_tests
                success = run_system_tests()
            else:
                print(f"❌ Unknown test module: {module_name}")
                success = False
            
            all_results[module_name] = success
            overall_success = overall_success and success
            
            print(f"\n{'✅' if success else '❌'} {description}: {'PASSED' if success else 'FAILED'}")
            
        except ImportError as e:
            print(f"❌ Cannot import {module_name}: {e}")
            all_results[module_name] = False
            overall_success = False
        except Exception as e:
            print(f"❌ Error running {module_name}: {e}")
            all_results[module_name] = False
            overall_success = False
        
        print("\n" + "="*80 + "\n")
    
    # Final summary
    print_header("Test Suite Summary")
    
    for module_name, success in all_results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} {module_name}")
    
    print(f"\nOverall Status: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 Your GitHub Actions Monitor is ready to use!")
        print("\nNext steps:")
        print("1. Ensure .env file contains your GITHUB_TOKEN")
        print("2. Update config.yaml with your repositories")
        print("3. Run: python github_actions_monitor.py --local")
        print("4. For production: python github_actions_monitor.py")
    else:
        print("\n🔧 Some tests failed. Please check the configuration and dependencies.")
        print("\nCommon issues:")
        print("• Missing GITHUB_TOKEN in .env file")
        print("• Invalid GitHub token or no repository access")
        print("• Missing dependencies (run: pip install -r requirements.txt)")
        print("• Network connectivity issues")
    
    return overall_success


def run_quick_test():
    """Run a quick subset of tests for basic validation."""
    print_header("GitHub Actions Monitor - Quick Test")
    
    load_env()
    
    # Basic dependency check
    deps = check_dependencies()
    required_deps = ['yaml', 'github']
    
    missing_deps = [dep for dep in required_deps if not deps.get(dep, False)]
    
    if missing_deps:
        print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
        print("Install with: pip install PyGithub PyYAML python-dotenv")
        return False
    
    print("✅ All required dependencies available")
    
    # Configuration check
    config_file = get_config_path()
    if not config_file.exists():
        print("❌ Configuration file not found: config.yaml")
        return False
    
    print("✅ Configuration file found")
    
    # Environment check
    github_token = os.getenv('GITHUB_TOKEN')
    
    if not github_token:
        print("❌ GITHUB_TOKEN not found in environment")
        env_file = get_project_root() / ".env"
        if env_file.exists():
            print("   .env file exists but token not loaded")
        else:
            print("   Create .env file with GITHUB_TOKEN=your_token")
        return False
    
    print("✅ GitHub token found in environment")
    
    # Test monitor creation
    try:
        monitor = create_monitor_instance(str(config_file), local_mode=True)
        if not monitor:
            print("❌ Failed to create monitor instance")
            return False
        
        print("✅ Monitor instance created successfully")
        
        # Test GitHub connection
        monitor._initialize_github_client()
        if not monitor.github:
            print("❌ Failed to initialize GitHub client")
            return False
        
        print("✅ GitHub client initialized")
        
        # Test user access
        user = monitor.github.get_user()
        print(f"✅ Connected as GitHub user: {user.login}")
        
        print("\n🎉 Quick test passed! Your basic setup is working.")
        return True
        
    except Exception as e:
        print(f"❌ Error during quick test: {e}")
        return False


def show_help():
    """Show usage help."""
    print("GitHub Actions Monitor - Test Suite")
    print("="*50)
    print()
    print("Usage: python -m src.tests.test_all [command]")
    print("   or: python src/tests/test_all.py [command]")
    print()
    print("Commands:")
    print("  all      Run complete test suite (default)")
    print("  quick    Run quick validation tests")
    print("  overview Show system overview")
    print("  help     Show this help message")
    print()
    print("Individual test modules:")
    print("  python -m src.tests.test_connections  - Configuration and connection tests")
    print("  python -m src.tests.test_system       - System and logging tests")
    print()
    print("Examples:")
    print("  python -m src.tests.test_all          # Run all tests")
    print("  python -m src.tests.test_all quick    # Quick validation")
    print("  python -m src.tests.test_all overview # Show system status")


if __name__ == "__main__":
    # Parse command line arguments
    command = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if command == "help" or command == "-h" or command == "--help":
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
        print("Use 'python -m src.tests.test_all help' for usage information")
        sys.exit(1)
