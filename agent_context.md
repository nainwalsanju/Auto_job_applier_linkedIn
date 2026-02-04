# Auto Job Applier LinkedIn - Agent Context

This file is generated. Do not edit manually.
Regenerate with: `python execution/generate_agent_context.py`

## Project Overview

- Project Name: LinkedIn AI Auto Job Applier
- Project Root: PROJECT_ROOT
- Generated On: February 04, 2026

## User Profile (Redacted)

- Name: <REDACTED>
- Location: <REDACTED>
- Phone: <REDACTED>
- Email: <REDACTED>
- LinkedIn: <REDACTED>
- Portfolio: <REDACTED>
- Current Employer: <REDACTED>
- Years of Experience: <REDACTED>
- Visa Sponsorship: <REDACTED>
- Citizenship: <REDACTED>
- Notice Period (days): <REDACTED>

Notes:
- Personal details are configured locally in `config/personals.py` and `config/questions.py`.
- Sensitive values are redacted in this document.

## Job Search Configuration

- Search Terms: Java, Backend Engineer, Software Engineer, Software Developer, Senior Software Engineer, Senior Backend Developer, SDE-3, SSE
- Search Locations: India,United States,Asia,Australia,Canada,Europe,UAE,Middle East,Singapore, Pune, Maharashtra, India, United Kingdom,America
- Randomize Location: Yes
- Switch After: 30
- Randomize Order: Yes
- Sort By: Most relevant
- Date Posted: Any time
- Easy Apply Only: Yes
- Experience Levels: Associate, Mid-Senior level
- Job Types: []
- Work Styles: Remote, Hybrid
- Under 10 Applicants: No
- In Your Network: No
- Fair Chance Employer: No
- Bad Words (Company): BharatPe
- Bad Words (Description): US Citizen, USA Citizen, No C2C, No Corp2Corp, Embedded Programming, CNC
- Security Clearance: No
- Current Experience: 6
- Preferred Work Style: remote

## AI Configuration

- AI Enabled: Yes
- Provider: deepseek
- API URL: https://api.deepseek.com/v1
- Model: deepseek-chat
- Stream Output: No
- LinkedIn Username: <REDACTED>
- LinkedIn Password: <REDACTED>
- LLM API Key: <REDACTED>

## Bot Settings

- Pause Before Submit: Yes
- Pause At Failed Question: Yes
- Overwrite Previous Answers: No
- Run In Background: No
- Close External Tabs: No
- Disable Extensions: Yes
- Safe Mode: Yes
- Smooth Scroll: No
- Keep Screen Awake: Yes
- Stealth Mode: No
- Click Gap (seconds): 1
- Run Non-Stop: No
- Alternate Sort: Yes
- Cycle Date Posted: Yes
- Stop Date Cycle At 24hr: No

## Paths

- Default Resume: data/resumes/default/resume.pdf
- Generated Resumes: data/resumes/
- Applied Jobs CSV: data/excels/all_applied_applications_history.csv
- Failed Jobs CSV: data/excels/all_failed_applications_history.csv
- Logs Folder: logs/

## Security Notes

- Do not commit real credentials or personal data.
- Store secrets in `.env` and keep `config/secrets.py` redacted or local-only.
- Use template files for public repos (e.g., `config/secrets.example.py`).
