'''
Author:     Sai Vignesh Golla
LinkedIn:   https://www.linkedin.com/in/saivigneshgolla/

Copyright (C) 2024 Sai Vignesh Golla

License:    GNU Affero General Public License
            https://www.gnu.org/licenses/agpl-3.0.en.html
            
GitHub:     https://github.com/GodsScion/Auto_job_applier_linkedIn

version:    26.01.18.23.30

Contributor: Sanjay Nainwal (sanjaynainwal129@gmail.com) - Feature: Recruiter Messaging
'''


# Imports
import csv
import os
from datetime import datetime
from typing import Literal

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from config.recruiter_messaging import *
from config.personals import first_name, last_name
from config.questions import years_of_experience
from modules.helpers import print_lg, buffer, make_directories

# Import AI functions conditionally
if use_ai_for_messages:
    from config.secrets import ai_provider, use_AI
    if use_AI:
        from modules.ai.openaiConnections import ai_answer_question
        from modules.ai.deepseekConnections import deepseek_answer_question
        from modules.ai.geminiConnections import gemini_answer_question


# Global variables
messages_sent_today = 0
messaged_recruiters = set()  # Track recruiter IDs to avoid duplicates


def find_recruiter_on_job_page(driver: WebDriver) -> dict | None:
    '''
    Detects recruiter information from the job posting page.
    Returns a dictionary with recruiter details or None if not found.
    
    Returns:
    {
        'name': str,
        'title': str,
        'profile_link': str,
        'recruiter_id': str,
        'can_message': bool,
        'is_free_message': bool  # True if free message, False if InMail required
    }
    '''
    try:
        print_lg("DEBUG: Starting recruiter search...")
        
        # STEP 1: Find "Meet the hiring team" section
        # Verified XPath: Look for h2 with specific class and text, then get parent div
        hiring_team_section = None
        try:
            print_lg("DEBUG: Looking for 'Meet the hiring team' header...")
            hiring_team_header = driver.find_element(By.XPATH, 
                "//h2[contains(@class, 'text-heading-medium') and contains(normalize-space(.), 'Meet the hiring team')]")
            print_lg("DEBUG: Found header! Getting parent section...")
            hiring_team_section = hiring_team_header.find_element(By.XPATH, 
                "./parent::div[contains(@class, 'artdeco-card')]")
            print_lg("DEBUG: ✅ Found 'Meet the hiring team' section")
        except NoSuchElementException:
            print_lg("DEBUG: ❌ No 'Meet the hiring team' section found on this job posting.")
            return None
        
        if not hiring_team_section:
            print_lg("DEBUG: ❌ hiring_team_section is None")
            return None
        
        recruiter_info = {}
        
        # STEP 2: Find recruiter profile link
        try:
            print_lg("DEBUG: Looking for recruiter profile link...")
            recruiter_link = hiring_team_section.find_element(By.XPATH, ".//a[contains(@href, '/in/')]")
            recruiter_info['profile_link'] = recruiter_link.get_attribute('href')
            
            # Extract recruiter ID from profile link
            recruiter_id = recruiter_info['profile_link'].split('/in/')[-1].split('/')[0].split('?')[0]
            recruiter_info['recruiter_id'] = recruiter_id
            print_lg(f"DEBUG: ✅ Found profile link: {recruiter_info['profile_link']}")
        except NoSuchElementException:
            print_lg("DEBUG: ❌ Could not find recruiter profile link")
            return None
        
        # STEP 3: Find recruiter name
        try:
            print_lg("DEBUG: Looking for recruiter name...")
            name_element = hiring_team_section.find_element(By.XPATH, 
                ".//span[contains(@class, 'jobs-poster__name')]")
            recruiter_info['name'] = name_element.text.strip()
            print_lg(f"DEBUG: ✅ Found recruiter name: {recruiter_info['name']}")
        except NoSuchElementException:
            print_lg("DEBUG: ⚠️ Could not find recruiter name, using fallback")
            recruiter_info['name'] = "Unknown Recruiter"
        
        # STEP 4: Find recruiter title
        try:
            print_lg("DEBUG: Looking for recruiter title...")
            title_element = hiring_team_section.find_element(By.XPATH,
                ".//div[contains(@class, 'linked-area')]//div[contains(@class, 'text-body-small')]")
            recruiter_info['title'] = title_element.text.strip()
            print_lg(f"DEBUG: ✅ Found recruiter title: {recruiter_info['title']}")
        except NoSuchElementException:
            print_lg("DEBUG: ⚠️ Could not find recruiter title")
            recruiter_info['title'] = "Recruiter"
        
        # STEP 5: Check message capability
        print_lg("DEBUG: Checking message capability...")
        message_capability = check_message_capability(driver, hiring_team_section)
        recruiter_info['can_message'] = message_capability['can_message']
        recruiter_info['is_free_message'] = message_capability['is_free_message']
        
        print_lg(f"✅ Found recruiter: {recruiter_info['name']} ({recruiter_info['title']}) - "
                f"Can Message: {recruiter_info['can_message']}, Free Message: {recruiter_info['is_free_message']}")
        
        return recruiter_info
    
    except Exception as e:
        print_lg(f"❌ Error finding recruiter: {e}")
        import traceback
        print_lg(f"DEBUG: Traceback: {traceback.format_exc()}")
        return None


