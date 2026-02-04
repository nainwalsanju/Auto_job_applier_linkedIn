"""
Author:     Sanjay Nainwal
GitHub:     https://github.com/nainwalsanju/Auto_job_applier_linkedIn
Description: Selectors for Glassdoor UI elements.
"""

# LOGIN
LOGIN_URL = "https://www.glassdoor.com/profile/login_input.htm"
USERNAME_FIELD = "//input[@id='inlineUserEmail']"
PASSWORD_FIELD = "//input[@id='inlineUserPassword']"
SUBMIT_LOGIN = "//button[@type='submit']"

# SEARCH
SEARCH_URL = "https://www.glassdoor.com/Job/index.htm"
JOB_TITLE_INPUT = "//input[@id='searchBar-jobTitle']"
LOCATION_INPUT = "//input[@id='searchBar-location']"
SEARCH_BUTTON = "//button[@data-test='search-bar-submit']"

# FILTERS
EASY_APPLY_FILTER = "//button[contains(., 'Easy Apply')]"
DATE_POSTED_FILTER = "//button[@data-test='filter-date-posted']"
LAST_24H_OPTION = "//li[contains(., 'Last 24 Hours')]"

# JOB LISTING
JOB_LIST_ITEMS = "//li[@data-test='jobListing']"
JOB_TITLE_LINK = ".//a[@data-test='job-link']"
COMPANY_NAME = ".//span[@class='EmployerProfile_employerName__8w09P']"

# APPLICATION
APPLY_BUTTON = "//button[@data-test='apply-button']"
# Glassdoor Easy Apply forms often open in a modal or new tab
GD_EASY_APPLY_INDICATOR = "//button[contains(., 'Easy Apply')]"
FORM_CONTAINER = "//div[contains(@class, 'Modal')]"
CONTINUE_BUTTON = "//button[contains(., 'Continue') or contains(., 'Next')]"
SUBMIT_APP_BUTTON = "//button[contains(., 'Submit')]"
