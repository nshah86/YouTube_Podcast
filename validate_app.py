#!/usr/bin/env python3
"""
Pre-flight validation script for VideoTranscript Pro.
Checks all dependencies, imports, templates, and static files before starting the app.
"""
import os
import sys
from pathlib import Path

def print_status(message, status="INFO"):
    """Print colored status message."""
    colors = {
        "INFO": "\033[94m",  # Blue
        "SUCCESS": "\033[92m",  # Green
        "ERROR": "\033[91m",  # Red
        "WARNING": "\033[93m",  # Yellow
    }
    reset = "\033[0m"
    symbol = {"INFO": "ℹ", "SUCCESS": "✓", "ERROR": "✗", "WARNING": "⚠"}[status]
    print(f"{colors.get(status, '')}{symbol} {message}{reset}")

def check_python_version():
    """Check Python version."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_status(f"Python 3.8+ required. Found {version.major}.{version.minor}", "ERROR")
        return False
    print_status(f"Python {version.major}.{version.minor}.{version.micro}", "SUCCESS")
    return True

def check_required_packages():
    """Check if all required packages are installed."""
    required = [
        "flask",
        "youtube_transcript_api",
        "langchain",
        "langchain_openai",
        "gtts",
        "dotenv",
    ]
    missing = []
    for package in required:
        try:
            if package == "dotenv":
                __import__("dotenv")
            elif package == "langchain_openai":
                __import__("langchain_openai")
            else:
                __import__(package)
            print_status(f"Package '{package}' installed", "SUCCESS")
        except ImportError:
            print_status(f"Package '{package}' NOT installed", "ERROR")
            missing.append(package)
    
    if missing:
        print_status(f"Missing packages: {', '.join(missing)}", "ERROR")
        print_status("Run: pip install -r requirements.txt", "INFO")
        return False
    return True

def check_imports():
    """Check if all app imports work."""
    try:
        print_status("Testing imports...", "INFO")
        
        # Test config import
        from config import get_config
        print_status("Config module imported", "SUCCESS")
        
        # Test src imports
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
        from src.youtube_podcast.utils.youtube_utils import fetch_transcript
        from src.youtube_podcast.agents.summary_agent import generate_summary
        from src.youtube_podcast.agents.podcast_agent import create_conversation, generate_podcast
        from src.youtube_podcast.config.settings import DEFAULT_OUTPUT_DIR
        print_status("Source modules imported", "SUCCESS")
        
        # Test Flask app creation
        from app import create_app
        app = create_app()
        print_status("Flask app created successfully", "SUCCESS")
        
        return True
    except Exception as e:
        print_status(f"Import error: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        return False

def check_files():
    """Check if all required files exist."""
    required_files = {
        "app.py": "Main Flask application",
        "config.py": "Configuration module",
        "requirements.txt": "Dependencies list",
    }
    
    required_dirs = {
        "templates": "HTML templates",
        "static/css": "CSS stylesheets",
        "static/js": "JavaScript files",
        "src/youtube_podcast": "Core application code",
    }
    
    all_ok = True
    
    for file, desc in required_files.items():
        if os.path.exists(file):
            print_status(f"{desc} found: {file}", "SUCCESS")
        else:
            print_status(f"{desc} missing: {file}", "ERROR")
            all_ok = False
    
    for dir_path, desc in required_dirs.items():
        if os.path.isdir(dir_path):
            print_status(f"{desc} found: {dir_path}/", "SUCCESS")
        else:
            print_status(f"{desc} missing: {dir_path}/", "ERROR")
            all_ok = False
    
    return all_ok

def check_templates():
    """Check if all required templates exist."""
    required_templates = [
        "base.html",
        "index.html",
        "about.html",
        "features.html",
        "pricing.html",
        "api.html",
        "support.html",
        "404.html",
        "500.html",
    ]
    
    all_ok = True
    for template in required_templates:
        path = os.path.join("templates", template)
        if os.path.exists(path):
            print_status(f"Template found: {template}", "SUCCESS")
        else:
            print_status(f"Template missing: {template}", "ERROR")
            all_ok = False
    
    return all_ok

def check_static_files():
    """Check if static files exist."""
    static_files = {
        "static/css/style.css": "Main stylesheet",
        "static/js/main.js": "Main JavaScript",
    }
    
    all_ok = True
    for file, desc in static_files.items():
        if os.path.exists(file):
            print_status(f"{desc} found: {file}", "SUCCESS")
        else:
            print_status(f"{desc} missing: {file}", "ERROR")
            all_ok = False
    
    return all_ok

def check_environment():
    """Check environment variables."""
    print_status("Checking environment...", "INFO")
    
    # Check for .env file
    if os.path.exists(".env"):
        print_status(".env file found", "SUCCESS")
    else:
        print_status(".env file not found (optional for development)", "WARNING")
    
    # Check for OPENAI_API_KEY
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print_status("OPENAI_API_KEY is set", "SUCCESS")
    else:
        print_status("OPENAI_API_KEY not set (required for AI features)", "WARNING")
    
    # Check for SECRET_KEY
    secret_key = os.getenv("SECRET_KEY")
    if secret_key:
        print_status("SECRET_KEY is set", "SUCCESS")
    else:
        print_status("SECRET_KEY not set (will use default for development)", "WARNING")
    
    return True

def check_output_directory():
    """Check if output directory exists and is writable."""
    output_dir = os.path.join(os.getcwd(), "output")
    try:
        os.makedirs(output_dir, exist_ok=True)
        # Test write
        test_file = os.path.join(output_dir, ".test_write")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        print_status(f"Output directory writable: {output_dir}", "SUCCESS")
        return True
    except Exception as e:
        print_status(f"Output directory error: {str(e)}", "ERROR")
        return False

def main():
    """Run all validation checks."""
    print("\n" + "=" * 60)
    print("VideoTranscript Pro - Pre-flight Validation")
    print("=" * 60 + "\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Required Packages", check_required_packages),
        ("File Structure", check_files),
        ("Templates", check_templates),
        ("Static Files", check_static_files),
        ("Imports", check_imports),
        ("Environment", check_environment),
        ("Output Directory", check_output_directory),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n--- {name} ---")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print_status(f"Check failed with exception: {str(e)}", "ERROR")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {name}: {status}")
    
    print(f"\nTotal: {passed}/{total} checks passed")
    
    if passed == total:
        print_status("\nAll checks passed! App is ready to start.", "SUCCESS")
        return 0
    else:
        print_status(f"\n{total - passed} check(s) failed. Please fix issues before starting.", "ERROR")
        return 1

if __name__ == "__main__":
    sys.exit(main())