def check_message_capability(driver: WebDriver, hiring_team_section: WebElement) -> dict:
    '''
    Checks if recruiter can be messaged and if it's free or requires InMail.
    
    Returns:
    {
        'can_message': bool,
        'is_free_message': bool,  # True if free, False if InMail
        'message_type': str  # 'free', 'inmail', 'connection', or 'unavailable'
    }
    '''
    result = {
        'can_message': False,
        'is_free_message': False,
        'message_type': 'unavailable'
    }
    
    try:
        print_lg("DEBUG: Checking for Message button...")
        
        # STEP 1: Find Message button in entry-point div
        message_button = None
        try:
            # DEBUG: Print all buttons found to see what's available
            all_buttons = hiring_team_section.find_elements(By.TAG_NAME, "button")
            print_lg(f"DEBUG: Found {len(all_buttons)} buttons in hiring section:")
            for i, btn in enumerate(all_buttons):
                try:
                    txt = btn.text.strip()
                    cls = btn.get_attribute("class")
                    print_lg(f"  Button {i}: Text='{txt}', Class='{cls}'")
                except:
                    pass

            # Verified XPath - use normalize-space for text matching
            # Also tried finding by aria-label just in case
            message_button = hiring_team_section.find_element(By.XPATH,
                ".//button[contains(normalize-space(.), 'Message') or contains(@aria-label, 'Message')]")
            
            print_lg("DEBUG: ✅ Found Message button")
            result['can_message'] = True
        except NoSuchElementException:
            print_lg("DEBUG: ❌ No message button found (checked 'Message' text and aria-label)")
            return result
        
        if not result['can_message']:
            return result
        
        # STEP 2: Check connection degree (1st/2nd/3rd)
        try:
            print_lg("DEBUG: Checking connection degree...")
            connection_degree = hiring_team_section.find_element(By.XPATH,
                ".//span[contains(@class, 'hirer-card__connection-degree')]")
            degree_text = connection_degree.text.strip()
            print_lg(f"DEBUG: Connection degree: {degree_text}")
            
            if '1st' in degree_text or '2nd' in degree_text:
                result['is_free_message'] = True
                result['message_type'] = 'connection'
                print_lg(f"DEBUG: ✅ Recruiter is {degree_text} connection (FREE messaging)")
                return result
            elif '3rd' in degree_text:
                result['is_free_message'] = False
                result['message_type'] = 'inmail'
                print_lg(f"DEBUG: ❌ Recruiter is {degree_text} connection (INMAIL required)")
                return result
            else:
                print_lg(f"DEBUG: Recruiter connection degree: {degree_text} (unknown, assuming INMAIL)")
                result['is_free_message'] = False
                result['message_type'] = 'inmail'
                return result
        except NoSuchElementException:
            print_lg("DEBUG: ⚠️ Could not find connection degree")
            result['is_free_message'] = False
            result['message_type'] = 'inmail'
        
        # STEP 3: Check button classes for premium/inmail indicators
        try:
            button_classes = message_button.get_attribute('class')
            print_lg(f"DEBUG: Button classes: {button_classes}")
            
            if 'premium' in button_classes.lower() or 'inmail' in button_classes.lower():
                result['is_free_message'] = False
                result['message_type'] = 'inmail'
                print_lg("DEBUG: ❌ Button has premium/inmail class - requires InMail")
                return result
        except Exception as e:
            print_lg(f"DEBUG: Could not check button classes: {e}")
        
        # STEP 4: Default decision based on entry-point presence
        # If button is in entry-point div and no premium indicators, assume free
        result['is_free_message'] = True
        result['message_type'] = 'free'
        print_lg("DEBUG: ✅ Message button in entry-point div with no premium indicators - assuming FREE messaging")
        
        return result
    
    except Exception as e:
        print_lg(f"DEBUG: ❌ Error checking message capability: {e}")
        import traceback
        print_lg(f"DEBUG: Traceback: {traceback.format_exc()}")
        return result


