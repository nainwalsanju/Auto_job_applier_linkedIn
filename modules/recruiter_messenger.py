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
import random
import uuid
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
from config.personals import first_name, last_name, phone_number
from config.questions import years_of_experience, headline, linkedIn, website
from modules.helpers import print_lg, buffer, make_directories

# Import AI functions conditionally
if use_ai_for_messages:
    from config.secrets import ai_provider, use_AI
    if use_AI:
        from modules.ai.openaiConnections import ai_answer_question
        from modules.ai.deepseekConnections import deepseek_answer_question
        from modules.ai.geminiConnections import gemini_answer_question
        from modules.ai.prompts import generate_complete_message_prompt


def robust_find_element(driver_or_element: WebDriver | WebElement, selectors: list[tuple[By, str]], timeout: int = 10) -> WebElement:
    """
    Robustly find an element using multiple fallback selectors.

    Args:
        driver_or_element: WebDriver instance or WebElement to search within
        selectors: List of (By, selector) tuples to try in order
        timeout: Timeout for each attempt

    Returns:
        WebElement if found

    Raises:
        NoSuchElementException if none of the selectors work
    """
    for by, selector in selectors:
        try:
            element = WebDriverWait(driver_or_element, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            print_lg(f"DEBUG: Found element with selector: {by}='{selector}'")
            return element
        except (NoSuchElementException, TimeoutException):
            print_lg(f"DEBUG: Selector failed: {by}='{selector}', trying next...")
            continue
    raise NoSuchElementException(f"No element found with any of the provided selectors: {selectors}")


def robust_find_elements(driver_or_element: WebDriver | WebElement, selectors: list[tuple[By, str]], timeout: int = 10) -> list[WebElement]:
    """
    Robustly find elements using multiple fallback selectors.

    Args:
        driver_or_element: WebDriver instance or WebElement to search within
        selectors: List of (By, selector) tuples to try in order
        timeout: Timeout for each attempt

    Returns:
        List of WebElements found with the first working selector
    """
    for by, selector in selectors:
        try:
            elements = WebDriverWait(driver_or_element, timeout).until(
                lambda d: d.find_elements(by, selector)
            )
            if elements:
                print_lg(f"DEBUG: Found {len(elements)} elements with selector: {by}='{selector}'")
                return elements
        except (NoSuchElementException, TimeoutException):
            print_lg(f"DEBUG: Selector failed: {by}='{selector}', trying next...")
            continue
    print_lg(f"DEBUG: No elements found with any selector")
    return []


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
        hiring_team_header_selectors = [
            (By.XPATH, "//h2[contains(@class, 'text-heading-medium') and contains(normalize-space(.), 'Meet the hiring team')]"),
            (By.CSS_SELECTOR, "h2[class*='text-heading'][class*='medium']"),
            (By.XPATH, "//h2[contains(text(), 'Meet the hiring team')]"),
            (By.XPATH, "//h2[contains(text(), 'hiring team')]"),
            (By.XPATH, "//h2[contains(@aria-label, 'hiring team')]"),
            (By.XPATH, "//h3[contains(text(), 'Meet the hiring team')]"),
            (By.CSS_SELECTOR, "h2[data-test-id*='hiring']"),
            (By.XPATH, "//div[contains(@class, 'hiring-team')]//h2"),
        ]

        hiring_team_section_selectors = [
            (By.XPATH, "./ancestor::div[contains(@class, 'job-details-people-who-can-help__section--two-pane')]"),
            (By.XPATH, "./parent::div[contains(@class, 'artdeco-card')]"),
            (By.XPATH, "./ancestor::div[contains(@class, 'card')]"),
            (By.XPATH, "./parent::div"),
        ]

        hiring_team_section = None
        try:
            print_lg("DEBUG: Looking for 'Meet the hiring team' header...")
            hiring_team_header = robust_find_element(driver, hiring_team_header_selectors)
            print_lg("DEBUG: Found header! Getting parent section...")

            # Try multiple selectors for the section
            for by, selector in hiring_team_section_selectors:
                try:
                    hiring_team_section = hiring_team_header.find_element(by, selector)
                    print_lg(f"DEBUG: ✅ Found 'Meet the hiring team' section with {by}='{selector}'")
                    print_lg(f"DEBUG: Section contains {len(hiring_team_section.find_elements(By.TAG_NAME, 'a'))} links, {len(hiring_team_section.find_elements(By.TAG_NAME, 'span'))} spans, {len(hiring_team_section.find_elements(By.TAG_NAME, 'div'))} divs")
                    break
                except NoSuchElementException:
                    continue

            if not hiring_team_section:
                print_lg("DEBUG: ❌ Could not find section container with any selector")
                return None

        except NoSuchElementException:
            print_lg("DEBUG: ❌ No 'Meet the hiring team' section found on this job posting.")
            return None
        
        if not hiring_team_section:
            print_lg("DEBUG: ❌ hiring_team_section is None")
            return None

        recruiter_info = {}

        # STEP 2: Find recruiter profile link
        profile_link_selectors = [
            (By.XPATH, ".//div[contains(@class, 'display-flex align-items-center mt4')]//a[contains(@href, '/in/')]"),
            (By.XPATH, ".//a[contains(@href, '/in/')]"),
            (By.CSS_SELECTOR, "a[href*='/in/']"),
            (By.XPATH, ".//a[contains(@data-test-id, 'profile-link')]"),
            (By.XPATH, ".//a[contains(@aria-label, 'profile')]"),
            (By.XPATH, ".//a[@data-control-name='profile_link']"),
            (By.CSS_SELECTOR, "a[data-control-name='profile_link']"),
        ]

        try:
            print_lg(f"DEBUG: STEP 2: Extracting profile link from {len(hiring_team_section.find_elements(By.XPATH, './/a'))} total links in section")
            print_lg("DEBUG: Looking for recruiter profile link...")
            recruiter_link = robust_find_element(hiring_team_section, profile_link_selectors)
            recruiter_info['profile_link'] = recruiter_link.get_attribute('href')

            # Extract recruiter ID from profile link
            recruiter_id = recruiter_info['profile_link'].split('/in/')[-1].split('/')[0].split('?')[0]
            recruiter_info['recruiter_id'] = recruiter_id
            print_lg(f"DEBUG: ✅ Found profile link: {recruiter_info['profile_link']}")
        except NoSuchElementException:
            print_lg("DEBUG: ❌ Could not find recruiter profile link")
            return None

        # STEP 3: Find recruiter name
        name_selectors = [
            (By.XPATH, ".//div[contains(@class, 'display-flex align-items-center mt4')]//span"),
            (By.XPATH, ".//span[contains(@class, 'jobs-poster__name')]"),
            (By.CSS_SELECTOR, "span[class*='poster'][class*='name']"),
            (By.XPATH, ".//span[contains(@data-test-id, 'name')]"),
            (By.XPATH, ".//span[contains(@aria-label, 'name')]"),
            (By.XPATH, ".//a[contains(@href, '/in/')]/span"),  # name inside profile link
            (By.XPATH, ".//h3"),  # sometimes name is h3
            (By.XPATH, ".//span[contains(@class, 'hirer-card__name')]"),
            (By.CSS_SELECTOR, "span[class*='hirer-card'][class*='name']"),
        ]

        try:
            print_lg("DEBUG: STEP 3: Extracting recruiter name")
            print_lg("DEBUG: Looking for recruiter name...")
            name_element = robust_find_element(hiring_team_section, name_selectors)
            recruiter_info['name'] = name_element.text.strip()
            print_lg(f"DEBUG: ✅ Found recruiter name: {recruiter_info['name']}")
        except NoSuchElementException:
            print_lg("DEBUG: ⚠️ Could not find recruiter name, using fallback")
            recruiter_info['name'] = "Unknown Recruiter"

        # STEP 4: Find recruiter title
        title_selectors = [
            (By.XPATH, ".//div[contains(@class, 'display-flex align-items-center mt4')]//div[contains(@class, 'text-body-small')]"),
            (By.XPATH, ".//div[contains(@class, 'linked-area')]//div[contains(@class, 'text-body-small')]"),
            (By.CSS_SELECTOR, "div[class*='linked-area'] div[class*='text-body']"),
            (By.XPATH, ".//div[contains(@data-test-id, 'title')]"),
            (By.XPATH, ".//span[contains(@aria-label, 'title')]"),
            (By.XPATH, ".//div[contains(@class, 'text-body-small')]"),
            (By.XPATH, ".//div[contains(@class, 'subtitle')]"),
            (By.XPATH, ".//div[contains(@class, 'hirer-card__subtitle')]"),
            (By.CSS_SELECTOR, "div[class*='hirer-card'][class*='subtitle']"),
        ]

        try:
            print_lg("DEBUG: STEP 4: Extracting recruiter title")
            print_lg("DEBUG: Looking for recruiter title...")
            title_element = robust_find_element(hiring_team_section, title_selectors)
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
        
        print_lg("DEBUG: Recruiter detection completed successfully")

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
        message_button_selectors = [
            (By.XPATH, ".//button[contains(normalize-space(.), 'Message') or contains(@aria-label, 'Message')]"),
            (By.CSS_SELECTOR, "button[aria-label*='Message']"),
            (By.XPATH, ".//button[contains(@data-test-id, 'message-button')]"),
            (By.XPATH, ".//button[contains(@class, 'message')]"),
            (By.XPATH, ".//button[contains(@title, 'Message')]"),
            (By.XPATH, ".//button[@data-control-name='message']"),
            (By.CSS_SELECTOR, "button[data-control-name='message']"),
            (By.XPATH, ".//button[@data-control-name='message_from_profile']"),
            (By.XPATH, ".//button[contains(@aria-label, 'Send message to')]"),
            (By.XPATH, ".//button[contains(@data-tracking-control-name, 'message')]"),
        ]

        message_button = None
        try:
            # DEBUG: Print all buttons found to see what's available
            all_buttons = robust_find_elements(hiring_team_section, [(By.TAG_NAME, "button")])
            print_lg(f"DEBUG: Found {len(all_buttons)} buttons in hiring section:")
            for i, btn in enumerate(all_buttons):
                try:
                    txt = btn.text.strip()
                    cls = btn.get_attribute("class")
                    aria = btn.get_attribute("aria-label")
                    print_lg(f"  Button {i}: Text='{txt}', Class='{cls}', Aria='{aria}'")
                except:
                    pass

            message_button = robust_find_element(hiring_team_section, message_button_selectors)

            print_lg("DEBUG: ✅ Found Message button")
            result['can_message'] = True
        except NoSuchElementException:
            print_lg("DEBUG: ❌ No message button found with any selector")
            return result
        
        if not result['can_message']:
            return result

        # STEP 2: Open message modal to check for InMail credits display
        print_lg("DEBUG: Opening message modal to check for InMail credits...")
        modal_opened = False
        try:
            # Click the message button
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", message_button)
            buffer(1)
            message_button.click()
            modal_opened = True

            # Wait for modal to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'msg-form__contenteditable')]"))
            )
            buffer(1)

            # Check for InMail credits in the modal
            inmail_selectors = [
                (By.XPATH, "//section[contains(@class, 'msg-inmail-credits-display')]"),
                (By.XPATH, "//p[contains(text(), 'InMail credits')]"),
                (By.XPATH, "//*[contains(text(), 'Use') and contains(text(), 'InMail credits')]"),
                (By.CSS_SELECTOR, "section[class*='inmail-credits']"),
                (By.XPATH, "//div[contains(@class, 'inmail')]"),
                (By.XPATH, "//div[contains(@class, 'premium-upsell')]"),
                (By.CSS_SELECTOR, "div[class*='premium-upsell']"),
                (By.XPATH, "//span[contains(text(), 'Premium')]"),
                (By.XPATH, "//div[contains(@class, 'msg-inmail-upsell')]"),
                (By.XPATH, "//div[contains(@aria-label, 'InMail credits')]"),
                (By.XPATH, "//button[contains(@aria-label, 'Buy InMail credits')]"),
            ]

            try:
                inmail_element = robust_find_element(driver, inmail_selectors, timeout=5)
                print_lg(f"DEBUG: InMail credits detected in modal: {inmail_element.text.strip()}")
                result['is_free_message'] = False
                result['message_type'] = 'inmail'
                print_lg("DEBUG: ❌ Modal shows InMail credits - requires InMail")
                return result
            except NoSuchElementException:
                print_lg("DEBUG: No InMail credits detected in modal - assuming free message")
                result['is_free_message'] = True
                result['message_type'] = 'free'
                return result

        except Exception as e:
            print_lg(f"DEBUG: Error opening modal for check: {e}")
            # Fallback to connection degree check
            print_lg("DEBUG: Falling back to connection degree check...")

            # STEP 3: Check connection degree (1st/2nd/3rd)
            connection_degree_selectors = [
                (By.XPATH, ".//span[contains(@class, 'hirer-card__connection-degree')]"),
                (By.CSS_SELECTOR, "span[class*='connection-degree']"),
                (By.XPATH, ".//span[contains(@aria-label, 'connection')]"),
                (By.XPATH, ".//span[contains(text(), '1st') or contains(text(), '2nd') or contains(text(), '3rd')]"),
                (By.XPATH, ".//div[contains(@class, 'connection')]//span"),
                (By.XPATH, ".//span[contains(@class, 'degree-icon')]"),
                (By.CSS_SELECTOR, "span[class*='degree']"),
            ]

            try:
                print_lg("DEBUG: Checking connection degree...")
                connection_degree = robust_find_element(hiring_team_section, connection_degree_selectors)
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

            # STEP 4: Check button classes for premium/inmail indicators
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

            # STEP 5: Default decision based on entry-point presence
            # If button is in entry-point div and no premium indicators, assume free
            result['is_free_message'] = True
            result['message_type'] = 'free'
            print_lg("DEBUG: ✅ Message button in entry-point div with no premium indicators - assuming FREE messaging")

        finally:
            # Close the modal if it was opened
            if modal_opened:
                try:
                    # Try ESC key to close modal
                    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                    buffer(1)
                    print_lg("DEBUG: Closed modal after check")
                except Exception as e:
                    print_lg(f"DEBUG: Error closing modal: {e}")
        
        return result
    
    except Exception as e:
        print_lg(f"DEBUG: ❌ Error checking message capability: {e}")
        import traceback
        print_lg(f"DEBUG: Traceback: {traceback.format_exc()}")
        return result


