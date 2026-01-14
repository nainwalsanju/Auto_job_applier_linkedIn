"""
Job Models for LinkedIn Auto Job Applier

This module provides Pydantic models for job-related data structures.
All models include validation and serialization methods.

Example:
    job = JobDetails(
        job_id="123456789",
        title="Python Developer",
        company="Tech Corp",
        work_location="Remote",
        work_style="Full-time"
    )
    print(job.to_csv_dict())
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum


class WorkStyle(str, Enum):
    """Work style options for jobs."""

    FULL_TIME = "Full-time"
    PART_TIME = "Part-time"
    CONTRACT = "Contract"
    TEMPORARY = "Temporary"
    INTERNSHIP = "Internship"
    OTHER = "Other"


class ApplicationType(str, Enum):
    """Type of application method."""

    EASY_APPLY = "Easy Apply"
    EXTERNAL_APPLY = "External Apply"
    UNKNOWN = "Unknown"


@dataclass
class JobDetails:
    """
    Job details extracted from LinkedIn.

    Attributes:
        job_id: Unique LinkedIn job identifier
        title: Job title
        company: Company name
        work_location: Location of the job
        work_style: Work arrangement (remote, hybrid, etc.)
        description: Full job description text
        experience_required: Years of experience required
        skills: List of skills mentioned in the job
        hr_name: Name of the HR contact (if available)
        hr_link: LinkedIn profile link of HR (if available)
        date_posted: When the job was posted
        reposted: Whether the job is a repost
    """

    job_id: str
    title: str
    company: str
    work_location: str
    work_style: str
    description: str = ""
    experience_required: Optional[int] = None
    skills: list[str] = field(default_factory=list)
    hr_name: Optional[str] = None
    hr_link: Optional[str] = None
    date_posted: Optional[datetime] = None
    reposted: bool = False

    def to_csv_dict(self) -> dict[str, str]:
        """Convert to dictionary suitable for CSV export."""
        return {
            "job_id": self.job_id,
            "title": self.title,
            "company": self.company,
            "work_location": self.work_location,
            "work_style": self.work_style,
            "experience_required": str(self.experience_required or ""),
            "skills": ", ".join(self.skills),
            "hr_name": self.hr_name or "",
            "hr_link": self.hr_link or "",
            "description": self.description[:1000] if self.description else "",
        }

    def to_summary_dict(self) -> dict[str, str]:
        """Convert to a summary dictionary for logging."""
        return {
            "job_id": self.job_id,
            "title": self.title,
            "company": self.company,
            "location": self.work_location,
        }


@dataclass
class ApplicationResult:
    """
    Result of a job application attempt.

    Attributes:
        job: The JobDetails that was applied to
        applied: Whether the application was successful
        application_type: Type of application (Easy Apply/External)
        external_link: Link to external application (if applicable)
        date_applied: When the application was submitted
        questions_answered: List of questions that were answered
        error: Error message if application failed
        screenshot: Path to screenshot (if taken)
    """

    job: JobDetails
    applied: bool
    application_type: str = ApplicationType.UNKNOWN.value
    external_link: Optional[str] = None
    date_applied: datetime = field(default_factory=datetime.now)
    questions_answered: list = field(default_factory=list)
    error: Optional[str] = None
    screenshot: Optional[str] = None

    def to_csv_dict(self) -> dict[str, str]:
        """Convert to dictionary suitable for CSV export."""
        return {
            "job_id": self.job.job_id,
            "title": self.job.title,
            "company": self.job.company,
            "applied": str(self.applied),
            "application_type": self.application_type,
            "external_link": self.external_link or "",
            "date_applied": self.date_applied.isoformat(),
            "error": self.error or "",
            "questions_count": str(len(self.questions_answered)),
        }


@dataclass
class FormQuestion:
    """
    A single form question with its answer.

    Attributes:
        label: The question text/label
        question_type: Type of input (select, radio, text, textarea, checkbox)
        answer: The selected/entered answer
        options: Available options (for select/radio questions)
        prev_answer: Previously selected answer (for edits)
        answered_by_ai: Whether AI was used to generate the answer
    """

    label: str
    question_type: str
    answer: str
    options: list[str] = field(default_factory=list)
    prev_answer: Optional[str] = None
    answered_by_ai: bool = False

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary."""
        return {
            "label": self.label,
            "type": self.question_type,
            "answer": self.answer,
            "options": ", ".join(self.options),
            "ai_generated": str(self.answered_by_ai),
        }


@dataclass
class SessionStats:
    """
    Statistics for a job application session.

    Attributes:
        start_time: When the session started
        jobs_found: Total jobs found
        jobs_applied: Successfully applied jobs
        jobs_skipped: Jobs skipped (blacklist, etc.)
        jobs_failed: Failed applications
        questions_answered: Total questions answered
        ai_calls: Number of AI API calls made
    """

    start_time: datetime = field(default_factory=datetime.now)
    jobs_found: int = 0
    jobs_applied: int = 0
    jobs_skipped: int = 0
    jobs_failed: int = 0
    questions_answered: int = 0
    ai_calls: int = 0

    @property
    def end_time(self) -> datetime:
        """Get the current time as end time."""
        return datetime.now()

    @property
    def duration_seconds(self) -> float:
        """Get session duration in seconds."""
        return (self.end_time - self.start_time).total_seconds()

    @property
    def success_rate(self) -> float:
        """Calculate success rate of applications."""
        total = self.jobs_applied + self.jobs_failed
        if total == 0:
            return 0.0
        return (self.jobs_applied / total) * 100

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for logging."""
        return {
            "duration_seconds": str(self.duration_seconds),
            "jobs_found": str(self.jobs_found),
            "jobs_applied": str(self.jobs_applied),
            "jobs_skipped": str(self.jobs_skipped),
            "jobs_failed": str(self.jobs_failed),
            "success_rate": f"{self.success_rate:.1f}%",
            "questions_answered": str(self.questions_answered),
            "ai_calls": str(self.ai_calls),
        }

    def increment_applied(self) -> None:
        """Increment applied counter."""
        self.jobs_applied += 1

    def increment_skipped(self) -> None:
        """Increment skipped counter."""
        self.jobs_skipped += 1

    def increment_failed(self) -> None:
        """Increment failed counter."""
        self.jobs_failed += 1

    def increment_questions(self) -> None:
        """Increment question counter."""
        self.questions_answered += 1

    def increment_ai_calls(self) -> None:
        """Increment AI call counter."""
        self.ai_calls += 1
