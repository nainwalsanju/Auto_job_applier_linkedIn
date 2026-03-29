#!/usr/bin/env python3
"""Generate a redacted agent context doc from config files.

This script is intentionally conservative about sensitive data. It will redact
PII and secrets while preserving non-sensitive configuration needed for context.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import importlib.util
from pathlib import Path
from typing import Any


REDACTED = "<REDACTED>"

PII_KEYS = {
    "first_name",
    "middle_name",
    "last_name",
    "phone_number",
    "current_city",
    "street",
    "state",
    "zipcode",
    "country",
    "ethnicity",
    "gender",
    "disability_status",
    "veteran_status",
    "website",
    "linkedIn",
    "headline",
    "linkedin_headline",
    "summary",
    "linkedin_summary",
    "cover_letter",
    "recent_employer",
}

SENSITIVE_KEYS = {
    "username",
    "password",
    "llm_api_key",
}

SENSITIVE_OR_PERSONAL_KEYS = PII_KEYS | SENSITIVE_KEYS | {
    "desired_salary",
    "current_ctc",
    "notice_period",
    "years_of_experience",
    "require_visa",
    "us_citizenship",
}


@dataclass
class ModuleLoadResult:
    module: Any | None
    error: str | None


def load_module(path: Path, name: str) -> ModuleLoadResult:
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            return ModuleLoadResult(None, f"Could not load module spec for {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return ModuleLoadResult(module, None)
    except Exception as exc:  # pragma: no cover - best effort
        return ModuleLoadResult(None, f"{exc.__class__.__name__}: {exc}")


def redact_value(key: str, value: Any) -> Any:
    if key in SENSITIVE_OR_PERSONAL_KEYS:
        return REDACTED
    return value


def format_value(value: Any) -> str:
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) if value else "[]"
    if value is None:
        return ""
    return str(value)


def get_attr(module: Any, key: str, default: Any = None) -> Any:
    if module is None:
        return default
    return getattr(module, key, default)


def section(lines: list[str], title: str) -> None:
    lines.append(f"## {title}")
    lines.append("")


def add_kv(lines: list[str], label: str, value: Any) -> None:
    lines.append(f"- {label}: {format_value(value)}")


def generate_agent_context() -> str:
    root = Path(__file__).resolve().parents[1]
    now = datetime.now().strftime("%B %d, %Y")

    personals = load_module(root / "config" / "personals.py", "config.personals")
    questions = load_module(root / "config" / "questions.py", "config.questions")
    search = load_module(root / "config" / "search.py", "config.search")
    settings = load_module(root / "config" / "settings.py", "config.settings")
    secrets = load_module(root / "config" / "secrets.py", "config.secrets")

    lines: list[str] = []
    lines.append("# Auto Job Applier LinkedIn - Agent Context")
    lines.append("")
    lines.append("This file is generated. Do not edit manually.")
    lines.append("Regenerate with: `python execution/generate_agent_context.py`")
    lines.append("")

    section(lines, "Project Overview")
    add_kv(lines, "Project Name", "LinkedIn AI Auto Job Applier")
    add_kv(lines, "Project Root", "PROJECT_ROOT")
    add_kv(lines, "Generated On", now)
    lines.append("")

    section(lines, "User Profile (Redacted)")
    add_kv(lines, "Name", REDACTED)
    add_kv(lines, "Location", REDACTED)
    add_kv(lines, "Phone", REDACTED)
    add_kv(lines, "Email", REDACTED)
    add_kv(lines, "LinkedIn", REDACTED)
    add_kv(lines, "Portfolio", REDACTED)
    add_kv(lines, "Current Employer", REDACTED)
    add_kv(
        lines,
        "Years of Experience",
        redact_value("years_of_experience", get_attr(questions.module, "years_of_experience")),
    )
    add_kv(
        lines,
        "Visa Sponsorship",
        redact_value("require_visa", get_attr(questions.module, "require_visa")),
    )
    add_kv(
        lines,
        "Citizenship",
        redact_value("us_citizenship", get_attr(questions.module, "us_citizenship")),
    )
    add_kv(
        lines,
        "Notice Period (days)",
        redact_value("notice_period", get_attr(questions.module, "notice_period")),
    )
    lines.append("")
    lines.append("Notes:")
    lines.append("- Personal details are configured locally in `config/personals.py` and `config/questions.py`.")
    lines.append("- Sensitive values are redacted in this document.")
    lines.append("")

    section(lines, "Job Search Configuration")
    add_kv(lines, "Search Terms", get_attr(search.module, "search_terms", []))
    add_kv(lines, "Search Locations", get_attr(search.module, "search_location", ""))
    add_kv(lines, "Randomize Location", get_attr(search.module, "randomize_search_location"))
    add_kv(lines, "Switch After", get_attr(search.module, "switch_number"))
    add_kv(lines, "Randomize Order", get_attr(search.module, "randomize_search_order"))
    add_kv(lines, "Sort By", get_attr(search.module, "sort_by"))
    add_kv(lines, "Date Posted", get_attr(search.module, "date_posted"))
    add_kv(lines, "Easy Apply Only", get_attr(search.module, "easy_apply_only"))
    add_kv(lines, "Experience Levels", get_attr(search.module, "experience_level", []))
    add_kv(lines, "Job Types", get_attr(search.module, "job_type", []))
    add_kv(lines, "Work Styles", get_attr(search.module, "on_site", []))
    add_kv(lines, "Under 10 Applicants", get_attr(search.module, "under_10_applicants"))
    add_kv(lines, "In Your Network", get_attr(search.module, "in_your_network"))
    add_kv(lines, "Fair Chance Employer", get_attr(search.module, "fair_chance_employer"))
    add_kv(lines, "Bad Words (Company)", get_attr(search.module, "about_company_bad_words", []))
    add_kv(lines, "Bad Words (Description)", get_attr(search.module, "bad_words", []))
    add_kv(lines, "Security Clearance", get_attr(search.module, "security_clearance"))
    add_kv(lines, "Current Experience", get_attr(search.module, "current_experience"))
    add_kv(lines, "Preferred Work Style", get_attr(search.module, "preferred_work_style"))
    lines.append("")

    section(lines, "AI Configuration")
    add_kv(lines, "AI Enabled", get_attr(secrets.module, "use_AI", "(env: USE_AI)"))
    add_kv(lines, "Provider", get_attr(secrets.module, "ai_provider", "(env: AI_PROVIDER)"))
    add_kv(lines, "API URL", get_attr(secrets.module, "llm_api_url", "(env: LLM_API_URL)"))
    add_kv(lines, "Model", get_attr(secrets.module, "llm_model", "(env: LLM_MODEL)"))
    add_kv(lines, "Stream Output", get_attr(secrets.module, "stream_output", "(env: STREAM_OUTPUT)"))
    add_kv(lines, "LinkedIn Username", REDACTED)
    add_kv(lines, "LinkedIn Password", REDACTED)
    add_kv(lines, "LLM API Key", REDACTED)
    if secrets.error:
        lines.append("")
        lines.append(f"Notes: Could not load secrets config ({secrets.error}). Using env placeholders.")
    lines.append("")

    section(lines, "Bot Settings")
    add_kv(lines, "Pause Before Submit", get_attr(questions.module, "pause_before_submit"))
    add_kv(lines, "Pause At Failed Question", get_attr(questions.module, "pause_at_failed_question"))
    add_kv(lines, "Overwrite Previous Answers", get_attr(questions.module, "overwrite_previous_answers"))
    add_kv(lines, "Run In Background", get_attr(settings.module, "run_in_background"))
    add_kv(lines, "Close External Tabs", get_attr(settings.module, "close_tabs"))
    add_kv(lines, "Disable Extensions", get_attr(settings.module, "disable_extensions"))
    add_kv(lines, "Safe Mode", get_attr(settings.module, "safe_mode"))
    add_kv(lines, "Smooth Scroll", get_attr(settings.module, "smooth_scroll"))
    add_kv(lines, "Keep Screen Awake", get_attr(settings.module, "keep_screen_awake"))
    add_kv(lines, "Stealth Mode", get_attr(settings.module, "stealth_mode"))
    add_kv(lines, "Click Gap (seconds)", get_attr(settings.module, "click_gap"))
    add_kv(lines, "Run Non-Stop", get_attr(settings.module, "run_non_stop"))
    add_kv(lines, "Alternate Sort", get_attr(settings.module, "alternate_sortby"))
    add_kv(lines, "Cycle Date Posted", get_attr(settings.module, "cycle_date_posted"))
    add_kv(lines, "Stop Date Cycle At 24hr", get_attr(settings.module, "stop_date_cycle_at_24hr"))
    lines.append("")

    section(lines, "Paths")
    add_kv(lines, "Default Resume", get_attr(questions.module, "default_resume_path"))
    add_kv(lines, "Generated Resumes", get_attr(settings.module, "generated_resume_path"))
    add_kv(lines, "Applied Jobs CSV", get_attr(settings.module, "file_name"))
    add_kv(lines, "Failed Jobs CSV", get_attr(settings.module, "failed_file_name"))
    add_kv(lines, "Logs Folder", get_attr(settings.module, "logs_folder_path"))
    lines.append("")

    section(lines, "Security Notes")
    lines.append("- Do not commit real credentials or personal data.")
    lines.append("- Store secrets in `.env` and keep `config/secrets.py` redacted or local-only.")
    lines.append("- Use template files for public repos (e.g., `config/secrets.example.py`).")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output_path = root / "agent_context.md"
    content = generate_agent_context()
    output_path.write_text(content, encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
