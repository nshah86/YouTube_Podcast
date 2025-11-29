# Automation Testing for VideoTranscript Pro

## Overview

This directory contains comprehensive automation tests for all features of VideoTranscript Pro.

## Test Coverage

The test suite covers:
1. ✅ Homepage loading
2. ✅ User signup
3. ✅ User login
4. ✅ Transcript extraction from YouTube videos
5. ✅ AI summary generation
6. ✅ Podcast generation
7. ✅ Navigation between pages

## Prerequisites

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install ChromeDriver:**
   - Windows: Download from https://chromedriver.chromium.org/
   - Or use: `pip install webdriver-manager`
   - ChromeDriver should be in your PATH

3. **Start the Flask app:**
   ```bash
   python start.py
   ```
   The app should be running at `http://127.0.0.1:5000`

## Running Tests

### Option 1: Using the test runner script (Recommended)
```bash
python run_tests.py
```

### Option 2: Using pytest directly
```bash
pytest tests/test_automation.py -v
```

### Option 3: Run with HTML report
```bash
pytest tests/test_automation.py -v --html=test_reports/report.html --self-contained-html
```

## Test Reports

Test reports are automatically generated in the `test_reports/` folder:

- **JSON Reports**: `test_reports/test_YYYYMMDD_HHMMSS.json`
  - Machine-readable test results
  - Includes test names, status, duration, errors

- **HTML Reports**: `test_reports/test_YYYYMMDD_HHMMSS.html`
  - Human-readable test results
  - Visual summary with pass/fail indicators
  - Detailed test information

## Test Configuration

Edit `tests/conftest.py` to configure:
- `BASE_URL`: The base URL of your application (default: http://127.0.0.1:5000)
- `TEST_VIDEOS`: List of YouTube video URLs to test with
- Browser options (headless mode, window size, etc.)

## Test User Accounts

The tests automatically generate unique test user accounts:
- Email format: `testuser_{timestamp}_{random}@test.com`
- Password: `TestPassword123!`

These accounts are created during signup tests and can be reused for login tests.

## YouTube Video Selection

The tests use short YouTube videos (30 seconds to 1 minute) with captions:
- Videos are randomly selected from a predefined list
- All videos are verified to have transcripts available

## Troubleshooting

### ChromeDriver not found
- Install ChromeDriver and add it to your PATH
- Or install: `pip install webdriver-manager`

### Tests timing out
- Increase wait times in `conftest.py`
- Check if the Flask app is running
- Verify network connectivity

### Tests failing
- Check browser console for JavaScript errors
- Verify Flask app logs
- Ensure all dependencies are installed

## Continuous Integration

These tests can be integrated into CI/CD pipelines:
```yaml
# Example GitHub Actions
- name: Run Tests
  run: |
    python start.py &
    sleep 5
    python run_tests.py
```