def generate_personalized_message(
    aiClient,
    recruiter_info: dict,
    job_description: str,
    job_title: str,
    company_name: str,
    job_link: str
) -> tuple[str, str]:
    '''
    Generates a personalized message for the recruiter.
    Returns (subject, body) tuple.
    '''
    # Extract recruiter first name
    recruiter_name = recruiter_info.get('name', 'there').split()[0]
    your_name = f"{first_name} {last_name}"
    
    # Generate AI personalization if enabled
    personalized_intro = ""
    why_interested = ""
    
    if use_ai_for_messages and use_AI and aiClient:
        try:
            # Generate personalized intro
            intro_prompt = f"""Based on this job description, write a 2-sentence personalized introduction 
explaining why the candidate is a good fit. Be specific about matching skills.

Job Title: {job_title}
Company: {company_name}
Job Description: {job_description[:500]}
Candidate Experience: {years_of_experience} years in backend development with Java"""
            
            if ai_provider.lower() == "openai":
                personalized_intro = ai_answer_question(aiClient, intro_prompt, question_type="text")
            elif ai_provider.lower() == "deepseek":
                personalized_intro = deepseek_answer_question(aiClient, intro_prompt, question_type="text")
            elif ai_provider.lower() == "gemini":
                personalized_intro = gemini_answer_question(aiClient, intro_prompt, question_type="text")
            
            # Generate why interested
            interest_prompt = f"""Write 1 sentence explaining why the candidate is interested in this role, 
focusing on growth opportunity or company reputation.

Job Title: {job_title}
Company: {company_name}"""
            
            if ai_provider.lower() == "openai":
                why_interested = ai_answer_question(aiClient, interest_prompt, question_type="text")
            elif ai_provider.lower() == "deepseek":
                why_interested = deepseek_answer_question(aiClient, interest_prompt, question_type="text")
            elif ai_provider.lower() == "gemini":
                why_interested = gemini_answer_question(aiClient, interest_prompt, question_type="text")
            
            print_lg(f"AI-generated personalization completed")
            
        except Exception as e:
            print_lg(f"Failed to generate AI personalization: {e}")
            personalized_intro = ""
            why_interested = ""
    
    # Format subject
    subject = message_subject.format(
        job_title=job_title,
        company_name=company_name,
        recruiter_name=recruiter_name
    )
    
    # Format message body
    body = message_template.format(
        recruiter_name=recruiter_name,
        job_title=job_title,
        company_name=company_name,
        job_link=job_link,
        your_name=your_name,
        years_of_experience=years_of_experience,
        personalized_intro=personalized_intro,
        why_interested=why_interested,
        key_skills="Java, Spring Boot, Microservices"  # Can be made dynamic later
    ).strip()
    
    # Ensure message is within LinkedIn limits
    # Subject: 200 chars, Body: 1900 chars for regular messages
    if len(subject) > 200:
        subject = subject[:197] + "..."
    
    if len(body) > 1900:
        body = body[:1897] + "..."
    
    return subject, body


