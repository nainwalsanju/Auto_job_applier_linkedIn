# LinkedIn Auto Job Applier - Architecture & Flow Documentation

## Table of Contents

1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Data Flow](#data-flow)
5. [Usage Examples](#usage-examples)
6. [Module Dependencies](#module-dependencies)
7. [Configuration](#configuration)
8. [Testing](#testing)

---

## Overview

This is an **automated LinkedIn job application bot** that:
- Searches for jobs based on your criteria
- Filters and parses job listings
- Applies to jobs automatically (Easy Apply)
- Handles form questions (manually or with AI)
- Tracks all applications in CSV/JSON

### Key Features

- **Stealth Mode**: Uses undetected-chromedriver to avoid detection
- **AI Integration**: Supports OpenAI, DeepSeek, and Gemini for answering questions
- **Structured Logging**: JSON logs for monitoring and debugging
- **Result Tracking**: Saves applied/failed jobs to CSV
- **Web UI**: Optional Flask web interface

---

## Project Structure

```
Auto_job_applier_linkedIn/
├── runAiBot.py                 # Original monolithic entry point (still works!)
├── app.py                      # Original Flask web UI
├── config/                     # Original configuration files
│   ├── secrets.py             # Credentials (now from .env)
│   ├── personals.py           # Personal info
│   ├── questions.py           # Pre-defined answers
│   ├── search.py              # Search criteria
│   ├── settings.py            # App settings
│   └── resume.py              # Resume config
├── modules/                    # Original modules (backward compatible)
│   ├── ai/                    # AI connections
│   ├── helpers.py
│   └── clickers_and_finders.py
├── src/linkedin_applier/       # NEW: Modular refactored code
│   ├── __init__.py            # Package entry
│   ├── core/                  # Browser, session, state
│   ├── jobs/                  # Job search, filter, parse, apply
│   ├── forms/                 # Form detection, answering
│   ├── ai/                    # AI client interface
│   ├── utils/                 # Logging, result tracking
│   ├── config/                # Configuration validation
│   ├── ui/                    # Web UI
│   └── exceptions/            # Custom exceptions
├── templates/                  # Web UI templates
├── test_refactored_code.py     # Unit tests
├── pyproject.toml             # Code quality config
└── requirements.txt           # Dependencies
```

---

## Core Components

### 1. Core Module (`src/linkedin_applier/core/`)

Manages browser lifecycle and application state.

#### BrowserManager
```python
from src.linkedin_applier.core import BrowserManager

# Create and initialize browser
browser = BrowserManager(headless=False, stealth_mode=True)
browser.initialize()

# Get driver for other modules
driver = browser.get_driver()

# Cleanup
browser.close()
```

**Responsibilities:**
- Initialize Chrome with stealth settings
- Manage WebDriver instance
- Handle browser lifecycle

#### SessionManager
```python
from src.linkedin_applier.core import SessionManager

session = SessionManager(driver, wait)

# Check login status
if not session.is_logged_in():
    session.login(username, password)

# Logout when done
session.logout()
```

**Responsibilities:**
- Check LinkedIn login status
- Handle login flow
- Manage session state

#### AppState
```python
from src.linkedin_applier.core import get_state

state = get_state()
state.start_session()

# Increment counters
state.increment_applied()
state.increment_skipped()
state.increment_failed()

# Get statistics
stats = state.get_stats()
# {'jobs_applied': '5', 'jobs_skipped': '2', 'jobs_failed': '1', ...}

# End session
final_stats = state.end_session()
```

**Responsibilities:**
- Track application statistics
- Manage blacklist of companies
- Track rejected job IDs

---

### 2. Jobs Module (`src/linkedin_applier/jobs/`)

Handles job search, filtering, parsing, and application.

#### JobSearcher
```python
from src.linkedin_applier.jobs import JobSearcher

searcher = JobSearcher(driver, wait)

# Search for jobs
searcher.search("Python Developer", "Remote")

# Navigate pages
for page in range(1, 10):
    if not searcher.navigate_to_page(page):
        break
    
    # Get job cards
    cards = searcher.get_job_cards()
    
    # Click on a job
    for card in cards:
        searcher.click_job(card)
```

#### JobFilter
```python
from src.linkedin_applier.jobs import JobFilter

filters = JobFilter(driver, wait)

# Apply filters from config
filters.apply_config_filters()

# Or manually
filters.set_date_filter("Past week")
filters.set_location_filter("Remote")
filters.set_experience_filter(["Mid-Senior", "Entry level"])
filters.set_work_style_filter(["Remote"])
```

#### JobParser
```python
from src.linkedin_applier.jobs import JobParser

parser = JobParser(driver, wait)

# Parse current job page
job = parser.parse_job_details()
# Returns JobDetails object with:
# - job_id, title, company, work_location, work_style
# - description, skills, experience_required

# Extract skills
skills = parser.extract_skills(job.description)

# Check blacklist
skip, reason = parser.check_blacklist(job.description, job.company)
if skip:
    print(f"Skipping: {reason}")
```

#### JobApplicator
```python
from src.linkedin_applier.jobs import JobApplicator

applicator = JobApplicator(driver, wait)

# Submit Easy Apply application
result = applicator.easy_apply(job, answers={
    "Email": "test@example.com",
    "Phone": "1234567890"
})

if result.applied:
    print(f"Applied to {job.title} at {job.company}")
else:
    print(f"Failed: {result.error}")
```

---

### 3. Forms Module (`src/linkedin_applier/forms/`)

Detects and fills form fields.

#### FormParser
```python
from src.linkedin_applier.forms import FormParser

parser = FormParser(driver, wait)

# Detect all form fields
fields = parser.detect_all_fields()
# Returns list of FormField objects:
# - label: "Email"
# - field_type: "text"
# - required: True
# - options: []

# Detect by keyword
detected = parser.detect_by_keywords()
# {'email': 'Email', 'phone': 'Phone Number', ...}
```

#### FormHandler
```python
from src.linkedin_applier.forms import FormHandler

handler = FormHandler(driver, wait)

# Fill form with answers
answers = {"Email": "test@example.com", "Phone": "123"}
answered = handler.fill_form(answers)
# Returns list of answered questions

# Get unanswered required questions
unanswered = handler.get_unanswered_questions()
```

---

### 4. AI Module (`src/linkedin_applier/ai/`)

Unified interface for AI providers.

#### AIClient
```python
from src.linkedin_applier.ai import AIClient, create_ai_client

# Create client
client = create_ai_client(provider="deepseek")

# Or directly
client = AIClient(provider="deepseek")

# Extract skills
skills = client.extract_skills(job_description)
# {'skills': ['Python', 'AWS', 'Docker'], 'tools': [...]}

# Answer questions
answer = client.answer_question(
    question="How many years of Python experience?",
    options=["1-2 years", "3-5 years", "5+ years"],
    question_type="single_select",
    job_description=job.description,
    user_info="5 years Python experience"
)
```

**Supported Providers:**
- `openai` - GPT-4, GPT-3.5-Turbo
- `deepseek` - DeepSeek-Chat (default)
- `gemini` - Google Gemini

---

### 5. Utils Module (`src/linkedin_applier/utils/`)

Utility functions for logging and tracking.

#### Logger
```python
from src.linkedin_applier.utils import setup_logging, log

# Initialize structured logging
setup_logging(log_dir="logs", log_level="INFO", json_format=True)

# Use throughout application
log.info("Job applied", job_id="12345", company="Google")
log.job_applied(job_id="12345", title="Developer", company="Google")
log.job_skipped(job_id="67890", reason="Blacklisted company")
log.job_failed(job_id="11111", error="Timeout")
log.session_started(search_terms=["Python"], location="Remote")
log.session_ended(stats={"applied": 10, "failed": 2})
```

#### ResultTracker
```python
from src.linkedin_applier.utils import ResultTracker, get_tracker

# Create tracker
tracker = ResultTracker(results_dir="results")

# Save successful application
tracker.save_applied(job, questions_answered=[...])

# Save failed application
tracker.save_failed(job, error="Timeout", screenshot="path/to/screenshot.png")

# Get session statistics
stats = tracker.get_session_stats()

# Save session to JSON
session_data = tracker.save_session()
```

---

### 6. Config Module (`src/linkedin_applier/config/`)

Configuration management and validation.

```python
from src.linkedin_applier.config import (
    AppConfig, SearchConfig, BrowserConfig,
    validate_config, load_legacy_config
)

# Create app config
config = AppConfig()
config.search.search_terms = ["Python Developer", "Backend Engineer"]
config.search.search_location = "Remote"
config.browser.stealth_mode = True

# Validate configuration
is_valid, errors = validate_config(config)
if not is_valid:
    print(f"Config errors: {errors}")

# Load from original config files
legacy = load_legacy_config()
```

---

### 7. Exceptions Module (`src/linkedin_applier/exceptions/`)

Custom exception hierarchy for better error handling.

```python
from src.linkedin_applier.exceptions import (
    LinkedInApplierError,
    BrowserError, ApplicationError, AIError,
    ElementNotFoundError, JobParseError,
    BlacklistMatchError
)

try:
    job = parser.parse_job_details()
except JobParseError as e:
    print(f"Failed to parse job: {e.message}")
    logger.error("Job parse failed", details=e.to_dict())
except BlacklistMatchError as e:
    print(f"Skipped blacklisted job: {e.details}")
```

---

## Data Flow

### Main Application Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        runAiBot.py                               │
│                   (Original entry point)                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Initialize Components                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │BrowserManager│  │SessionManager│  │     AppState        │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Job Search Loop                             │
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐       │
│  │JobSearcher  │───▶│JobParser   │───▶│JobApplicator    │       │
│  │             │    │             │    │                 │       │
│  │- search()   │    │- parse()    │    │- easy_apply()   │       │
│  │- paginate() │    │- extract()  │    │- upload_resume()│       │
│  └─────────────┘    └─────────────┘    └─────────────────┘       │
│                              │                                   │
│                              ▼                                   │
│                      ┌─────────────┐                             │
│                      │ ResultTracker│                           │
│                      │  (CSV/JSON)  │                           │
│                      └─────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

### Form Handling Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     Form Detected                                │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    FormParser.detect_all_fields()      │   │
│  │  Returns: List[FormField]                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 FormHandler.fill_form()                │   │
│  │                                                         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌────────────────┐  │   │
│  │  │  Pre-defined│  │   Config   │  │   AI Answer    │  │   │
│  │  │   Answers   │  │   Answers  │  │   (if needed)  │  │   │
│  │  └─────────────┘  └─────────────┘  └────────────────┘  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│                      ┌─────────────┐                             │
│                      │   Submit    │                             │
│                      └─────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

### AI Integration Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                 Question Answering                               │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              AIClient.answer_question()                │   │
│  │                                                         │   │
│  │  provider = deepseek | openai | gemini                 │   │
│  │       │                 │               │               │   │
│  │       ▼                 ▼               ▼               │   │
│  │  ┌─────────┐       ┌─────────┐   ┌─────────────┐      │   │
│  │  │DeepSeek │       │ OpenAI  │   │  Gemini    │      │   │
│  │  │  API    │       │   API   │   │    API     │      │   │
│  │  └─────────┘       └─────────┘   └─────────────┘      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│                      ┌─────────────┐                             │
│                      │  Return     │                             │
│                      │  Answer     │                             │
│                      └─────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Usage Examples

### Basic Usage

```python
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

from src.linkedin_applier.core import BrowserManager, SessionManager, AppState
from src.linkedin_applier.jobs import JobSearcher, JobParser, JobApplicator
from src.linkedin_applier.utils import setup_logging, log, get_tracker

# Initialize
setup_logging(log_dir="logs")
browser = BrowserManager(headless=False, stealth_mode=True)
browser.initialize()

driver = browser.driver
wait = WebDriverWait(driver, 30)

# Login
session = SessionManager(driver, wait)
session.login()

# Start tracking
state = AppState()
state.start_session()
tracker = get_tracker()

# Search for jobs
searcher = JobSearcher(driver, wait)
parser = JobParser(driver, wait)
applicator = JobApplicator(driver, wait)

searcher.search("Python Developer", "Remote")

# Process jobs on page
for card in searcher.get_job_cards():
    searcher.click_job(card)
    
    job = parser.parse_job_details()
    
    if parser.check_blacklist(job.description, job.company)[0]:
        state.increment_skipped()
        continue
    
    result = applicator.easy_apply(job)
    
    if result.applied:
        state.increment_applied()
        tracker.save_applied(job, result.questions_answered)
    else:
        state.increment_failed()
        tracker.save_failed(job, result.error)

# End session
stats = state.end_session()
tracker.save_session()
log.session_ended(stats=stats)

browser.close()
```

### Using AI for Questions

```python
from src.linkedin_applier.ai import create_ai_client

# Create AI client
ai_client = create_ai_client(provider="deepseek")

# When answering unknown questions
unknown_question = "How do you handle tight deadlines?"
answer = ai_client.answer_question(
    question=unknown_question,
    question_type="text",
    job_description=job.description,
    about_company=company_info,
    user_info=user_experience
)
```

---

## Module Dependencies

```
src.linkedin_applier/
├── __init__.py
├── core/
│   ├── browser_manager.py  ──depends on──▶ config/settings
│   ├── session.py          ──depends on──▶ config/secrets, core/browser_manager
│   └── state.py           ──depends on──▶ jobs/models
├── jobs/
│   ├── models.py          ──no external dependencies
│   ├── search.py          ──depends on──▶ core, utils, jobs/models
│   ├── filters.py         ──depends on──▶ core, utils
│   ├── parser.py          ──depends on──▶ core, utils, jobs/models, config/search
│   └── apply.py           ──depends on──▶ core, utils, jobs/models, 
│                                              config/personals, config/questions
├── forms/
│   ├── parser.py          ──depends on──▶ core, utils
│   └── handler.py         ──depends on──▶ core, forms/parser, config/personals
├── ai/
│   └── client.py          ──depends on──▶ config/secure_config, utils,
│                                              modules/ai/* (original)
├── utils/
│   ├── logger.py          ──no external dependencies
│   └── result_tracker.py  ──depends on──▶ jobs/models
├── config/
│   └── settings.py        ──depends on──▶ config/* (original)
├── ui/
│   └── web_ui.py          ──depends on──▶ config, utils
└── exceptions/
    └── custom_exceptions.py──no external dependencies
```

---

## Configuration

### Environment Variables (.env)

```env
# LinkedIn
LINKEDIN_USERNAME=your_email@example.com
LINKEDIN_PASSWORD=your_password

# AI
USE_AI=false
AI_PROVIDER=deepseek
LLM_API_KEY=your-api-key
LLM_MODEL=deepseek-chat

# Browser
STEALTH_MODE=false
CLICK_GAP=1
```

### Original Config Files (Still Used)

| File | Purpose |
|------|---------|
| `config/personals.py` | Name, address, experience, etc. |
| `config/questions.py` | Pre-defined answers to common questions |
| `config/search.py` | Search terms, filters, blacklist |
| `config/settings.py` | Browser settings, UI settings |
| `config/secrets.py` | Now loads from .env for security |

---

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
python test_refactored_code.py

# Or with pytest
pytest test_refactored_code.py -v
```

### Test Coverage

- ✅ Job models (JobDetails, ApplicationResult, SessionStats)
- ✅ Exception hierarchy
- ✅ Structured logging
- ✅ Result tracker
- ✅ Backward compatibility
- ✅ Core state management

---

## Backward Compatibility

The original `runAiBot.py` and `app.py` continue to work unchanged. All new modules can be imported alongside the original code:

```python
# Mix old and new code
from config.secrets import username  # Old
from src.linkedin_applier.jobs import JobParser  # New

# Use both
driver = create_driver_old_way()
parser = JobParser(driver, wait)
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Login fails | Check credentials in `.env` |
| AI not working | Set `USE_AI=true` and provide `LLM_API_KEY` |
| Browser detection | Enable `stealth_mode=True` |
| Form questions fail | Provide answers in `config/questions.py` |
| Type errors | Install dependencies: `pip install -r requirements.txt` |

### Logs

Check logs in the `logs/` directory for debugging:

```bash
# View recent logs
tail -f logs/applier_*.log
```

---

## Next Steps

1. **Complete Migration**: Eventually migrate all code from `runAiBot.py` to new modules
2. **Add More Tests**: Increase test coverage
3. **CI/CD**: Set up GitHub Actions
4. **Documentation**: Generate API docs with Sphinx

---

**Document Version:** 1.0  
**Last Updated:** January 15, 2026  
**Branch:** `refactor/improvements`
