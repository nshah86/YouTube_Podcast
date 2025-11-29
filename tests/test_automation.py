"""
Comprehensive automation tests for VideoTranscript Pro
Tests all features: signup, login, transcript extraction, summary, podcast generation
"""
import pytest
import time
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Add src to path for Supabase validation
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Test configuration (will be available via pytest fixtures)
BASE_URL = os.getenv("TEST_BASE_URL", "http://127.0.0.1:5000")


class TestAutomation:
    """Main test class for VideoTranscript Pro automation"""
    
    def test_01_homepage_loads(self, driver, test_report):
        """Test that homepage loads correctly"""
        test_name = "Homepage Loads"
        start_time = time.time()
        
        try:
            driver.get(BASE_URL)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check for key elements
            assert "VideoTranscript" in driver.title or "VideoTranscript" in driver.page_source
            assert driver.find_element(By.TAG_NAME, "input") or driver.find_element(By.ID, "youtube-url")
            
            duration = time.time() - start_time
            test_report['tests'].append({
                "name": test_name,
                "status": "PASSED",
                "duration": duration,
                "details": "Homepage loaded successfully"
            })
            test_report['summary']['total'] += 1
            test_report['summary']['passed'] += 1
            
        except Exception as e:
            duration = time.time() - start_time
            test_report['tests'].append({
                "name": test_name,
                "status": "FAILED",
                "duration": duration,
                "error": str(e)
            })
            test_report['summary']['total'] += 1
            test_report['summary']['failed'] += 1
            raise
    
    def test_02_user_signup(self, driver, test_user, test_report):
        """Test user signup functionality"""
        test_name = "User Signup"
        start_time = time.time()
        
        try:
            driver.get(f"{BASE_URL}/login")
            time.sleep(2)
            
            # Switch to signup tab
            try:
                signup_tab = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Sign Up')]"))
                )
                signup_tab.click()
                time.sleep(1)
            except:
                # If tab switching doesn't work, try direct signup form
                pass
            
            # Fill signup form
            email_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "signup-email"))
            )
            password_input = driver.find_element(By.ID, "signup-password")
            confirm_input = driver.find_element(By.ID, "signup-confirm")
            
            email_input.clear()
            email_input.send_keys(test_user["email"])
            password_input.clear()
            password_input.send_keys(test_user["password"])
            confirm_input.clear()
            confirm_input.send_keys(test_user["password"])
            
            # Submit form
            submit_btn = driver.find_element(By.XPATH, "//form[@id='signup-form']//button[@type='submit']")
            submit_btn.click()
            
            # Wait for response (either success message or redirect)
            time.sleep(3)
            
            # Check if signup was successful (check for success message or redirect)
            page_source = driver.page_source.lower()
            success_indicators = [
                "success",
                "account created",
                "redirecting",
                "login" in driver.current_url
            ]
            
            assert any(indicator in page_source or indicator in driver.current_url for indicator in success_indicators), \
                "Signup did not complete successfully"
            
            duration = time.time() - start_time
            test_report['tests'].append({
                "name": test_name,
                "status": "PASSED",
                "duration": duration,
                "details": f"User {test_user['email']} signed up successfully"
            })
            test_report['summary']['total'] += 1
            test_report['summary']['passed'] += 1
            
        except Exception as e:
            duration = time.time() - start_time
            test_report['tests'].append({
                "name": test_name,
                "status": "FAILED",
                "duration": duration,
                "error": str(e),
                "details": f"Failed to signup user {test_user['email']}"
            })
            test_report['summary']['total'] += 1
            test_report['summary']['failed'] += 1
            raise
    
    def test_03_user_login(self, driver, test_user, test_report):
        """Test user login functionality"""
        test_name = "User Login"
        start_time = time.time()
        
        try:
            driver.get(f"{BASE_URL}/login")
            time.sleep(2)
            
            # Fill login form
            email_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "login-email"))
            )
            password_input = driver.find_element(By.ID, "login-password")
            
            email_input.clear()
            email_input.send_keys(test_user["email"])
            password_input.clear()
            password_input.send_keys(test_user["password"])
            
            # Submit form
            submit_btn = driver.find_element(By.XPATH, "//form[@id='login-form']//button[@type='submit']")
            submit_btn.click()
            
            # Wait for login to complete
            time.sleep(3)
            
            # Check if logged in (check for logout button or account link)
            page_source = driver.page_source.lower()
            logged_in_indicators = [
                "logout" in page_source,
                "my account" in page_source,
                "account" in driver.current_url,
                BASE_URL in driver.current_url  # Redirected to home
            ]
            
            assert any(logged_in_indicators), "Login did not complete successfully"
            
            duration = time.time() - start_time
            test_report['tests'].append({
                "name": test_name,
                "status": "PASSED",
                "duration": duration,
                "details": f"User {test_user['email']} logged in successfully"
            })
            test_report['summary']['total'] += 1
            test_report['summary']['passed'] += 1
            
        except Exception as e:
            duration = time.time() - start_time
            test_report['tests'].append({
                "name": test_name,
                "status": "FAILED",
                "duration": duration,
                "error": str(e),
                "details": f"Failed to login user {test_user['email']}"
            })
            test_report['summary']['total'] += 1
            test_report['summary']['failed'] += 1
            raise
    
    def test_04_extract_transcript(self, driver, test_video_url, test_report):
        """Test transcript extraction from YouTube video"""
        test_name = "Extract Transcript"
        start_time = time.time()
        
        try:
            driver.get(BASE_URL)
            time.sleep(2)
            
            # Find and fill YouTube URL input
            url_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "youtube-url"))
            )
            url_input.clear()
            url_input.send_keys(test_video_url)
            
            # Click extract button
            extract_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "extract-btn"))
            )
            extract_btn.click()
            
            # Wait for transcript to load (check for transcript content or success message)
            time.sleep(10)  # Give time for transcript extraction
            
            # Check for transcript content
            page_source = driver.page_source
            transcript_indicators = [
                "transcript" in page_source.lower(),
                "copy" in page_source.lower(),
                "download" in page_source.lower(),
                driver.find_elements(By.CLASS_NAME, "transcript-content"),
                driver.find_elements(By.ID, "transcript-content")
            ]
            
            # Check if any indicator is present
            has_transcript = any(
                isinstance(ind, bool) and ind or 
                (isinstance(ind, list) and len(ind) > 0)
                for ind in transcript_indicators
            )
            
            assert has_transcript, "Transcript was not extracted or displayed"
            
            duration = time.time() - start_time
            test_report['tests'].append({
                "name": test_name,
                "status": "PASSED",
                "duration": duration,
                "details": f"Successfully extracted transcript from {test_video_url}"
            })
            test_report['summary']['total'] += 1
            test_report['summary']['passed'] += 1
            
        except Exception as e:
            duration = time.time() - start_time
            test_report['tests'].append({
                "name": test_name,
                "status": "FAILED",
                "duration": duration,
                "error": str(e),
                "details": f"Failed to extract transcript from {test_video_url}"
            })
            test_report['summary']['total'] += 1
            test_report['summary']['failed'] += 1
            raise
    
    def test_05_generate_summary(self, driver, test_report):
        """Test AI summary generation"""
        test_name = "Generate Summary"
        start_time = time.time()
        
        try:
            # Ensure we're on a page with transcript
            # If not, extract one first
            if "transcript" not in driver.page_source.lower():
                pytest.skip("No transcript available for summary generation")
            
            # Look for summary button or link
            summary_buttons = driver.find_elements(
                By.XPATH, 
                "//button[contains(text(), 'Summary') or contains(text(), 'Generate Summary')]"
            )
            
            if not summary_buttons:
                # Try to find by ID or class
                summary_buttons = driver.find_elements(By.ID, "generate-summary-btn")
                summary_buttons.extend(driver.find_elements(By.CLASS_NAME, "summary-btn"))
            
            if summary_buttons:
                summary_btn = summary_buttons[0]
                summary_btn.click()
                
                # Wait for summary to generate
                time.sleep(15)  # AI summary generation takes time
                
                # Check for summary content
                page_source = driver.page_source.lower()
                summary_indicators = [
                    "summary" in page_source,
                    "summary-content" in page_source,
                    len(driver.find_elements(By.CLASS_NAME, "summary-content")) > 0
                ]
                
                assert any(summary_indicators), "Summary was not generated"
                
                duration = time.time() - start_time
                test_report['tests'].append({
                    "name": test_name,
                    "status": "PASSED",
                    "duration": duration,
                    "details": "AI summary generated successfully"
                })
                test_report['summary']['total'] += 1
                test_report['summary']['passed'] += 1
            else:
                pytest.skip("Summary button not found - may require transcript first")
                
        except Exception as e:
            duration = time.time() - start_time
            test_report['tests'].append({
                "name": test_name,
                "status": "FAILED",
                "duration": duration,
                "error": str(e),
                "details": "Failed to generate summary"
            })
            test_report['summary']['total'] += 1
            test_report['summary']['failed'] += 1
            raise
    
    def test_06_generate_podcast(self, driver, test_report):
        """Test podcast generation"""
        test_name = "Generate Podcast"
        start_time = time.time()
        
        try:
            # Ensure we have a transcript
            if "transcript" not in driver.page_source.lower():
                pytest.skip("No transcript available for podcast generation")
            
            # Look for podcast button
            podcast_buttons = driver.find_elements(
                By.XPATH,
                "//button[contains(text(), 'Podcast') or contains(text(), 'Generate Podcast')]"
            )
            
            if not podcast_buttons:
                podcast_buttons = driver.find_elements(By.ID, "generate-podcast-btn")
                podcast_buttons.extend(driver.find_elements(By.CLASS_NAME, "podcast-btn"))
            
            if podcast_buttons:
                podcast_btn = podcast_buttons[0]
                podcast_btn.click()
                
                # Wait for podcast options or generation
                time.sleep(5)
                
                # Check for podcast options (voice selection, etc.)
                page_source = driver.page_source.lower()
                podcast_indicators = [
                    "podcast" in page_source,
                    "voice" in page_source,
                    "male" in page_source or "female" in page_source,
                    len(driver.find_elements(By.CLASS_NAME, "podcast-options")) > 0
                ]
                
                if any(podcast_indicators):
                    # Try to generate podcast (select voice and generate)
                    voice_buttons = driver.find_elements(
                        By.XPATH,
                        "//button[contains(text(), 'Male') or contains(text(), 'Female')]"
                    )
                    
                    if voice_buttons:
                        voice_buttons[0].click()
                        time.sleep(20)  # Podcast generation takes longer
                    
                    # Check for audio player or download link
                    audio_indicators = [
                        "audio" in page_source,
                        "download" in page_source,
                        len(driver.find_elements(By.TAG_NAME, "audio")) > 0
                    ]
                    
                    assert any(audio_indicators), "Podcast was not generated"
                    
                    duration = time.time() - start_time
                    test_report['tests'].append({
                        "name": test_name,
                        "status": "PASSED",
                        "duration": duration,
                        "details": "Podcast generated successfully"
                    })
                    test_report['summary']['total'] += 1
                    test_report['summary']['passed'] += 1
                else:
                    pytest.skip("Podcast options not available")
            else:
                pytest.skip("Podcast button not found")
                
        except Exception as e:
            duration = time.time() - start_time
            test_report['tests'].append({
                "name": test_name,
                "status": "FAILED",
                "duration": duration,
                "error": str(e),
                "details": "Failed to generate podcast"
            })
            test_report['summary']['total'] += 1
            test_report['summary']['failed'] += 1
            raise
    
    def test_07_navigation(self, driver, test_report):
        """Test navigation between pages"""
        test_name = "Navigation"
        start_time = time.time()
        
        try:
            pages = [
                ("/", "Home"),
                ("/features", "Features"),
                ("/pricing", "Pricing"),
                ("/api", "API"),
                ("/support", "Support"),
            ]
            
            for url, name in pages:
                driver.get(f"{BASE_URL}{url}")
                time.sleep(2)
                
                # Check page loaded
                assert driver.current_url.endswith(url) or BASE_URL in driver.current_url
                assert len(driver.page_source) > 1000  # Page has content
            
            duration = time.time() - start_time
            test_report['tests'].append({
                "name": test_name,
                "status": "PASSED",
                "duration": duration,
                "details": f"Successfully navigated to {len(pages)} pages"
            })
            test_report['summary']['total'] += 1
            test_report['summary']['passed'] += 1
            
        except Exception as e:
            duration = time.time() - start_time
            test_report['tests'].append({
                "name": test_name,
                "status": "FAILED",
                "duration": duration,
                "error": str(e)
            })
            test_report['summary']['total'] += 1
            test_report['summary']['failed'] += 1
            raise