def send_message_to_recruiter(
    driver: WebDriver,
    recruiter_info: dict,
    subject: str,
    message_body: str
) -> tuple[bool, str]:
    '''
    Sends message to the recruiter via LinkedIn.
    Returns (success: bool, error_message: str)
    '''
    global messages_sent_today
    
    if dry_run_mode:
        print_lg(f"[DRY RUN] Would send message to {recruiter_info['name']}")
        print_lg(f"Subject: {subject}")
        print_lg(f"Body: {message_body}")
        return True, "Dry run - message not actually sent"
    
    msg_modal_open = False
    print_lg(f"DEBUG: Attempting to send message to {recruiter_info['name']} - Free: {recruiter_info.get('is_free_message', 'Unknown')}")
    try:
        # Find and click message button
        # VERIFIED XPATH: Use normalize-space for checking text to handle whitespace/newlines
        try:
            message_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(normalize-space(.), 'Message') or contains(@aria-label, 'Message')]")))
        except TimeoutException:
            # Fallback: Try looking specifically in the hiring team section if global search fails
            message_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(@class, 'artdeco-card')]//button[contains(normalize-space(.), 'Message')]")))

        # Scroll into view and click
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", message_button)
        buffer(1)
        message_button.click()
        msg_modal_open = True
        buffer(2)  # Wait for modal to open

        # Check if this is an InMail modal (uses credits)
        try:
            inmail_credits_element = driver.find_element(By.XPATH,
                "//section[contains(@class, 'msg-inmail-credits-display')] | //p[contains(text(), 'InMail credits')]")
            print_lg(f"DEBUG: InMail credits detected: {inmail_credits_element.text.strip()}")
            # This is InMail, close modal without sending
            print_lg("DEBUG: Skipping InMail to preserve credits")
            return False, "SKIP: InMail Required (credits detected in modal)"
        except NoSuchElementException:
            print_lg("DEBUG: No InMail credits detected - proceeding with free message")

        # Wait for message modal to appear
        wait = WebDriverWait(driver, 10)
        
        # Find subject field (if present)
        try:
            print_lg("DEBUG: Waiting for Subject field...")
            subject_field = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//input[@placeholder='Subject' or contains(@name, 'subject')]")))
            subject_field.clear()
            subject_field.send_keys(subject)
            print_lg("DEBUG: ✅ Subject typed")
        except TimeoutException:
            print_lg("DEBUG: Subject field not found - assuming regular message (not InMail)")
        
        # Find message body field
        print_lg("DEBUG: Waiting for Message Body field...")
        try:
            # Use specific class for contenteditable
            message_field = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@class, 'msg-form__contenteditable')]")))
            
            message_field.click()
            buffer(1)

            # Clear the field
            driver.execute_script("arguments[0].innerHTML = '<p></p>';", message_field)

            # Set text with JS and dispatch events
            driver.execute_script("arguments[0].innerHTML = '<p>' + arguments[1] + '</p>'; arguments[0].dispatchEvent(new Event('input', { bubbles: true })); arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", message_field, message_body)

            buffer(1)

            # Check if text was entered
            entered_text = message_field.get_attribute('innerText').strip()
            print(f"DEBUG: Entered text length: {len(entered_text)}")
            if not entered_text or len(entered_text) < 5:
                print_lg("DEBUG: ⚠️ JS text set failed, trying again...")
                driver.execute_script("arguments[0].innerHTML = '<p>' + arguments[1] + '</p>'; arguments[0].dispatchEvent(new Event('input', { bubbles: true })); arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", message_field, message_body)
                buffer(1)
                entered_text = message_field.get_attribute('innerText').strip()
                print(f"DEBUG: After retry, entered text length: {len(entered_text)}")

            if not entered_text or len(entered_text) < 5:
                print_lg("DEBUG: ❌ Text insertion completely failed")
                return False, "Text insertion failed"

            # Check send button
            send_button_pre_check = driver.find_elements(By.XPATH, "//button[contains(@class, 'msg-form__send-btn')]")
            is_send_enabled = len(send_button_pre_check) > 0 and send_button_pre_check[0].is_enabled()

            if not is_send_enabled:
                print_lg("DEBUG: ⚠️ Send button is disabled after text insertion")
            else:
                print_lg("DEBUG: ✅ Send button is enabled")

            print_lg("DEBUG: ✅ Message body process completed")

        except TimeoutException:
            print_lg("DEBUG: ❌ Could not find Message Body field!")
            return False, "Message Body field not found"

        # Find and click send button
        print_lg("DEBUG: Waiting for Send button...")
        try:
            send_button = driver.find_element(By.XPATH,
                "//button[contains(@class, 'msg-form__send-btn') or contains(text(), 'Send')]")
            
            # Check if button is enabled
            if not send_button.is_enabled():
                 print_lg("DEBUG: ⚠️ Send button is disabled! attempting final force enablement...")
                 # One last try to enable it by focusing and blurring
                 driver.execute_script("arguments[0].focus(); arguments[0].blur();", message_field)
                 buffer(1)
                 
                 if not send_button.is_enabled():
                     print_lg("DEBUG: ❌ Send button still disabled. Aborting to avoid stuck state.")
                     return False, "Send button disabled (text input failure)"
            
            try:
                send_button.click()
            except Exception as e:
                print_lg(f"DEBUG: Send button click failed: {e}")
                return False, "Send button click failed"

            print_lg(f"✅ Message sent successfully to {recruiter_info['name']}")
            messages_sent_today += 1
            messaged_recruiters.add(recruiter_info['recruiter_id'])

            buffer(3)  # Wait for message to send
            msg_modal_open = False # Considered closed if sent successfully (usually auto-closes)

            return True, ""
            
        except NoSuchElementException:
            print_lg("DEBUG: ❌ Send button not found!")
            return False, "Send button not found"
    
    except Exception as e:
        error_msg = f"Failed to send message: {str(e)}"
        print_lg(error_msg)
        return False, error_msg
        
    finally:
        # ALWAYS try to close the modal if it might still be open
        # This prevents the "stuck modal" issue
        try:
            print_lg("DEBUG: Checking for open modals to close")
            # Try ESC key first to dismiss any modal
            try:
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                buffer(1)
                print_lg("DEBUG: Attempted ESC to dismiss modals")
            except Exception as esc_e:
                print_lg(f"DEBUG: ESC key failed: {esc_e}")

            # Updated selectors based on User HTML
            # 1. Close icon button (SVG)
            # 2. Text "Close your draft conversation"
            # 3. Minimize button (fallback)
            close_buttons = driver.find_elements(By.XPATH,
                """//button[contains(@class, 'msg-overlay-bubble-header__control') or contains(@aria-label, 'Close') or contains(@title, 'Close')]""")
            
            if len(close_buttons) > 0:
                print_lg(f"DEBUG: Found {len(close_buttons)} close buttons. Ensuring modal is closed...")
                for btn in close_buttons:
                    try:
                        if btn.is_displayed():
                            btn.click()
                            buffer(1)
                            
                            # Handle "Discard draft" popup if it appears
                            try:
                                discard_btn = driver.find_element(By.XPATH, 
                                    "//button[contains(@class, 'artdeco-modal__confirm-btn') or contains(., 'Discard')]")
                                discard_btn.click()
                                print_lg("DEBUG: Discarded draft to close modal")
                            except:
                                pass
                    except:
                        pass
            else:
                 print_lg("DEBUG: ⚠️ No Close button found via new XPath")
                 
        except Exception as e:
            print_lg(f"DEBUG: Error ensuring modal closed: {e}")


