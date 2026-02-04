'''
Author:     Sanjay Nainwal
LinkedIn:   https://www.linkedin.com/in/sanjay-nainwal/

Copyright (C) 2024 Sanjay Nainwal

License:    GNU Affero General Public License
            https://www.gnu.org/licenses/agpl-3.0.en.html

GitHub:     https://github.com/nainwalsanju/Auto_job_applier_linkedIn

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
import time

from config.recruiter_messaging import *
from config.personals import first_name, last_name
from config.questions import years_of_experience
from modules.helpers import print_lg, buffer, make_directories
from modules.bot_logger import (
    log_step, log_html_snapshot, log_action, log_decision, 
    log_error, log_recruiter_action, log_section_separator
)

# Import AI functions conditionally
if use_ai_for_messages:
    from config.secrets import ai_provider, use_AI
    if use_AI:
        from modules.ai.openaiConnections import ai_answer_question
        from modules.ai.deepseekConnections import deepseek_answer_question
        from modules.ai.geminiConnections import gemini_answer_question


# Global variables
messages_sent_today = 0
messaged_recruiters = set()  # Track recruiter IDs and action types to avoid duplicates


def _ensure_modal_closed(driver: WebDriver) -> None:
    '''
    Ensures any open message modal is closed to prevent stuck state.
    '''
    try:
        print_lg("🔒 Attempting to ensure all modals are closed...")
        # Multiple attempts to close any open modals
        for attempt in range(5):
            try:
                # First, try ESC key multiple times
                for _ in range(3):
                    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                    buffer(0.5)

                # Comprehensive list of close button selectors for LinkedIn modals
                close_selectors = [
                    # Message overlay modals
                    "//button[contains(@class, 'msg-overlay-bubble-header__control')]",
                    "//button[contains(@class, 'msg-overlay-bubble-header__close')]",
                    "//button[contains(@aria-label, 'Close message')]",
                    "//button[contains(@data-test-id, 'close-button')]",

                    # Artdeco modals
                    "//button[contains(@class, 'artdeco-modal__dismiss')]",
                    "//button[contains(@aria-label, 'Close')]",
                    "//button[contains(@aria-label, 'Dismiss')]",

                    # Generic close buttons
                    "//button[contains(@class, 'artdeco-button--circle') and contains(@aria-label, 'Close')]",
                    "//button[contains(@type, 'button') and contains(@aria-label, 'Close')]",

                    # Message-specific modals
                    "//div[contains(@class, 'msg-overlay-modal')]//button[contains(@aria-label, 'Close')]",
                    "//div[contains(@class, 'msg-form-modal')]//button[contains(@aria-label, 'Close')]",

                    # Overflow menu close
                    "//button[contains(@aria-label, 'Close menu')]",
                ]

                modal_closed = False
                # Skip extensive cleanup if dry run or minimal cleanup requested
                # Reduced attempts/waits for speed
                modal_closed = False
                for selector in close_selectors:
                    try:
                        # Use a very short wait for finding close buttons
                        close_btns = driver.find_elements(By.XPATH, selector)
                        if close_btns:
                           for close_btn in close_btns:
                                if close_btn.is_displayed():
                                    close_btn.click()
                                    buffer(0.5)
                                    modal_closed = True
                    except:
                        pass
                
                if modal_closed:
                    print_lg(f"Modal closed on attempt {attempt + 1}")
                    return

                # Handle "Discard draft" confirmation dialogs
                discard_selectors = [
                    "//button[contains(@class, 'artdeco-modal__confirm-btn')]",
                    "//button[contains(., 'Discard')]",
                    "//button[contains(@aria-label, 'Discard')]",
                    "//button[contains(text(), 'Discard draft')]"
                ]

                for selector in discard_selectors:
                    try:
                        discard_btns = driver.find_elements(By.XPATH, selector)
                        for discard_btn in discard_btns:
                            if discard_btn.is_displayed() and discard_btn.is_enabled():
                                discard_btn.click()
                                buffer(1)
                                modal_closed = True
                                break
                    except Exception:
                        continue

                # Check if any modals are still open by looking for modal backdrops
                try:
                    modal_backdrops = driver.find_elements(By.XPATH,
                        "//div[contains(@class, 'artdeco-modal') or contains(@class, 'msg-overlay') or contains(@class, 'modal-backdrop')]")
                    if not modal_backdrops:
                        break  # No more modals found
                except Exception:
                    break  # No modals found

                if modal_closed:
                    print_lg(f"Modal closed on attempt {attempt + 1}")
                    buffer(1)
                else:
                    buffer(1)  # Wait before next attempt

            except Exception as e:
                print_lg(f"Modal close attempt {attempt + 1} failed: {e}")
                buffer(1)
                continue

        # Final verification - try to detect any remaining message-related modals
        try:
            message_modals = driver.find_elements(By.XPATH,
                "//div[contains(@class, 'msg-connections-typeahead') or contains(@class, 'msg-form__contenteditable') or contains(@class, 'msg-overlay-modal')]")
            
            # Filter for only VISIBLE modals
            visible_modals = [m for m in message_modals if m.is_displayed()]
            
            if visible_modals:
                print_lg(f"⚠️ WARNING: {len(visible_modals)} visible message modal(s) may still be open, forcing additional close attempts")
                # Force close with JavaScript - more aggressive
                driver.execute_script("""
                    // Hide all modal overlays
                    var overlays = document.querySelectorAll('[class*="overlay"], [class*="backdrop"], [class*="modal"]');
                    for (var i = 0; i < overlays.length; i++) {
                        overlays[i].style.display = 'none';
                        overlays[i].style.visibility = 'hidden';
                        overlays[i].remove();
                    }

                    // Click all possible close buttons
                    var closeSelectors = [
                        'button[aria-label*="Close"]',
                        'button[aria-label*="Dismiss"]',
                        'button[class*="close"]',
                        'button[class*="dismiss"]',
                        'button[aria-label*="close"]',
                        'button[data-test-id*="close"]'
                    ];

                    for (var s = 0; s < closeSelectors.length; s++) {
                        var buttons = document.querySelectorAll(closeSelectors[s]);
                        for (var i = 0; i < buttons.length; i++) {
                            if (buttons[i].offsetParent !== null) {
                                buttons[i].click();
                            }
                        }
                    }

                    // Send ESC key multiple times
                    var escEvent = new KeyboardEvent('keydown', {key: 'Escape', keyCode: 27, which: 27, bubbles: true});
                    for (var i = 0; i < 5; i++) {
                        document.dispatchEvent(escEvent);
                    }
                """)
                buffer(3)
        except Exception as e:
            print_lg(f"❌ Final modal cleanup error: {e}")

    except Exception as e:
        print_lg(f"❌ Critical error in modal closing: {e}")

    # Final check - log any remaining VISIBLE modals only
    try:
        remaining_modals = driver.find_elements(By.XPATH, "//div[contains(@class, 'artdeco-modal') or contains(@class, 'msg-overlay-conversation-bubble--is-active') or contains(@class, 'modal-backdrop')]")
        # Only count actually visible modals
        visible_modals = [m for m in remaining_modals if m.is_displayed()]
        if visible_modals:
            print_lg(f"⚠️ Warning: {len(visible_modals)} visible modal(s) may still be present")
        else:
            print_lg("✅ Modal cleanup completed successfully")
    except Exception as e:
        print_lg(f"Error checking for remaining modals: {e}")


def find_recruiters_on_job_page(driver: WebDriver) -> list[dict]:
    '''
    Detects all potential messaging targets from the job posting page.
    Returns a list of dictionaries with recruiter/connection details.

    Returns list of:
    {
        'name': str,
        'title': str,
        'profile_link': str,
        'recruiter_id': str,
        'can_message': bool,
        'is_free_message': bool,  # True if free message, False if InMail required
        'button_type': str,  # 'message', 'connect', or 'none'
        'section': str  # 'hiring_team' or 'connections'
    }
    '''
    recruiters = []

    try:
        print_lg("Starting recruiter search...")
        log_section_separator("RECRUITER SEARCH")
        log_step("Starting recruiter search on job page")
        log_html_snapshot(driver, "recruiter_search_start", "Initial state before searching for recruiters")

        # Ensure no modals are open from previous operations
        _ensure_modal_closed(driver)
        log_action("Modal cleanup", "Ensured no stray modals are open")

        # STEP 1: Find "Meet the hiring team" section
        hiring_team_section = None
        try:
            hiring_team_header = driver.find_element(By.XPATH,
                "//h2[contains(@class, 'text-heading-medium') and contains(normalize-space(.), 'Meet the hiring team')]")
            hiring_team_section = hiring_team_header.find_element(By.XPATH,
                "./parent::div[contains(@class, 'artdeco-card')]")
            print_lg("Found 'Meet the hiring team' section")

            # Extract recruiter from hiring team section
            recruiter_info = _extract_recruiter_from_section(driver, hiring_team_section, 'hiring_team')
            if recruiter_info:
                recruiters.append(recruiter_info)

        except NoSuchElementException:
            print_lg("No 'Meet the hiring team' section found on this job posting.")

        # STEP 2: Find "People you can reach out to" section (always check, regardless of hiring team)
        try:
            connections_section = driver.find_element(By.XPATH,
                "//div[contains(@class, 'job-details-people-who-can-help__section--two-pane') and contains(@class, 'artdeco-card')]")
            print_lg("Found 'People you can reach out to' section")

            # Extract all connections from this section
            connections_list = find_connections_in_help_section(driver, connections_section)
            recruiters.extend(connections_list)

        except NoSuchElementException:
            print_lg("No 'People you can reach out to' section found on this job posting.")

        # STEP 3: Check for "Show all" button to expand and get more connections
        # This opens a modal with potentially many more 1st-degree connections
        try:
            modal_connections = find_connections_in_show_all_modal(driver)
            if modal_connections:
                # Deduplicate by recruiter_id to avoid messaging same person twice
                existing_ids = {r.get('recruiter_id') for r in recruiters}
                new_connections = [c for c in modal_connections if c.get('recruiter_id') not in existing_ids]
                recruiters.extend(new_connections)
                print_lg(f"Added {len(new_connections)} new connections from 'Show all' modal")
        except Exception as e:
            print_lg(f"⚠️ Error checking 'Show all' modal: {e}")

        print_lg(f"Found {len(recruiters)} potential messaging targets")
        return recruiters

    except Exception as e:
        print_lg(f"Error finding recruiters: {e}")
        return []


def _extract_recruiter_from_section(driver: WebDriver, section: WebElement, section_type: str) -> dict | None:
    '''
    Extracts recruiter information from a given section (hiring team or connection card).
    '''
    recruiter_info = {'section': section_type}

    # STEP 1: Find profile link
    try:
        recruiter_link = section.find_element(By.XPATH, ".//a[contains(@href, '/in/')]")
        recruiter_info['profile_link'] = recruiter_link.get_attribute('href')

        # Extract recruiter ID from profile link
        try:
             recruiter_id = recruiter_info['profile_link'].split('/in/')[-1].split('/')[0].split('?')[0]
             recruiter_info['recruiter_id'] = recruiter_id
        except:
             recruiter_info['recruiter_id'] = "unknown"
    except NoSuchElementException:
        recruiter_info['profile_link'] = ""
        recruiter_info['recruiter_id'] = "unknown"

    # STEP 2: Find name - ROBUST EXTRACTION
    # LinkedIn splits names across nested spans with aria-hidden, so we try multiple strategies
    recruiter_info['name'] = "Unknown"
    
    name_selectors = [
        # Priority 1: Get text from profile link anchor (most stable)
        ".//a[contains(@href, '/in/')]",
        # Priority 2: Hiring team specific selectors
        ".//span[contains(@class, 'jobs-poster__name')]",
        ".//div[contains(@class, 'hirer-card__hirer-information')]//span[contains(@class, 'text-heading')]",
        # Priority 3: Entity lockup title (common in modals/cards)
        ".//div[contains(@class, 'artdeco-entity-lockup__title')]//strong",
        ".//div[contains(@class, 'artdeco-entity-lockup__title')]//span[contains(@class, 'artdeco-entity-lockup__title')]",
        # Priority 4: Generic strong/heading elements
        ".//strong",
        ".//span[@aria-hidden='true']",
    ]
    
    for selector in name_selectors:
        try:
            name_element = section.find_element(By.XPATH, selector)
            name_text = name_element.text.strip()
            # Validate: names should be at least 2 chars, not contain obvious non-name patterns
            if name_text and len(name_text) >= 2 and not name_text.startswith('http'):
                recruiter_info['name'] = name_text.split('\n')[0].strip()  # Take first line only
                break
        except NoSuchElementException:
            continue
    
    # Fallback: Try extracting name from button aria-label if still Unknown
    if recruiter_info['name'] == "Unknown":
        try:
            # Look for Message/Connect button aria-label like "Message John Doe"
            btn = section.find_element(By.XPATH, 
                ".//button[contains(@aria-label, 'Message') or contains(@aria-label, 'Connect')]")
            aria_label = btn.get_attribute('aria-label') or ""
            # Extract name by removing "Message " or "Connect " prefix
            for prefix in ['Message ', 'Connect ']:
                if aria_label.startswith(prefix):
                    recruiter_info['name'] = aria_label[len(prefix):].strip()
                    print_lg(f"📝 Extracted name from button aria-label: {recruiter_info['name']}")
                    break
        except:
            pass

    # STEP 3: Find title
    try:
        if section_type == 'hiring_team':
            title_element = section.find_element(By.XPATH,
                ".//div[contains(@class, 'linked-area')]//div[contains(@class, 'text-body-small')]")
        else:  # connections section
            title_element = section.find_element(By.XPATH,
                ".//div[contains(@class, 'artdeco-entity-lockup__subtitle')]")
        recruiter_info['title'] = title_element.text.strip()
    except NoSuchElementException:
        recruiter_info['title'] = "Unknown Title"

    # STEP 4: Check message capability and button type
    message_capability = check_message_capability(driver, section)
    recruiter_info.update(message_capability)

    print_lg(f"Found {section_type} target: {recruiter_info['name']} ({recruiter_info['title']}) - "
            f"Button: {recruiter_info.get('button_type', 'none')}, Can Message: {recruiter_info['can_message']}, Free: {recruiter_info['is_free_message']}")

    return recruiter_info


def find_connections_in_help_section(driver: WebDriver, connections_section: WebElement) -> list[dict]:
    '''
    Extracts all connection targets from the "People you can reach out to" section.
    '''
    connections = []

    try:
        # Find all individual connection cards within the section
        connection_cards = connections_section.find_elements(By.XPATH,
            ".//div[contains(@class, 'artdeco-entity-lockup') and .//a[contains(@href, '/in/')]]")

        for card in connection_cards:
            recruiter_info = _extract_recruiter_from_section(driver, card, 'connections')
            if recruiter_info:
                connections.append(recruiter_info)

    except Exception as e:
        print_lg(f"Error extracting connections from help section: {e}")

    return connections


def find_connections_in_show_all_modal(driver: WebDriver) -> list[dict]:
    '''
    Clicks the "Show all" button to open the connections modal and extracts
    all 1st-degree connections who can be messaged for free.
    
    Returns list of connection dictionaries with messaging capability info.
    '''
    connections = []
    modal_opened = False
    
    try:
        # STEP 1: Find and click the "Show all" button
        # It's typically inside the "People you can reach out to" section
        show_all_selectors = [
            "//button[contains(@class, 'artdeco-button') and .//span[text()='Show all']]",
            "//a[contains(@class, 'inline-block')]//button[.//span[text()='Show all']]",
            "//div[contains(@class, 'job-details-people-who-can-help')]//button[.//span[text()='Show all']]"
        ]
        
        show_all_btn = None
        for selector in show_all_selectors:
            try:
                buttons = driver.find_elements(By.XPATH, selector)
                # Get the first visible 'Show all' button
                for btn in buttons:
                    if btn.is_displayed():
                        show_all_btn = btn
                        break
                if show_all_btn:
                    break
            except:
                continue
        
        if not show_all_btn:
            print_lg("ℹ️ No 'Show all' button found - skipping expanded connections")
            return connections
        
        print_lg("🔍 Found 'Show all' button, clicking to expand connections...")
        
        # Scroll button into view and click
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", show_all_btn)
        buffer(0.5)
        
        try:
            show_all_btn.click()
        except:
            driver.execute_script("arguments[0].click();", show_all_btn)
        
        buffer(1.5)  # Wait for modal to load
        modal_opened = True
        
        # STEP 2: Find the opened modal
        modal = None
        modal_selectors = [
            "//div[contains(@class, 'job-details-connections-modal__modal-wrapper')]",
            "//div[@role='dialog' and contains(@class, 'artdeco-modal')]"
        ]
        
        for selector in modal_selectors:
            try:
                modal = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                print_lg("✅ Opened 'In your network' modal")
                break
            except:
                continue
        
        if not modal:
            print_lg("⚠️ Could not find connections modal after clicking 'Show all'")
            return connections
        
        # STEP 3: Extract all connection cards from the modal
        # Look for cards with "Message" buttons (1st degree - free messaging)
        connection_cards = modal.find_elements(By.XPATH,
            ".//div[contains(@class, 'artdeco-entity-lockup') and .//button[.//span[text()='Message']]]")
        
        print_lg(f"📋 Found {len(connection_cards)} connections with Message button in modal")
        
        for card in connection_cards:
            try:
                conn_info = {'section': 'modal_connections'}
                
                # Extract name
                try:
                    name_elem = card.find_element(By.XPATH, 
                        ".//div[contains(@class, 'artdeco-entity-lockup__title')]//strong")
                    conn_info['name'] = name_elem.text.strip()
                except:
                    conn_info['name'] = "Unknown"
                
                # Extract title/subtitle
                try:
                    title_elem = card.find_element(By.XPATH,
                        ".//div[contains(@class, 'artdeco-entity-lockup__subtitle')]")
                    conn_info['title'] = title_elem.text.strip()
                except:
                    conn_info['title'] = "Unknown Title"
                
                # Extract profile link
                try:
                    link_elem = card.find_element(By.XPATH, ".//a[contains(@href, '/in/')]")
                    conn_info['profile_link'] = link_elem.get_attribute('href')
                    conn_info['recruiter_id'] = conn_info['profile_link'].split('/in/')[-1].split('/')[0].split('?')[0]
                except:
                    conn_info['profile_link'] = ""
                    conn_info['recruiter_id'] = "unknown"
                
                # Extract connection degree
                degree = "1st"  # Default to 1st since they have Message button
                try:
                    degree_elem = card.find_element(By.XPATH,
                        ".//span[contains(@class, 'artdeco-entity-lockup__degree')]")
                    degree_text = degree_elem.text.strip()
                    if '1st' in degree_text:
                        degree = "1st"
                    elif '2nd' in degree_text:
                        degree = "2nd"
                    elif '3rd' in degree_text:
                        degree = "3rd"
                except:
                    pass
                
                conn_info['connection_degree'] = degree
                
                # If they have a Message button, they're 1st degree = free messaging
                conn_info['can_message'] = True
                conn_info['is_free_message'] = (degree == "1st")
                conn_info['button_type'] = 'message'
                conn_info['message_type'] = 'connection' if degree == "1st" else 'inmail'
                
                # Only add if it's a free message (1st degree)
                if conn_info['is_free_message'] and conn_info['name'] != "Unknown":
                    print_lg(f"   ✅ Modal connection: {conn_info['name']} ({degree}) - Free Message")
                    connections.append(conn_info)
                else:
                    print_lg(f"   ⏭️ Skipping modal connection: {conn_info['name']} ({degree}) - Not free")
                    
            except Exception as e:
                print_lg(f"   ⚠️ Error parsing connection card: {e}")
                continue
        
        print_lg(f"📊 Total free messageable connections from modal: {len(connections)}")
        
    except Exception as e:
        print_lg(f"⚠️ Error processing 'Show all' modal: {e}")
    
    finally:
        # STEP 4: Close the modal if it was opened
        if modal_opened:
            try:
                close_btn = driver.find_element(By.XPATH,
                    "//div[contains(@class, 'artdeco-modal')]//button[@aria-label='Dismiss' or contains(@class, 'artdeco-modal__dismiss')]")
                close_btn.click()
                buffer(0.5)
                print_lg("✅ Closed connections modal")
            except:
                # Try ESC key as fallback
                try:
                    from selenium.webdriver.common.keys import Keys
                    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                    buffer(0.5)
                except:
                    pass
    
    return connections


def check_message_capability(driver: WebDriver, section: WebElement) -> dict:
    '''
    Checks if target can be messaged and what type of interaction is available.

    Returns:
    {
        'can_message': bool,
        'is_free_message': bool,  # True if free, False if InMail/connect required
        'message_type': str,  # 'free', 'inmail', 'connection', 'connect', or 'unavailable'
        'button_type': str  # 'message', 'connect', or 'none'
    }
    '''
    result = {
        'can_message': False,
        'is_free_message': False,
        'message_type': 'unavailable',
        'button_type': 'none',
        'has_message_button': False,
        'has_connect_button': False
    }

    try:
        # STEP 1: Scan for ALL types of buttons first
        message_button = None
        connect_button = None
        
        try:
            message_button = section.find_element(By.XPATH,
                ".//button[contains(normalize-space(.), 'Message') or contains(@aria-label, 'Message')]")
            result['can_message'] = True
            result['has_message_button'] = True
        except NoSuchElementException:
            pass
            
        try:
            connect_button = section.find_element(By.XPATH,
                ".//button[contains(normalize-space(.), 'Connect') or contains(@aria-label, 'Connect')]")
            result['can_message'] = True
            result['has_connect_button'] = True
        except NoSuchElementException:
            pass
            
        if not message_button and not connect_button:
            return result

        # STEP 2: Determine Connection Degree
        degree_text = ""
        try:
            connection_degree = section.find_element(By.XPATH, ".//span[contains(@class, 'hirer-card__connection-degree')]")
            degree_text = connection_degree.text.strip()
        except:
            pass

        # STEP 3: Prioritization Logic
        # Case A: 1st Degree Connection -> Always Message (Free)
        if '1st' in degree_text and message_button:
            result['button_type'] = 'message'
            result['is_free_message'] = True
            result['message_type'] = 'connection'
            return result

        # Case B: Connect Button Exists (2nd/3rd) -> Safer to use Connect + Note (Free)
        # We prioritize Connect over Message for non-1st because Message is often InMail
        if connect_button:
            result['button_type'] = 'connect'
            result['is_free_message'] = True
            result['message_type'] = 'connect'
            return result

        # Case C: Only Message Button Exists (2nd/3rd or Open Profile or InMail)
        if message_button:
            result['button_type'] = 'message'
            
            # Check for explicit premium/lock indicators on the button
            is_locked = False
            try:
                # 1. Check classes
                button_classes = message_button.get_attribute('class').lower()
                if 'premium' in button_classes or 'locked' in button_classes:
                    is_locked = True
                
                # 2. Check for lock icon SVG inside button
                if not is_locked:
                    try:
                        message_button.find_element(By.XPATH, ".//*[contains(@data-test-icon, 'lock')]")
                        is_locked = True
                    except:
                        pass
                
                # 3. Check aria-label for "InMail"
                if not is_locked:
                    aria_label = message_button.get_attribute('aria-label')
                    if aria_label and 'inmail' in aria_label.lower():
                        is_locked = True
            except:
                pass

            if is_locked:
                result['is_free_message'] = False
                result['message_type'] = 'inmail'
            else:
                # IMPORTANT: Without a lock icon, we CANNOT reliably determine if it's free.
                # LinkedIn doesn't show InMail indicators until AFTER clicking the button.
                # For safety, we mark it as 'unknown' - the post-click check will verify.
                # We still allow the attempt, but is_free_message = False means we expect
                # the post-click verification to confirm it's actually free.
                result['is_free_message'] = False  # Conservative - assume InMail until proven free
                result['message_type'] = 'unknown'  # Let post-click determine
                print_lg(f"⚠️ Pre-click check: Cannot determine if message is free (no 1st degree indicator)")
                
            return result

        return result

    except Exception as e:
        print_lg(f"Error checking message capability: {e}")
        return result


def _trim_to_limit(text: str, limit: int) -> str:
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    trimmed = text[: max(0, limit - 3)].rstrip()
    return f"{trimmed}..."


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
Job Description: {job_description[:1000]}
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

            print_lg("AI-generated personalization completed")

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

    # Log the AI generated message for verification
    if use_ai_for_messages:
        print_lg("\n================= AI GENERATED MESSAGE =================")
        print_lg(f"SUBJECT: {subject}")
        print_lg(f"BODY:\n{body}")
        print_lg("========================================================\n")

    # Ensure message is within LinkedIn limits
    # Subject: 200 chars, Body: 1900 chars for regular messages
    subject = _trim_to_limit(subject, 200)
    body = _trim_to_limit(body, 1900)

    return subject, body


def generate_connection_note(
    aiClient,
    recruiter_info: dict,
    job_description: str,
    job_title: str,
    company_name: str,
) -> str:
    recruiter_name = recruiter_info.get('name', 'Recruiter').split()[0]
    your_name = f"{first_name} {last_name}"
    personalized_intro = ""
    why_interested = ""

    if use_ai_for_messages and use_AI and aiClient:
        try:
            intro_prompt = f"""Write a very short friendly intro (1 sentence, <= 20 words) for a LinkedIn connection note.

Job Title: {job_title}
Company: {company_name}
Job Description: {job_description[:800]}
Candidate Experience: {years_of_experience} years in backend development with Java"""

            if ai_provider.lower() == "openai":
                personalized_intro = ai_answer_question(aiClient, intro_prompt, question_type="text")
            elif ai_provider.lower() == "deepseek":
                personalized_intro = deepseek_answer_question(aiClient, intro_prompt, question_type="text")
            elif ai_provider.lower() == "gemini":
                personalized_intro = gemini_answer_question(aiClient, intro_prompt, question_type="text")

            interest_prompt = f"""Write 1 short sentence (<= 20 words) explaining interest in this role/company for a LinkedIn connection note.

Job Title: {job_title}
Company: {company_name}"""

            if ai_provider.lower() == "openai":
                why_interested = ai_answer_question(aiClient, interest_prompt, question_type="text")
            elif ai_provider.lower() == "deepseek":
                why_interested = deepseek_answer_question(aiClient, interest_prompt, question_type="text")
            elif ai_provider.lower() == "gemini":
                why_interested = gemini_answer_question(aiClient, interest_prompt, question_type="text")

            personalized_intro = personalized_intro.strip().replace("\n", " ")
            why_interested = why_interested.strip().replace("\n", " ")
        except Exception as e:
            print_lg(f"Failed to generate AI connection note personalization: {e}")
            personalized_intro = ""
            why_interested = ""

    note = connection_note_template.format(
        recruiter_name=recruiter_name,
        job_title=job_title,
        company_name=company_name,
        your_name=your_name,
        years_of_experience=years_of_experience,
        personalized_intro=personalized_intro,
        why_interested=why_interested,
        key_skills="Java, Spring Boot, Microservices",
    ).strip()

    note = " ".join(note.split())
    return _trim_to_limit(note, connection_note_max_chars)


def send_message_to_recruiter(
    driver: WebDriver,
    recruiter_info: dict,
    message_init_data: dict
) -> tuple[bool, str]:
    '''
    Sends message to the recruiter via LinkedIn.
    Returns (success: bool, error_message: str)

    STEP 1: Capture initial state
    STEP 2: Click message button (may open inline modal OR new window)
    STEP 3: Detect messaging context (inline modal vs new window)
    STEP 4: Compose message in detected context
    STEP 5: Send message
    STEP 6: Cleanup - always execute
    '''
    global messages_sent_today

    # Log the messaging attempt
    log_section_separator(f"MESSAGE TO: {recruiter_info.get('name', 'Unknown')}")
    log_recruiter_action(recruiter_info.get('name', 'Unknown'), 
                         f"Starting message attempt | Section: {recruiter_info.get('section')} | Button: {recruiter_info.get('button_type')}")
    log_html_snapshot(driver, f"msg_start_{recruiter_info.get('name', 'unknown')[:20]}", 
                      f"Before messaging {recruiter_info.get('name')}")

    if dry_run_mode:
        print_lg(f"[DRY RUN] Would send message to {recruiter_info['name']}")
        print_lg(f"📝 Message Subject: {subject}")
        print_lg(f"📝 Message Body:\n{message_body}")
        log_decision("DRY RUN", f"Would send message to {recruiter_info['name']}")
        return True, "Dry run - message not actually sent"

    # STEP 1: Capture initial state
    original_window = driver.current_window_handle
    pre_click_handles = set(driver.window_handles)
    log_step("Captured initial browser state", f"Window: {original_window[:30]}... | Handles: {len(pre_click_handles)}")
    
    # Initialize variables for cleanup scope
    messaging_window_handle = None
    is_new_window = False

    # Ensure no stray modals are open from previous operations
    # CRITICAL: Close existing messaging bubbles to prevent 'full bar' issue
    # LinkedIn allows max 3-4 bubbles; if full, new Message click won't work
    # ALSO: Open bubbles can physically block the Message button click
    print_lg("🧹 Closing any existing messaging bubbles...")
    try:
        # Close conversation bubbles
        conversation_bubbles = driver.find_elements(By.XPATH,
            "//aside[contains(@class,'msg-overlay-conversation-bubble')]//button[contains(@aria-label,'Close')] | "
            "//*[contains(@class,'msg-overlay-conversation-bubble')]//button[contains(@aria-label,'Close')]")
        for bubble_close in conversation_bubbles[:5]:
            try:
                if bubble_close.is_displayed():
                    bubble_close.click()
                    buffer(0.3)
                    print_lg("✅ Closed a conversation bubble")
            except:
                pass
        
        # Close the messaging list bubble (this is what blocks clicks!)
        list_bubbles = driver.find_elements(By.XPATH,
            "//aside[contains(@class,'msg-overlay-list-bubble')]//button[contains(@aria-label,'Close')] | "
            "//*[contains(@class,'msg-overlay-list-bubble')]//button[contains(@aria-label,'Close')]")
        for bubble_close in list_bubbles[:3]:
            try:
                if bubble_close.is_displayed():
                    bubble_close.click()
                    buffer(0.3)
                    print_lg("✅ Closed a list bubble")
            except:
                pass
        
        # JavaScript fallback - force hide any remaining bubbles
        try:
            driver.execute_script("""
                // Hide all messaging overlays
                var bubbles = document.querySelectorAll('[class*="msg-overlay"]');
                for (var i = 0; i < bubbles.length; i++) {
                    if (bubbles[i].classList.contains('msg-overlay-list-bubble') || 
                        bubbles[i].classList.contains('msg-overlay-conversation-bubble')) {
                        bubbles[i].style.display = 'none';
                    }
                }
            """)
            print_lg("✅ JavaScript cleanup executed")
        except:
            pass
            
    except Exception as e:
        print_lg(f"⚠️ Bubble closing warning: {e}")
    
    _ensure_modal_closed(driver)
    buffer(1)

    # STEP 2: Click message/connect button
    try:
        current_name = recruiter_info.get('name', '').split()[0]
        section_type = recruiter_info.get('section', '')
        original_button_type = recruiter_info.get('button_type')
        
        # SPECIAL CASE: Modal connections require re-opening the modal first
        if section_type == 'modal_connections':
            print_lg(f"🔍 Re-opening 'Show all' modal to message {current_name}...")
            
            # Click Show all button to re-open modal
            show_all_selectors = [
                "//button[contains(@class, 'artdeco-button') and .//span[text()='Show all']]",
                "//a[contains(@class, 'inline-block')]//button[.//span[text()='Show all']]",
                "//div[contains(@class, 'job-details-people-who-can-help')]//button[.//span[text()='Show all']]"
            ]
            
            show_all_btn = None
            for selector in show_all_selectors:
                try:
                    buttons = driver.find_elements(By.XPATH, selector)
                    for btn in buttons:
                        if btn.is_displayed():
                            show_all_btn = btn
                            break
                    if show_all_btn:
                        break
                except:
                    continue
            
            if not show_all_btn:
                return False, f"Could not find 'Show all' button to message modal connection {current_name}"
            
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", show_all_btn)
            buffer(0.5)
            try:
                show_all_btn.click()
            except:
                driver.execute_script("arguments[0].click();", show_all_btn)
            buffer(1.5)
            
            # Wait for modal to open
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'job-details-connections-modal__modal-wrapper')]"))
                )
                print_lg("✅ Re-opened modal for messaging")
            except:
                return False, f"Could not re-open modal for {current_name}"
        
        # 2. Find button relative to the recruiter's name (Most Robust)
        # Instead of finding a container first (which might be too narrow, like just the <a> tag),
        # we search for a button that shares a common ancestor with the recruiter's name.
        
        print_lg(f"🔍 Searching for button anchored to name: '{current_name}'")
        
        # STRATEGY: Use recruiter_id from profile_link to find button (most reliable)
        # LinkedIn names can be split across spans making text matching fragile
        recruiter_id = recruiter_info.get('recruiter_id', '')
        profile_link = recruiter_info.get('profile_link', '')
        button_type = recruiter_info.get('button_type', 'message')
        
        action_button = None
        
        # APPROACH 1: Find button via profile link/recruiter_id (MOST RELIABLE)
        # This finds the card container containing the profile link, then finds the button within it
        if recruiter_id and recruiter_id != "unknown":
            profile_based_xpaths = []
            
            if button_type == 'message':
                profile_based_xpaths = [
                    # Find button in same container as profile link
                    f"//a[contains(@href, '/in/{recruiter_id}')]/ancestor::*[contains(@class,'artdeco-entity-lockup') or contains(@class,'hirer-card') or contains(@class,'display-flex')][1]//button[contains(@aria-label, 'Message') or .//span[normalize-space()='Message'] or contains(normalize-space(.), 'Message')]",
                    # Hiring team section specifically
                    f"//section[.//h2[contains(text(),'Meet the hiring team')]]//a[contains(@href, '/in/{recruiter_id}')]/ancestor::div[1]//button[contains(@aria-label, 'Message') or contains(normalize-space(.), 'Message')]",
                    # Modal connections
                    f"//div[@role='dialog']//a[contains(@href, '/in/{recruiter_id}')]/ancestor::*[contains(@class,'artdeco-entity-lockup')][1]//button[contains(normalize-space(.), 'Message')]",
                ]
            elif button_type == 'connect':
                profile_based_xpaths = [
                    f"//a[contains(@href, '/in/{recruiter_id}')]/ancestor::*[contains(@class,'artdeco-entity-lockup') or contains(@class,'hirer-card') or contains(@class,'display-flex')][1]//button[contains(@aria-label, 'Connect') or .//span[normalize-space()='Connect'] or contains(normalize-space(.), 'Connect')]",
                ]
            
            for xpath in profile_based_xpaths:
                try:
                    action_button = driver.find_element(By.XPATH, xpath)
                    print_lg(f"✅ Found button via profile ID: /in/{recruiter_id}")
                    break
                except:
                    continue
        
        # APPROACH 2: Name-based matching (fallback, less reliable due to split spans)
        if not action_button:
            name_clean = current_name
            name_based_xpaths = []
            
            if button_type == 'message':
                name_based_xpaths = [
                    # Modal-specific
                    f"//div[contains(@class, 'job-details-connections-modal')]//div[contains(., '{name_clean}')]//button[contains(normalize-space(.), 'Message')]",
                    f"//div[@role='dialog']//div[contains(., '{name_clean}')]//button[contains(normalize-space(.), 'Message')]",
                    # Hiring team section - find by section context, not name
                    "//section[.//h2[contains(text(),'Meet the hiring team')]]//button[contains(@aria-label, 'Message') or contains(normalize-space(.), 'Message')]",
                    # Generic containers with name
                    f"//*[contains(., '{name_clean}') and (contains(@class, 'artdeco-entity-lockup') or contains(@class, 'hirer-card') or contains(@class, 'display-flex'))]//button[contains(normalize-space(.), 'Message')]",
                ]
            elif button_type == 'connect':
                name_based_xpaths = [
                    "//section[.//h2[contains(text(),'Meet the hiring team')]]//button[contains(@aria-label, 'Connect') or contains(normalize-space(.), 'Connect')]",
                    f"//*[contains(., '{name_clean}') and (contains(@class, 'artdeco-entity-lockup') or contains(@class, 'hirer-card'))]//button[contains(normalize-space(.), 'Connect')]",
                ]
            
            for xpath in name_based_xpaths:
                try:
                    action_button = driver.find_element(By.XPATH, xpath)
                    print_lg(f"✅ Found button via name-based fallback")
                    break
                except:
                    continue
        
        # APPROACH 3: ARIA-label direct lookup (uses button's own label)
        if not action_button:
            # Try finding button by aria-label containing the recruiter name
            aria_xpaths = []
            if button_type == 'message':
                aria_xpaths = [
                    f"//button[contains(@aria-label, 'Message {current_name}')]",
                    f"//button[contains(@aria-label, 'Message') and contains(@aria-label, '{current_name.split()[0]}')]",
                    # Last resort: any visible Message button in the hiring team / connections area
                    "//div[contains(@class, 'job-details-people-who-can-help') or contains(@class, 'hirer-card')]//button[contains(normalize-space(.), 'Message')]",
                ]
            elif button_type == 'connect':
                aria_xpaths = [
                    f"//button[contains(@aria-label, 'Connect') and contains(@aria-label, '{current_name.split()[0]}')]",
                    "//div[contains(@class, 'hirer-card')]//button[contains(normalize-space(.), 'Connect')]",
                ]
            
            for xpath in aria_xpaths:
                try:
                    action_button = driver.find_element(By.XPATH, xpath)
                    print_lg(f"✅ Found button via aria-label lookup")
                    break
                except:
                    continue

        if not action_button:
             raise Exception(f"Could not find '{button_type}' button for recruiter '{current_name}' (ID: {recruiter_id})")

        print_lg(f"🖱️  Clicking {recruiter_info['button_type']} button (Safe Scope)...")
        
        # Scroll to ensure visibility
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", action_button)
        buffer(1)
        action_button.click()
        buffer(2)

        
    except Exception as e:
        return False, f"Failed to click {recruiter_info['button_type']} button: {e}"

    # STEP 3: Handle specific flows (Message vs Connect)
    
    # --- FLOW A: CONNECT WITH NOTE ---
    if recruiter_info['button_type'] == 'connect':
        try:
            print_lg("⏳ Waiting for Connect modal...")
            # Wait for the 'Add a note' modal
            modal_xpath = "//div[contains(@class, 'artdeco-modal') and contains(., 'Invite')]"
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, modal_xpath)))
            
            # Check if we need to click "Add a note"
            try:
                print_lg("�️  Clicking 'Add a note'...")
                add_note_btn = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Add a note')]")
                add_note_btn.click()
                buffer(1)
            except NoSuchElementException:
                # Does logic allow sending without note? Only if 'Add a note' is missing (already open?)
                print_lg("ℹ️ 'Add a note' button not found, checking if text area is already visible")

            # Generate connection note (personalized) if not provided
            aiClient = message_init_data.get('aiClient')
            job_description = message_init_data.get('job_description', '')
            job_title = message_init_data.get('job_title', '')
            company_name = message_init_data.get('company_name', '')
            message_body = message_init_data.get('message_body', '')
            if not message_body:
                message_body = generate_connection_note(
                    aiClient=aiClient,
                    recruiter_info=recruiter_info,
                    job_description=job_description,
                    job_title=job_title,
                    company_name=company_name,
                )

            # Type message
            print_lg("✍️  Typing connection note...")
            try:
                note_area = driver.find_element(By.ID, "custom-message")
                note_area.clear()
                note_area.send_keys(message_body)
                buffer(0.3)
                entered_text = note_area.get_attribute("value") or ""
                if len(entered_text.strip()) < len(message_body) * 0.5:
                    print_lg("⚠️ Note field insert check failed; retrying with JS + send_keys")
                    driver.execute_script("arguments[0].value = '';", note_area)
                    note_area.send_keys(message_body)
                    buffer(0.3)
            except NoSuchElementException:
                return False, "Could not find custom message text area for connection"
            
            # Send (or Verify for Dry Run)
            try:
                send_btn = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Send invitation')]")
            except NoSuchElementException:
                return False, "Could not find 'Send invitation' button"
            
            if dry_run_mode:
                print_lg("✅ [DRY RUN] Would click 'Send invitation'")
                # Close modal to clean up
                try: driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Dismiss')]").click()
                except: pass
                return True, "Dry run - connection note not sent"
            
            print_lg("📤 Sending invitation...")
            send_btn.click()
            buffer(2)
            
            messages_sent_today += 1

            action_type = recruiter_info.get('button_type', 'connect')
            recruiter_key = f"{recruiter_info.get('recruiter_id', 'unknown')}:{action_type}"
            messaged_recruiters.add(recruiter_key)

            # If a Message button also exists, attempt to message after connecting
            if recruiter_info.get('has_message_button'):
                print_lg("🔁 Connect sent; attempting Message since button also exists")
                recruiter_info['button_type'] = 'message'
                return send_message_to_recruiter(driver, recruiter_info, message_init_data)

            return True, "Connection request sent with note"
            
        except Exception as e:
            # Attempt to close any stuck modal
            try: driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Dismiss')]").click()
            except: pass
            return False, f"Failed in Connect flow: {e}"


    # --- FLOW B: REGULAR MESSAGE ---
    # Detect messaging context (New Window vs Inline Bubble)
    
    is_new_window = False
    messaging_window_handle = None
    
    # Check if a new window opened
    post_click_handles = set(driver.window_handles)
    if len(post_click_handles) > len(pre_click_handles):
        is_new_window = True
        new_handles = post_click_handles - pre_click_handles
        messaging_window_handle = list(new_handles)[0]
        driver.switch_to.window(messaging_window_handle)
        print_lg("switched to new messaging window")
        buffer(2)
    else:
        print_lg("Staying in main window (inline modal detected)")

    print_lg("⏳ Waiting for compose field to be fully rendered...")
    buffer(3)
    
    # STEP 4: Strict Verification of Conversation Context
    # User Requirement: "Don't just open new message window"
    # We enforce that the active bubble MUST contain the Recruiter's name.
    print_lg(f"🔍 Strictly verifying conversation context for {recruiter_info['name']}...")
    
    verified_context = False
    
    try:
        if is_new_window:
            # Logic for new window verification - wait for page load first
            buffer(2)  # Wait for new window content to fully load
            recruiter_first_name = recruiter_info['name'].split()[0].lower()
            page_source_lower = driver.page_source.lower()
            
            # Check if first name appears in page
            if recruiter_first_name in page_source_lower:
                verified_context = True
                print_lg(f"✅ Verified - Recruiter first name '{recruiter_first_name}' found in new window")
            else:
                # Try just first few characters (handles unicode/encoding issues)
                name_prefix = recruiter_first_name[:4]  # e.g., "gabr" for Gabriel
                if name_prefix in page_source_lower:
                    verified_context = True
                    print_lg(f"✅ Verified - Recruiter name prefix '{name_prefix}' found in new window")
                else:
                    # Check URL for profile indicator
                    if '/messaging/' in driver.current_url or '/in/' in driver.current_url:
                        print_lg(f"✅ Verified - Messaging URL detected, proceeding with message")
                        verified_context = True
                    else:
                        print_lg(f"⚠️ New window verification failed - name '{recruiter_first_name}' not found in page")
        else:
            # Inline Bubble Verification
            recruiter_first_name = recruiter_info['name'].split()[0]
            
            # 1. Wait for the NAME in any active message-related element (relaxed)
            verification_xpaths = [
                # Standard active bubble
                f"//*[contains(@class,'msg-overlay-conversation-bubble--is-active') or contains(@class,'msg-overlay-conversation-bubble--is-expanded') or contains(@class,'msg-overlay-conversation-bubble--is-compose')]//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{recruiter_first_name.lower()}')]",
                # Header in message overlay
                f"//*[contains(@class,'msg-overlay-bubble-header')]//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{recruiter_first_name.lower()}')]",
                # Any msg-convo container
                f"//*[contains(@class,'msg-convo-wrapper')]//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{recruiter_first_name.lower()}')]",
                # Generic: any element with 'msg' class containing the name
                f"//*[contains(@class,'msg-')]//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{recruiter_first_name.lower()}')]"
            ]
            
            for verification_xpath in verification_xpaths:
                try:
                    WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH, verification_xpath)))
                    print_lg(f"✅ Verified - Recruiter name '{recruiter_first_name}' found in active conversation")
                    verified_context = True
                    break
                except TimeoutException:
                    continue

            # 2. Fallback: Check page source (less strict but prevents false aborts)
            if not verified_context:
                print_lg(f"⚠️ XPath Validation failed, checking page source...")
                if recruiter_first_name.lower() in driver.page_source.lower():
                    verified_context = True
                    print_lg(f"✅ Verified (Page Source) - Name '{recruiter_first_name}' found")
    
    except Exception as e:
        print_lg(f"⚠️ Verification check error: {e}")

    # FINAL DECISION: Abort if not verified
    if not verified_context:
         # Check for "New message" header which confirms it's a generic window
         try: 
             driver.find_element(By.XPATH, "//h2[contains(text(), 'New message')]")
             return False, "SAFETY ABORT: Generic 'New message' window detected (No Recipient)"
         except: pass
         
         return False, f"SAFETY ABORT: Could not verify that message window belongs to {recruiter_info['name']}"

    # STEP 4.5: POST-CLICK InMail Detection
    # Some recruiters show "Message" button but it actually requires InMail credits.
    # We detect this AFTER the click by checking for InMail-specific elements in the modal.
    # CRITICAL: Only check VISIBLE elements in active message bubbles, not the entire page!
    print_lg(f"🔍 Checking if modal requires InMail credits...")
    is_inmail_modal = False
    is_confirmed_free = False
    
    # For 1st degree connections, skip InMail check entirely - they are always free
    if recruiter_info.get('connection_degree') == '1st':
        print_lg(f"✅ Skipping InMail check - {recruiter_info['name']} is 1st degree connection (always free)")
        is_confirmed_free = True
    elif recruiter_info.get('is_free_message', False):
        print_lg(f"✅ Skipping InMail check - {recruiter_info['name']} was pre-verified as free message")
        is_confirmed_free = True
    else:
        # NOT a 1st degree connection and NOT pre-verified as free
        # We need to be STRICT here - only allow if we find POSITIVE proof it's free
        print_lg(f"⚠️ {recruiter_info['name']} is NOT 1st degree - checking for InMail indicators...")
        
        try:
            # Check for InMail indicators in the modal
            inmail_indicators = [
                # InMail credits display section
                "//div[contains(@class,'msg-overlay')]//div[contains(@class,'msg-inmail')]",
                "//div[contains(@class,'msg-overlay')]//span[contains(text(),'InMail')]",
                "//div[contains(@class,'msg-form')]//div[contains(@class,'inmail')]",
                # Text mentioning InMail credits
                "//*[contains(text(),'InMail credit')]",
                "//*[contains(text(),'InMail credits')]",
                # Subject line field (InMail requires subject, regular messages don't)
                "//input[@name='subject' or contains(@placeholder,'Subject')]",
                "//div[contains(@class,'msg-form')]//input[contains(@aria-label,'Subject')]"
            ]
            
            for indicator in inmail_indicators:
                try:
                    elems = driver.find_elements(By.XPATH, indicator)
                    for elem in elems:
                        if elem.is_displayed():
                            is_inmail_modal = True
                            print_lg(f"⚠️ InMail detected via VISIBLE element: {indicator[:60]}...")
                            break
                    if is_inmail_modal:
                        break
                except:
                    continue
            
            # ADDITIONAL CHECK: Look for "Free" or "Open Profile" indicators to confirm it's free
            free_indicators = [
                "//*[contains(@class,'msg-overlay')]//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'free')]",
                "//*[contains(text(),'Open Profile')]",
                "//*[contains(text(),'open profile')]",
            ]
            
            for free_ind in free_indicators:
                try:
                    elems = driver.find_elements(By.XPATH, free_ind)
                    for elem in elems:
                        if elem.is_displayed():
                            is_confirmed_free = True
                            is_inmail_modal = False
                            print_lg(f"✅ Found FREE indicator - confirmed as free message")
                            break
                    if is_confirmed_free:
                        break
                except:
                    continue
            
            # SAFETY: If pre-click said NOT free AND we didn't find positive proof it's free, BLOCK IT
            if not is_confirmed_free and not is_inmail_modal:
                # Pre-click detection said is_free_message=False, but we couldn't detect InMail indicators
                # This could mean LinkedIn changed their UI - be CONSERVATIVE and block
                print_lg(f"⚠️ SAFETY CHECK: Pre-click detection marked as NOT free, no positive free confirmation found")
                is_inmail_modal = True  # Treat as InMail to be safe
        
        except Exception as e:
            print_lg(f"⚠️ Post-click InMail check error: {e}")
            # On error, if pre-click said not free, be conservative
            if not recruiter_info.get('is_free_message', False):
                is_inmail_modal = True
    
    # Handle InMail modal - close it and skip
    if is_inmail_modal:
        print_lg(f"🚫 POST-CLICK InMail DETECTION: Modal requires InMail credits!")
        # CAPTURE DEBUG DATA FOR THIS FAILURE
        try:
            timestamp = os.environ.get('Safe_Current_Time', 'unknown_time').replace(':', '')
            debug_file = f"debug_html_dumps/INMAIL_BLOCK_{timestamp}.html"
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print_lg(f"📸 Saved INMAIL VALIDATION FAILURE dump to: {debug_file}")
        except Exception as e:
            print_lg(f"Could not save debug dump: {e}")

        # Close this InMail modal before returning - try multiple methods
        modal_closed = False
        
        # Try multiple close button selectors
        close_button_xpaths = [
            # Close button by aria-label
            "//button[@aria-label='Close your draft conversation']",
            # Close button with close icon
            "//button[contains(@class,'msg-overlay-bubble-header__control')]//*[contains(@data-test-icon,'close')]/..",
            # Any close button in message header
            "//button[contains(@class,'msg-overlay-bubble-header__control') and .//span[contains(text(),'Close')]]",
            # Generic close with X icon in overlay
            "//*[contains(@class,'msg-overlay')]//button[.//*[contains(@data-test-icon,'close')]]"
        ]
        
        for close_xpath in close_button_xpaths:
            try:
                close_btn = driver.find_element(By.XPATH, close_xpath)
                close_btn.click()
                buffer(0.5)
                print_lg(f"✅ Closed InMail modal via: {close_xpath[:50]}...")
                modal_closed = True
                break
            except:
                continue
        
        # JavaScript fallback if button clicks didn't work
        if not modal_closed:
            try:
                driver.execute_script("""
                    var modals = document.querySelectorAll('.msg-overlay-conversation-bubble, .msg-inmail-compose-form-v2');
                    modals.forEach(function(m) { 
                        var closeBtn = m.querySelector('button[data-test-icon="close-small"], button[aria-label*="Close"]');
                        if(closeBtn) closeBtn.click();
                    });
                """)
                buffer(0.5)
                print_lg("✅ Closed InMail modal via JavaScript")
                modal_closed = True
            except Exception as js_err:
                print_lg(f"⚠️ JS close also failed: {js_err}")
        
        if not modal_closed:
            print_lg("⚠️ Could not close InMail modal - will be cleaned up by next modal check")
        
        # Handle new window case
        if is_new_window and messaging_window_handle:
            driver.close()
            driver.switch_to.window(list(pre_click_handles)[0])
        
        return False, "SKIPPED: InMail required (detected post-click in modal)"
    
    print_lg(f"✅ Modal is FREE message - no InMail credits required")
    
    # STEP 5: Compose message in detected context
    try:
        # Generate personalized message here, JUST-IN-TIME!
        # This ensures we don't waste tokens on profiles that require InMail (which we skipped above)
        print_lg(f"🧠 Generating AI message for {recruiter_info['name']} (Verified Free)...")
        
        # Unpack init data
        aiClient = message_init_data.get('aiClient')
        job_description = message_init_data.get('job_description', '')
        job_title = message_init_data.get('job_title', '')
        company_name = message_init_data.get('company_name', '')
        job_link = message_init_data.get('job_link', '')
        
        # Check if we already have pre-generated content (legacy support or manual override)
        message_subject = message_init_data.get('message_subject', '')
        message_body = message_init_data.get('message_body', '')
        
        if not message_body:
             if recruiter_info.get('button_type') == 'connect':
                 message_body = generate_connection_note(
                    aiClient=aiClient,
                    recruiter_info=recruiter_info,
                    job_description=job_description,
                    job_title=job_title,
                    company_name=company_name,
                 )
                 message_subject = ""
             else:
                 message_subject, message_body = generate_personalized_message(
                    aiClient=aiClient,
                    recruiter_info=recruiter_info,
                    job_description=job_description,
                    job_title=job_title,
                    company_name=company_name,
                    job_link=job_link
                 )
        
        # Try multiple selectors for message body field (LinkedIn UI varies)
        msg_body = None
        body_selectors = [
            # Primary: Contenteditable INSIDE the active bubble (Most specific/safe for overlays)
            "//*[contains(@class,'msg-overlay-conversation-bubble--is-active') or contains(@class,'msg-overlay-conversation-bubble--is-expanded') or contains(@class,'msg-overlay-conversation-bubble--is-compose')]//div[contains(@class,'msg-form__contenteditable')]",
            # Fallback 1: Full Page / Generic Class Match (Critical for new window mode)
            "//div[contains(@class, 'msg-form__contenteditable')]",
            # Fallback 2: Role-based (Very common in ARIA apps)
            "//div[@role='textbox']",
            # Fallback 3: Generic contenteditable
            "//div[@contenteditable='true']"
        ]
        
        for selector in body_selectors:
            try:
                msg_body = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                print_lg(f"✅ Found message body with selector: {selector[:50]}...")
                break
            except:
                continue
        
        if not msg_body:
            return False, "ERROR: Message body field not found with any selector"
        
        # Ensure field is focused and ready
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", msg_body)
        driver.execute_script("arguments[0].focus();", msg_body)
        buffer(0.5)
        
        # Clear existing content first
        driver.execute_script("""
            var field = arguments[0];
            field.innerHTML = '';
            field.dispatchEvent(new Event('input', { bubbles: true }));
        """, msg_body)
        buffer(0.3)
        
        # Try to fill message using standard send_keys (matches Easy Apply strategy)
        # This mimics real user behavior and triggers native events best
        try:
            msg_body.click()
            buffer(0.2)
            msg_body.clear()
            msg_body.send_keys(message_body)
            buffer(0.5)
            
            # Verify text was inserted
            entered_text = msg_body.get_attribute('innerText').strip()
            
            # If clear() didn't work (common in contenteditable), try JS clear + send_keys
            if len(entered_text) < len(message_body) * 0.5:
                print_lg("Standard send_keys failed to clear/insert. Retrying...")
                driver.execute_script("arguments[0].innerHTML = '';", msg_body)
                msg_body.send_keys(message_body)
                buffer(0.5)
                entered_text = msg_body.get_attribute('innerText').strip()
            
            if len(entered_text) < 10:
                print_lg(f"⚠️ Warning: Only {len(entered_text)} chars inserted. Trying Actions chain...")
                # Fallback: ActionChains
                actions = ActionChains(driver)
                actions.move_to_element(msg_body).click().send_keys(message_body).perform()
                buffer(0.5)
                entered_text = msg_body.get_attribute('innerText').strip()

            print_lg(f"✅ Successfully inserted {len(entered_text)} characters")
            
        except Exception as e:
            return False, f"ERROR: Failed to fill message fields - {str(e)}"

    except Exception as e:
        return False, f"ERROR: Failed to prepare message body - {str(e)}"
    
    # STEP 5: Send message
    try:
        # Try multiple send button selectors (LinkedIn UI varies)
        send_button = None
        send_selectors = [
            # Primary: msg-form__send-button
            "//button[contains(@class,'msg-form__send-button') and not(@disabled)]",
            # Fallback 1: msg-form with send
            "//button[contains(@class,'msg-form') and contains(@class,'send') and not(@disabled)]",
            # Fallback 2: Just send button with aria-label
            "//button[contains(@aria-label,'Send') and not(@disabled)]",
            # Fallback 3: Any button with 'Send' text
            "//button[contains(normalize-space(.),'Send') and not(@disabled)]",
            # Fallback 4: submit type button
            "//button[@type='submit' and not(@disabled)]"
        ]
        
        for selector in send_selectors:
            try:
                send_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                print_lg(f"✅ Found send button with selector: {selector[:50]}...")
                break
            except:
                continue
        
        if not send_button:
            log_error("Send button not found", f"Tried {len(send_selectors)} selectors")
            # Save HTML dump for debugging
            dump_path = f"debug_html_dumps/SEND_BUTTON_MISSING_{recruiter_info.get('name', 'unknown')}_{int(time.time())}.html"
            make_directories([os.path.dirname(dump_path)])
            try:
                with open(dump_path, "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print_lg(f"📸 Saved SEND BUTTON MISSING dump to: {dump_path}")
            except Exception as e:
                print_lg(f"Failed to save debug dump: {e}")
            
            return False, "ERROR: Send button not found with any selector"
        
        # DRY RUN CHECK: Don't actually click send if in dry run mode
        if dry_run_mode:
            print_lg(f"✅ [DRY RUN] Would click 'Send' for {recruiter_info['name']}")
            _ensure_modal_closed(driver)
            return True, "Dry run - message not sent"
        
        send_button.click()
        buffer(3)  # Wait for send confirmation
        
        # Verify message was sent by checking if modal/compose area is gone
        send_verified = False
        for _ in range(5):
            try:
                # If we can't find the message body anymore, send likely succeeded
                driver.find_element(By.XPATH, "//div[contains(@class,'msg-form__contenteditable')]")
                buffer(1)  # Still there, wait more
            except NoSuchElementException:
                send_verified = True
                break
        
        if send_verified:
            print_lg(f"✅ Message sent and verified for {recruiter_info['name']}")
        else:
            print_lg(f"⚠️ Message clicked send for {recruiter_info['name']} but modal still visible")
        
        messages_sent_today += 1
        action_type = recruiter_info.get('button_type', 'message')
        recruiter_key = f"{recruiter_info.get('recruiter_id', 'unknown')}:{action_type}"
        messaged_recruiters.add(recruiter_key)
        
        return True, ""
        
    except Exception as e:
        return False, f"ERROR: Failed to send message - {str(e)}"
    
    except Exception as e:
        error_msg = f"Failed to send message: {str(e)}"
        print_lg(error_msg)
        return False, error_msg
    
    finally:
        # STEP 6: Cleanup - always execute
        try:
            if is_new_window and messaging_window_handle in driver.window_handles:
                driver.close()
                driver.switch_to.window(original_window)
                print_lg("✅ Closed messaging window and returned to original")
            else:
                # Close inline modal if it exists
                try:
                    close_btn = driver.find_element(By.XPATH,
                        "//button[@aria-label='Close' or contains(@class,'close-modal')]")
                    close_btn.click()
                    buffer(1)
                except:
                    pass  # Modal already closed, ignore
                    
                _ensure_modal_closed(driver)
        except Exception as e:
            print_lg(f"Error in cleanup: {e}")





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


def should_skip_recruiter(recruiter_info: dict, job_id: str, already_applied: bool, action_type: str = "message") -> tuple[bool, str]:
    '''
    Determines if recruiter should be skipped.
    Returns (should_skip: bool, reason: str)
    '''
    # Check if already messaged this recruiter
    recruiter_key = f"{recruiter_info.get('recruiter_id', 'unknown')}:{action_type}"
    if recruiter_key in messaged_recruiters:
        return True, "Already messaged this recruiter today"

    # Check if already applied to job
    if skip_if_already_applied and already_applied:
        return True, "Already applied via Easy Apply"

    # Check if InMail required but we want only free messages
    # IMPORTANT: If message_type is 'unknown', we still attempt - post-click verification will decide
    message_type = recruiter_info.get('message_type', 'unknown')
    if skip_inmail_required and not recruiter_info['is_free_message'] and message_type != 'unknown':
        return True, "InMail required (preserving credits)"

    # Check daily limit
    if check_daily_message_limit():
        return True, "Daily message limit reached"

    # Check if can message or connect at all
    if not recruiter_info['can_message']:
        return True, "No message or connect button available"

    return False, ""