def clean_message_for_chrome(message: str) -> str:
    '''
    Remove non-BMP Unicode characters (emojis, etc.) that ChromeDriver can't handle.
    '''
    return ''.join(c for c in message if ord(c) < 0x10000)


def generate_personalized_message(
    aiClient,
    recruiter_info: dict,
    job_description: str,
    job_title: str,
    company_name: str,
    job_link: str
) -> tuple[str, str, str]:
    '''
    Generates a personalized message for the recruiter using random template selection for A/B testing.
    Returns (subject, body, template_name) tuple.
    '''
    # Extract recruiter first name and title
    recruiter_name = recruiter_info.get('name', 'there').split()[0]
    recruiter_full_name = recruiter_info.get('name', 'Recruiter')
    recruiter_title = recruiter_info.get('title', 'Recruiter')
    your_name = f"{first_name} {last_name}"

    # Randomly select a message template for A/B testing
    selected_template = random.choice(message_templates)
    template_name = selected_template["name"]
    print_lg(f"A/B Testing: Selected template '{template_name}' for recruiter {recruiter_name}")

    # Generate AI personalization if enabled
    ai_generated_body = ""

    if use_ai_for_messages and use_AI and aiClient:
        try:
            # Generate complete personalized message body
            complete_prompt = generate_complete_message_prompt.format(
                recruiter_name=recruiter_full_name,
                recruiter_title=recruiter_title,
                job_title=job_title,
                company_name=company_name,
                job_description=job_description[:1000],  # Limit description length
                candidate_name=your_name,
                years_of_experience=years_of_experience,
                candidate_headline=headline,
                candidate_summary=headline,  # Using headline as summary for now, could enhance later
                candidate_skills="Java, Spring Boot, Microservices, Backend Development",  # Could be made dynamic
                linkedin_profile=linkedIn,
                portfolio_url=website,
                phone_number=phone_number,
                resume_link="https://drive.google.com/file/d/1kLdZWzTeRAAm4QtWrv2UQjHJ-H5ADOgd/view?usp=sharing",  # Hardcoded for now
                job_link=job_link
            )

            if ai_provider.lower() == "openai":
                ai_generated_body = ai_answer_question(aiClient, complete_prompt, question_type="text")
            elif ai_provider.lower() == "deepseek":
                ai_generated_body = deepseek_answer_question(aiClient, complete_prompt, question_type="text")
            elif ai_provider.lower() == "gemini":
                ai_generated_body = gemini_answer_question(aiClient, complete_prompt, question_type="text")

            print_lg(f"AI-generated complete personalized message completed")

        except Exception as e:
            print_lg(f"Failed to generate AI personalized message: {e}")
            ai_generated_body = ""

    # Format subject from selected template
    subject = selected_template["subject"].format(
        job_title=job_title,
        company_name=company_name,
        recruiter_name=recruiter_name
    )

    # Use AI-generated body if available, otherwise use selected template
    if ai_generated_body and ai_generated_body.strip():
        body = ai_generated_body.strip()
    else:
        # Use selected template body with fallback values for personalized_intro and why_interested
        personalized_intro = ""
        why_interested = ""
        body = selected_template["body"].format(
            recruiter_name=recruiter_name,
            job_title=job_title,
            company_name=company_name,
            job_link=job_link,
            your_name=your_name,
            years_of_experience=years_of_experience,
            personalized_intro=personalized_intro,
            why_interested=why_interested,
            key_skills="Java, Spring Boot, Microservices"
        ).strip()

    # Clean message for ChromeDriver compatibility
    subject = clean_message_for_chrome(subject)
    body = clean_message_for_chrome(body)

    # Ensure message is within LinkedIn limits
    # Subject: 200 chars, Body: 1900 chars for regular messages
    if len(subject) > 200:
        subject = subject[:197] + "..."

    if len(body) > 1900:
        body = body[:1897] + "..."

    return subject, body, template_name


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
        global_message_selectors = [
            (By.XPATH, "//button[contains(normalize-space(.), 'Message') or contains(@aria-label, 'Message')]"),
            (By.CSS_SELECTOR, "button[aria-label*='Message']"),
            (By.XPATH, "//button[contains(@data-test-id, 'message-button')]"),
            (By.XPATH, "//button[contains(@title, 'Message')]"),
            (By.XPATH, "//button[@data-control-name='message']"),
            (By.CSS_SELECTOR, "button[data-control-name='message']"),
            (By.XPATH, "//button[contains(@class, 'message') and not(contains(@class, 'premium'))]"),
            (By.XPATH, "//button[@data-control-name='message_from_profile']"),
            (By.XPATH, "//button[contains(@aria-label, 'Send message to')]"),
            (By.XPATH, "//button[contains(@data-tracking-control-name, 'message')]"),
        ]

        hiring_team_message_selectors = [
            (By.XPATH, "//div[contains(@class, 'artdeco-card')]//button[contains(normalize-space(.), 'Message')]"),
            (By.CSS_SELECTOR, "div[class*='card'] button[aria-label*='Message']"),
            (By.XPATH, "//div[contains(@class, 'hirer-card')]//button[@data-control-name='message']"),
            (By.XPATH, "//div[contains(@class, 'hirer-card')]//button[@data-control-name='message_from_profile']"),
            (By.XPATH, "//div[contains(@class, 'hirer-card')]//button[contains(@aria-label, 'Send message to')]"),
        ]

        try:
            # Try global selectors first
            message_button = robust_find_element(driver, global_message_selectors)
        except NoSuchElementException:
            # Fallback to hiring team section
            message_button = robust_find_element(driver, hiring_team_message_selectors)

        # Scroll into view and click
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", message_button)
        buffer(1)

        # Retry logic for opening message modal
        max_modal_retries = 3
        modal_opened = False
        for attempt in range(max_modal_retries):
            try:
                message_button.click()
                msg_modal_open = True

                # Wait for modal to fully load using WebDriverWait for textarea placeholder
                wait = WebDriverWait(driver, 10)
                wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'msg-form__contenteditable') and (@placeholder or @data-placeholder)]")))

                # Add buffer sleep for modal animation
                buffer(1)

                modal_opened = True
                print_lg(f"DEBUG: Message modal opened successfully on attempt {attempt + 1}")
                break

            except TimeoutException:
                if attempt == max_modal_retries - 1:
                    print_lg(f"DEBUG: Failed to open message modal after {max_modal_retries} attempts")
                    raise
                print_lg(f"DEBUG: Modal not loaded on attempt {attempt + 1}, retrying...")
                buffer(2)  # Buffer before retry

        # Check if this is an InMail modal (uses credits)
        inmail_selectors = [
            (By.XPATH, "//section[contains(@class, 'msg-inmail-credits-display')]"),
            (By.XPATH, "//p[contains(text(), 'InMail credits')]"),
            (By.XPATH, "//*[contains(text(), 'Use') and contains(text(), 'InMail credits')]"),
            (By.CSS_SELECTOR, "section[class*='inmail-credits']"),
            (By.XPATH, "//div[contains(@class, 'inmail')]"),
            (By.XPATH, "//div[contains(@class, 'premium-upsell')]"),
            (By.CSS_SELECTOR, "div[class*='premium-upsell']"),
            (By.XPATH, "//span[contains(text(), 'Premium')]"),
            (By.XPATH, "//div[contains(@class, 'msg-inmail-upsell')]"),
            (By.XPATH, "//div[contains(@aria-label, 'InMail credits')]"),
            (By.XPATH, "//button[contains(@aria-label, 'Buy InMail credits')]"),
        ]

        is_inmail = False
        try:
            inmail_credits_element = robust_find_element(driver, inmail_selectors)
            print_lg(f"DEBUG: InMail credits detected: {inmail_credits_element.text.strip()}")
            is_inmail = True
        except NoSuchElementException:
            print_lg("DEBUG: No InMail credits detected - proceeding with message")

        # If InMail and we want to skip InMail, skip
        if is_inmail and skip_inmail_required:
            print_lg("DEBUG: Skipping InMail as per configuration")
            return False, "SKIP: InMail Required (skip_inmail_required=True)"
        elif is_inmail:
            print_lg("DEBUG: Proceeding with InMail message (skip_inmail_required=False)")

        # Wait for message modal to appear
        wait = WebDriverWait(driver, 10)

        # Find subject field (if present)
        subject_selectors = [
            (By.XPATH, "//input[@placeholder='Subject' or contains(@name, 'subject')]"),
            (By.CSS_SELECTOR, "input[placeholder='Subject']"),
            (By.XPATH, "//input[contains(@aria-label, 'Subject')]"),
            (By.XPATH, "//input[contains(@id, 'subject')]"),
            (By.XPATH, "//input[@name='subject']"),
            (By.CSS_SELECTOR, "input[name='subject']"),
            (By.XPATH, "//input[@data-test-id='subject-input']"),
        ]

        try:
            print_lg("DEBUG: Waiting for Subject field...")
            subject_field = robust_find_element(driver, subject_selectors)
            subject_field.clear()
            subject_field.send_keys(subject)
            print_lg("DEBUG: ✅ Subject typed")
        except NoSuchElementException:
            print_lg("DEBUG: Subject field not found - assuming regular message (not InMail)")

        # Find message body field
        message_body_selectors = [
            (By.XPATH, "//div[contains(@class, 'msg-form__contenteditable')]"),
            (By.CSS_SELECTOR, "div[class*='msg-form'][class*='contenteditable']"),
            (By.XPATH, "//div[contains(@contenteditable, 'true')]"),
            (By.XPATH, "//div[contains(@role, 'textbox')]"),
            (By.XPATH, "//div[contains(@aria-label, 'message')]"),
            (By.XPATH, "//div[@contenteditable='true' and contains(@placeholder, 'Write a message')]"),
            (By.CSS_SELECTOR, "div[contenteditable='true']"),
            (By.XPATH, "//div[contains(@class, 'editor-content')]"),
            (By.XPATH, "//div[contains(@aria-label, 'Write a message')]"),
            (By.XPATH, "//div[@data-test-id='message-input']"),
        ]

        print_lg("DEBUG: Waiting for Message Body field...")
        try:
            message_field = robust_find_element(driver, message_body_selectors)

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
            send_button_pre_check_selectors = [
                (By.XPATH, "//button[contains(@class, 'msg-form__send-btn')]"),
                (By.CSS_SELECTOR, "button[class*='msg-form'][class*='send-btn']"),
            ]
            send_button_pre_check = robust_find_elements(driver, send_button_pre_check_selectors)
            is_send_enabled = len(send_button_pre_check) > 0 and send_button_pre_check[0].is_enabled()

            if not is_send_enabled:
                print_lg("DEBUG: ⚠️ Send button is disabled after text insertion")
            else:
                print_lg("DEBUG: ✅ Send button is enabled")

            print_lg("DEBUG: ✅ Message body process completed")

        except NoSuchElementException:
            print_lg("DEBUG: ❌ Could not find Message Body field!")
            return False, "Message Body field not found"

        # Find and click send button
        send_button_selectors = [
            (By.XPATH, "//button[contains(@class, 'msg-form__send-btn') or contains(text(), 'Send')]"),
            (By.CSS_SELECTOR, "button[class*='msg-form'][class*='send-btn']"),
            (By.XPATH, "//button[contains(@aria-label, 'Send')]"),
            (By.XPATH, "//button[contains(@data-test-id, 'send-button')]"),
            (By.XPATH, "//button[type='submit']"),
            (By.XPATH, "//button[@data-control-name='send']"),
            (By.CSS_SELECTOR, "button[data-control-name='send']"),
            (By.XPATH, "//button[contains(@class, 'send-button')]"),
            (By.XPATH, "//button[contains(@aria-label, 'Send message')]"),
            (By.XPATH, "//button[@data-tracking-control-name='send_message']"),
        ]

        print_lg("DEBUG: Waiting for Send button...")
        try:
            send_button = robust_find_element(driver, send_button_selectors)

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
            close_button_selectors = [
                (By.XPATH, "//button[contains(@class, 'msg-overlay-bubble-header__control') or contains(@aria-label, 'Close') or contains(@title, 'Close')]"),
                (By.CSS_SELECTOR, "button[aria-label='Close']"),
                (By.XPATH, "//button[contains(@data-test-id, 'close-button')]"),
                (By.XPATH, "//button[contains(text(), 'Close')]"),
                (By.XPATH, "//button[@data-control-name='overlay.close_conversation_window']"),
                (By.XPATH, "//button[contains(@aria-label, 'Dismiss')]"),
            ]

            close_buttons = []
            for by, selector in close_button_selectors:
                try:
                    buttons = driver.find_elements(by, selector)
                    if buttons:
                        close_buttons.extend(buttons)
                        break
                except:
                    continue

            if len(close_buttons) > 0:
                print_lg(f"DEBUG: Found {len(close_buttons)} close buttons. Ensuring modal is closed...")
                for btn in close_buttons:
                    try:
                        if btn.is_displayed():
                            btn.click()
                            buffer(1)

                            # Handle "Discard draft" popup if it appears
                            discard_selectors = [
                                (By.XPATH, "//button[contains(@class, 'artdeco-modal__confirm-btn') or contains(., 'Discard')]"),
                                (By.CSS_SELECTOR, "button[class*='modal'][class*='confirm-btn']"),
                                (By.XPATH, "//button[contains(text(), 'Discard')]"),
                            ]
                            try:
                                for by, sel in discard_selectors:
                                    try:
                                        discard_btn = driver.find_element(by, sel)
                                        discard_btn.click()
                                        print_lg("DEBUG: Discarded draft to close modal")
                                        break
                                    except:
                                        continue
                            except:
                                pass
                    except:
                        pass
            else:
                 print_lg("DEBUG: ⚠️ No Close button found via any selector")
                 
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
    error_message: str = "",
    template_name: str = ""
) -> None:
    '''
    Records sent message or skip reason in CSV file.
    '''
    try:
        # Ensure directory exists
        make_directories([message_history_file])

        # Generate unique message ID
        message_id = str(uuid.uuid4())
        recruiter_id = recruiter_info.get('recruiter_id', '')

        # Determine message type
        if recruiter_info.get('is_free_message'):
            if recruiter_info.get('message_type') == 'connection':
                msg_type = "Free (1st Connection)"
            else:
                msg_type = "Free Message"
        else:
            msg_type = "Skipped - InMail Required"

        # Determine success status and handle SKIP: prefixed error messages
        if skip_reason:
            status = "Skipped"
        elif error_message and error_message.startswith("SKIP: "):
            status = "Skipped"
            skip_reason = error_message[5:]  # Remove "SKIP: " prefix
            error_message = ""
        elif success:
            status = "Sent"
        else:
            status = "Failed"

        # Prepare row data
        row = [
            message_id,
            job_id,
            job_title,
            company_name,
            job_link,
            recruiter_info.get('name', 'Unknown'),
            recruiter_info.get('title', 'Unknown'),
            recruiter_id,
            recruiter_info.get('profile_link', ''),
            msg_type,
            subject,
            message_body,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            status,
            skip_reason,
            error_message,
            template_name,
            '',  # Response Received (empty by default)
            ''   # Response Date (empty by default)
        ]

        # Check if file exists to determine if we need headers
        file_exists = os.path.exists(message_history_file)

        # Write to CSV
        with open(message_history_file, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            # Write header if new file
            if not file_exists:
                headers = [
                    'Message ID', 'Job ID', 'Job Title', 'Company', 'Job Link',
                    'Recruiter Name', 'Recruiter Title', 'Recruiter ID', 'Recruiter Profile Link',
                    'Message Type', 'Subject', 'Message Body', 'Date Sent',
                    'Status', 'Skip Reason', 'Error Message', 'Template Name',
                    'Response Received', 'Response Date'
                ]
                writer.writerow(headers)

            writer.writerow(row)

        print_lg(f"Tracking record saved for {recruiter_info.get('name', 'Unknown')} (ID: {message_id})")

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
    # Check if already applied to job
    if skip_if_already_applied and already_applied:
        return True, "Already applied"

    # Check if already messaged this recruiter
    if recruiter_info['recruiter_id'] in messaged_recruiters:
        return True, "Already contacted this recruiter today"

    # Check if InMail required but we want only free messages
    if skip_inmail_required and not recruiter_info['is_free_message']:
        return True, "InMail Required"

    # Check daily limit
    if check_daily_message_limit():
        return True, "Daily limit reached"

    # Check if can message at all
    if not recruiter_info['can_message']:
        return True, "No message button available"

    return False, ""
