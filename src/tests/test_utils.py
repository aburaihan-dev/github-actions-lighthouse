#!/usr/bin/env python3
"""
Test utilities for GitHub Actions Monitor

Reusable components for testing the monitor functionality.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Setup Python path for imports
def setup_python_path():
    """Add project root to Python path for imports."""
    # Get the project root (two levels up from src/tests)
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

# Load environment variables from .env file if it exists
def load_env():
    """Load environment variables from .env file."""
    try:
        from dotenv import load_dotenv
        # Look for .env file in project root
        project_root = Path(__file__).parent.parent.parent
        env_path = project_root / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✅ Loaded .env file from: {env_path.absolute()}")
            return True
    except ImportError:
        pass
    return False

def print_header(title, width=60):
    """Print a formatted header for test sections."""
    print("\n" + "=" * width)
    print(title)
    print("=" * width)

def print_subheader(title, width=40):
    """Print a formatted subheader for test subsections."""
    print(f"\n=== {title} ===")

def print_summary(results, test_names=None):
    """Print a formatted test summary."""
    print_header("TEST SUMMARY")
    
    passed = sum(results)
    total = len(results)
    
    if test_names:
        for i, (name, result) in enumerate(zip(test_names, results)):
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {name}")
    
    if passed == total:
        print(f"\n✅ All {total} tests passed!")
    else:
        print(f"\n⚠️  {passed}/{total} tests passed")
    
    return passed == total

def check_github_token():
    """Check if GitHub token is available."""
    github_token = os.getenv('GITHUB_TOKEN', 'Not set')
    if github_token != 'Not set':
        print("✅ GITHUB_TOKEN environment variable is set")
        return True
    else:
        print("⚠️  GITHUB_TOKEN environment variable not set")
        print("   You can set it by:")
        print("   - Creating a .env file with GITHUB_TOKEN=your_token")
        print("   - Setting environment variable: export GITHUB_TOKEN=your_token")
        return False

def check_dependencies():
    """Check if required dependencies are installed."""
    dependencies = {
        'github': 'PyGithub',
        'yaml': 'PyYAML',
        'dotenv': 'python-dotenv'
    }
    
    results = {}
    
    for module, package in dependencies.items():
        try:
            if module == 'github':
                import github
                try:
                    version = github.__version__
                except AttributeError:
                    try:
                        import pkg_resources
                        version = pkg_resources.get_distribution("PyGithub").version
                    except:
                        version = "unknown"
                print(f"✅ {package} version: {version}")
                results[module] = True
            elif module == 'yaml':
                import yaml
                print(f"✅ {package} available")
                results[module] = True
            elif module == 'dotenv':
                from dotenv import load_dotenv
                print(f"✅ {package} available (.env file support)")
                results[module] = True
        except ImportError:
            if module == 'dotenv':
                print(f"⚠️  {package} not installed - run: pip install {package}")
            else:
                print(f"❌ {package} not installed - run: pip install -r requirements.txt")
            results[module] = False
    
    return results

def show_environment_info():
    """Show comprehensive environment information."""
    print_subheader("Environment Information")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Project root: {Path(__file__).parent.parent.parent}")
    
    # Check for .env file
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / '.env'
    if env_file.exists():
        print(f"✅ .env file found: {env_file.absolute()}")
    else:
        print(f"⚠️  .env file not found (you can create one from .env.example)")
    
    # Check GitHub token
    check_github_token()
    
    # Check dependencies
    return check_dependencies()

def create_monitor_instance(config_path="config.yaml", local_mode=True):
    """Create a GitHubActionsMonitor instance for testing."""
    try:
        # Ensure Python path is set up
        setup_python_path()
        
        from github_actions_monitor import GitHubActionsMonitor
        
        # Use absolute path for config if it's relative
        if not Path(config_path).is_absolute():
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / config_path
        
        monitor = GitHubActionsMonitor(config_path=str(config_path), local_mode=local_mode)
        return monitor
    except Exception as e:
        print(f"❌ Error creating monitor instance: {e}")
        return None

def run_test_safely(test_func, test_name):
    """Run a test function safely with error handling."""
    try:
        result = test_func()
        return result
    except KeyboardInterrupt:
        print(f"\n❌ Test '{test_name}' interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Test '{test_name}' failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def format_age(seconds):
    """Format age in seconds to human-readable format."""
    if seconds < 3600:  # Less than 1 hour
        return f"{seconds/60:.0f}m ago"
    elif seconds < 86400:  # Less than 1 day
        return f"{seconds/3600:.1f}h ago"
    else:  # More than 1 day
        return f"{seconds/86400:.0f}d ago"

def format_duration(seconds):
    """Format duration in seconds to human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"

class TestResult:
    """Class to store test results with metadata."""
    
    def __init__(self, name, passed, message="", details=None):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now(timezone.utc)
    
    def __bool__(self):
        return self.passed
    
    def __str__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status} - {self.name}: {self.message}"

def create_test_directories():
    """Create necessary test directories."""
    directories = ['logs', 'data', 'test_logs', 'test_state', 'test_health']
    
    # Create directories relative to project root
    project_root = Path(__file__).parent.parent.parent
    
    for dir_name in directories:
        dir_path = project_root / dir_name
        try:
            dir_path.mkdir(exist_ok=True)
        except Exception as e:
            print(f"⚠️  Could not create directory {dir_name}: {e}")

def cleanup_test_files():
    """Clean up test files and directories."""
    project_root = Path(__file__).parent.parent.parent
    test_patterns = [
        'test_logs/*',
        'test_state/*',
        'test_health/*'
    ]
    
    for pattern in test_patterns:
        for file_path in project_root.glob(pattern):
            try:
                if file_path.is_file():
                    file_path.unlink()
                elif file_path.is_dir():
                    import shutil
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"⚠️  Could not clean up {file_path}: {e}")

def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent

def get_config_path(config_name="config.yaml"):
    """Get the full path to a config file."""
    return get_project_root() / config_name