def track_sent_message(
    job_id: str,
    job_title: str,
    company_name: str,
    job_link: str,
    recruiter_info: dict,
    subject: str,
    message_body: str,
    success: bool,
    skip_reason: str = "",
    error_message: str = ""
) -> None:
    '''
    Records sent message or skip reason in CSV file.
    '''
    try:
        # Ensure directory exists
        make_directories([message_history_file])
        
        # Determine message type
        if recruiter_info.get('is_free_message'):
            if recruiter_info.get('message_type') == 'connection':
                msg_type = "Free (1st Connection)"
            else:
                msg_type = "Free Message"
        else:
            msg_type = "Skipped - InMail Required"
        
        # Determine success status
        if skip_reason:
            status = "Skipped"
        elif success:
            status = "Sent"
        else:
            status = "Failed"
        
        # Prepare row data
        row = [
            job_id,
            job_title,
            company_name,
            job_link,
            recruiter_info.get('name', 'Unknown'),
            recruiter_info.get('title', 'Unknown'),
            recruiter_info.get('profile_link', ''),
            msg_type,
            subject,
            message_body,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            status,
            skip_reason,
            error_message
        ]
        
        # Check if file exists to determine if we need headers
        file_exists = os.path.exists(message_history_file)
        
        # Write to CSV
        with open(message_history_file, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Write header if new file
            if not file_exists:
                headers = [
                    'Job ID', 'Job Title', 'Company', 'Job Link',
                    'Recruiter Name', 'Recruiter Title', 'Recruiter Profile Link',
                    'Message Type', 'Subject', 'Message Body', 'Date Sent',
                    'Status', 'Skip Reason', 'Error Message'
                ]
                writer.writerow(headers)
            
            writer.writerow(row)
        
        print_lg(f"Tracking record saved for {recruiter_info.get('name', 'Unknown')}")
    
    except Exception as e:
        print_lg(f"Failed to track message: {e}")


def check_daily_message_limit() -> bool:
    '''
    Checks if daily message limit has been reached.
    Returns True if limit reached, False otherwise.
    '''
    global messages_sent_today
    
    if messages_sent_today >= max_messages_per_day:
        print_lg(f"⚠️ Daily message limit reached ({max_messages_per_day}). Stopping message sending.")
        return True
    
    return False


def should_skip_recruiter(recruiter_info: dict, job_id: str, already_applied: bool) -> tuple[bool, str]:
    '''
    Determines if recruiter should be skipped.
    Returns (should_skip: bool, reason: str)
    '''
    # Check if already messaged this recruiter
    if recruiter_info['recruiter_id'] in messaged_recruiters:
        return True, "Already messaged this recruiter today"
    
    # Check if already applied to job
    if skip_if_already_applied and already_applied:
        return True, "Already applied via Easy Apply"
    
    # Check if InMail required but we want only free messages
    if skip_inmail_required and not recruiter_info['is_free_message']:
        return True, "InMail required (preserving credits)"
    
    # Check daily limit
    if check_daily_message_limit():
        return True, "Daily message limit reached"
    
    # Check if can message at all
    if not recruiter_info['can_message']:
        return True, "No message button available"
    
    return False, ""
