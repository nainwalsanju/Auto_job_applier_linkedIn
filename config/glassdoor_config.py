"""
Author:     Sanjay Nainwal
GitHub:     https://github.com/nainwalsanju/Auto_job_applier_linkedIn
Description: Configuration settings for Glassdoor automation.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Glassdoor Search Settings
glassdoor_keywords = ["Backend Engineer", "Java Developer", "Software Engineer"]
glassdoor_location = "India"  # e.g., "United States", "London", "Remote"

# Filters
only_easy_apply = True  # Only target jobs with Glassdoor's Easy Apply
last_24_hours = True  # Only search for jobs posted in the last 24 hours

# Glassdoor Login (Uses environment variables)
glassdoor_username = os.getenv("GLASSDOOR_USERNAME", "your_email@example.com")
glassdoor_password = os.getenv("GLASSDOOR_PASSWORD", "your_password_here")

# Limits
max_glassdoor_apps_per_run = 25
