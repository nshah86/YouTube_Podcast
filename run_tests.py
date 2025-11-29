"""
Test runner script for VideoTranscript Pro automation tests
Run this script to execute all automation tests and generate reports
"""
import subprocess
import sys
import os
from datetime import datetime

def main():
    """Run all automation tests"""
    print("=" * 60)
    print("VideoTranscript Pro - Automation Test Suite")
    print("=" * 60)
    print(f"Test Run Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Ensure test reports directory exists
    test_reports_dir = os.path.join(os.path.dirname(__file__), "test_reports")
    os.makedirs(test_reports_dir, exist_ok=True)
    
    # Create test run folder
    test_run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    test_run_dir = os.path.join(test_reports_dir, test_run_id)
    os.makedirs(test_run_dir, exist_ok=True)
    
    # Run pytest with HTML report (single consolidated report)
    pytest_args = [
        sys.executable, "-m", "pytest",
        "tests/test_automation.py",
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        f"--html={test_run_dir}/report.html",
        "--self-contained-html",  # Include CSS/JS in HTML
        "-s",  # Show print statements
    ]
    
    try:
        result = subprocess.run(pytest_args, check=False)
        
        print()
        print("=" * 60)
        print("Test Run Completed")
        print("=" * 60)
        print(f"Exit Code: {result.returncode}")
        print(f"Test Run ID: {test_run_id}")
        print(f"Reports saved in: {test_run_dir}")
        print()
        print("To view reports:")
        print(f"  - HTML Report: {test_run_dir}/report.html")
        print(f"  - JSON Report: {test_run_dir}/*.json (if generated)")
        print()
        
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n\nTest run interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\nError running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

