"""
Pytest configuration and fixtures for VideoTranscript Pro automation tests
"""
import pytest
import os
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import json
from datetime import datetime

# Test configuration
BASE_URL = os.getenv("TEST_BASE_URL", "http://127.0.0.1:5000")
TEST_REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_reports")
TEST_VIDEOS = [
    # Short videos with captions (30 sec - 1 min)
    "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # "Me at the zoo" - 19 seconds
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll - has captions
    "https://www.youtube.com/watch?v=9bZkp7q19f0",  # PSY - Gangnam Style
]

# Ensure test reports directory exists
os.makedirs(TEST_REPORTS_DIR, exist_ok=True)

# Global test report (single report for entire test run)
_global_test_report = None


@pytest.fixture(scope="session")
def driver():
    """Create and configure Chrome WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        yield driver
    finally:
        driver.quit()


@pytest.fixture
def test_user():
    """Generate a unique test user"""
    timestamp = int(time.time())
    random_num = random.randint(1000, 9999)
    return {
        "email": f"testuser_{timestamp}_{random_num}@test.com",
        "password": "TestPassword123!",
        "name": f"Test User {timestamp}"
    }


@pytest.fixture
def test_video_url():
    """Get a random test video URL"""
    return random.choice(TEST_VIDEOS)


@pytest.fixture(scope="session")
def test_report():
    """Initialize single consolidated test report for entire test run"""
    global _global_test_report
    
    if _global_test_report is None:
        _global_test_report = {
            "test_run_id": f"test_{int(time.time())}",
            "start_time": datetime.now().isoformat(),
            "base_url": BASE_URL,
            "tests": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0
            }
        }
    
    yield _global_test_report
    
    # Finalize report only once at end of session
    if _global_test_report and _global_test_report.get("end_time") is None:
        _global_test_report["end_time"] = datetime.now().isoformat()
        _global_test_report["duration"] = (
            datetime.fromisoformat(_global_test_report["end_time"]) - 
            datetime.fromisoformat(_global_test_report["start_time"])
        ).total_seconds()
        
        # Save consolidated report
        report_file = os.path.join(TEST_REPORTS_DIR, f"{_global_test_report['test_run_id']}.json")
        with open(report_file, "w") as f:
            json.dump(_global_test_report, f, indent=2)
        
        # Generate single HTML report
        html_file = report_file.replace(".json", ".html")
        generate_html_report(_global_test_report, html_file)
        
        print(f"\n✓ Consolidated Test Report generated:")
        print(f"  - JSON: {report_file}")
        print(f"  - HTML: {html_file}")


def generate_html_report(report, html_file):
    """Generate HTML test report"""
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test Report - {report['test_run_id']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
        h1 {{ color: #333; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .summary-card {{ flex: 1; padding: 20px; border-radius: 8px; text-align: center; }}
        .summary-card.total {{ background: #e3f2fd; }}
        .summary-card.passed {{ background: #c8e6c9; }}
        .summary-card.failed {{ background: #ffcdd2; }}
        .summary-card.skipped {{ background: #fff9c4; }}
        .summary-card h2 {{ margin: 0; font-size: 2.5em; }}
        .summary-card p {{ margin: 5px 0 0 0; color: #666; }}
        .test-item {{ padding: 15px; margin: 10px 0; border-left: 4px solid #ddd; background: #fafafa; }}
        .test-item.passed {{ border-color: #4caf50; }}
        .test-item.failed {{ border-color: #f44336; }}
        .test-item.skipped {{ border-color: #ffeb3b; }}
        .test-name {{ font-weight: bold; font-size: 1.1em; }}
        .test-details {{ margin-top: 10px; color: #666; }}
        .error {{ color: #f44336; background: #ffebee; padding: 10px; border-radius: 4px; margin-top: 10px; }}
        .timestamp {{ color: #999; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Test Report: {report['test_run_id']}</h1>
        <div class="timestamp">
            Started: {report['start_time']}<br>
            Ended: {report['end_time']}<br>
            Duration: {report['duration']:.2f} seconds
        </div>
        
        <div class="summary">
            <div class="summary-card total">
                <h2>{report['summary']['total']}</h2>
                <p>Total Tests</p>
            </div>
            <div class="summary-card passed">
                <h2>{report['summary']['passed']}</h2>
                <p>Passed</p>
            </div>
            <div class="summary-card failed">
                <h2>{report['summary']['failed']}</h2>
                <p>Failed</p>
            </div>
            <div class="summary-card skipped">
                <h2>{report['summary']['skipped']}</h2>
                <p>Skipped</p>
            </div>
        </div>
        
        <h2>Test Details</h2>
"""
    
    for test in report['tests']:
        status_class = test['status'].lower()
        html += f"""
        <div class="test-item {status_class}">
            <div class="test-name">{test['name']}</div>
            <div class="test-details">
                Status: <strong>{test['status']}</strong><br>
                Duration: {test.get('duration', 0):.2f}s
"""
        if test.get('error'):
            html += f'<div class="error">Error: {test["error"]}</div>'
        if test.get('details'):
            html += f'<div>Details: {test["details"]}</div>'
        html += """
            </div>
        </div>
"""
    
    html += """
    </div>
</body>
</html>
"""
    
    with open(html_file, "w") as f:
        f.write(html)
