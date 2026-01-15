"""
Result Tracker for LinkedIn Auto Job Applier

This module tracks and persists application results to CSV files.
Provides session statistics and history tracking.

Usage:
    from src.linkedin_applier.utils.result_tracker import ResultTracker

    tracker = ResultTracker(results_dir="results")
    tracker.save_applied(job, questions_answered)
    tracker.save_failed(job, error)
    stats = tracker.get_session_stats()
"""

import csv
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from ..jobs import JobDetails, ApplicationResult, SessionStats, ApplicationType


class ResultTracker:
    """
    Track and persist job application results.

    Attributes:
        results_dir: Directory for results files
        applied_file: CSV file for successful applications
        failed_file: CSV file for failed applications
        session_file: JSON file for session statistics
    """

    def __init__(
        self,
        results_dir: Path = Path("results"),
        applied_filename: str = "applied_jobs.csv",
        failed_filename: str = "failed_jobs.csv",
        session_filename: Optional[str] = None,
    ):
        """
        Initialize the result tracker.

        Args:
            results_dir: Directory for results
            applied_filename: Name of applied jobs CSV file
            failed_filename: Name of failed jobs CSV file
            session_filename: Name of session JSON file (auto-generated if None)
        """
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        self.applied_file = self.results_dir / applied_filename
        self.failed_file = self.results_dir / failed_filename

        if session_filename:
            self.session_file = self.results_dir / session_filename
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.session_file = self.results_dir / f"session_{timestamp}.json"

        self._init_csv_files()
        self.session_stats = SessionStats()

    def _init_csv_files(self) -> None:
        """Initialize CSV files with headers if they don't exist."""
        applied_headers = [
            "job_id",
            "title",
            "company",
            "work_location",
            "work_style",
            "experience_required",
            "skills",
            "applied",
            "application_type",
            "external_link",
            "date_applied",
            "questions_count",
            "error",
        ]

        failed_headers = [
            "job_id",
            "title",
            "company",
            "work_location",
            "work_style",
            "experience_required",
            "skills",
            "error",
            "date_attempted",
            "screenshots",
            "notes",
        ]

        if not self.applied_file.exists():
            with open(self.applied_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=applied_headers)
                writer.writeheader()

        if not self.failed_file.exists():
            with open(self.failed_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=failed_headers)
                writer.writeheader()

    def save_applied(
        self,
        job: JobDetails,
        application_type: str = ApplicationType.EASY_APPLY.value,
        questions_answered: Optional[list] = None,
        external_link: Optional[str] = None,
    ) -> None:
        """
        Save a successful job application.

        Args:
            job: JobDetails instance
            application_type: Type of application
            questions_answered: List of answered questions
            external_link: Link to external application (if applicable)
        """
        result = ApplicationResult(
            job=job,
            applied=True,
            application_type=application_type,
            questions_answered=questions_answered or [],
            external_link=external_link,
        )

        with open(self.applied_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=result.to_csv_dict().keys())
            writer.writerow(result.to_csv_dict())

        self.session_stats.increment_applied()

    def save_failed(
        self,
        job: JobDetails,
        error: str,
        notes: Optional[str] = None,
        screenshot_path: Optional[str] = None,
    ) -> None:
        """
        Save a failed job application.

        Args:
            job: JobDetails instance
            error: Error message
            notes: Additional notes
            screenshot_path: Path to screenshot
        """
        row = {
            "job_id": job.job_id,
            "title": job.title,
            "company": job.company,
            "work_location": job.work_location,
            "work_style": job.work_style,
            "experience_required": str(job.experience_required or ""),
            "skills": ", ".join(job.skills),
            "error": error,
            "date_attempted": datetime.now().isoformat(),
            "screenshots": screenshot_path or "",
            "notes": notes or "",
        }

        with open(self.failed_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            writer.writerow(row)

        self.session_stats.increment_failed()

    def save_skipped(self, job: JobDetails, reason: str) -> None:
        """
        Save a skipped job (e.g., blacklist match).

        Args:
            job: JobDetails instance
            reason: Reason for skipping
        """
        # Skipped jobs are logged but not persisted to CSV
        # They are included in session statistics
        self.session_stats.increment_skipped()

    def save_session(self) -> dict:
        """
        Save session statistics to JSON file.

        Returns:
            Session statistics dictionary
        """
        stats_dict = self.session_stats.to_dict()
        stats_dict["start_time"] = self.session_stats.start_time.isoformat()
        stats_dict["end_time"] = self.session_stats.end_time.isoformat()
        stats_dict["timestamp"] = datetime.now().isoformat()

        with open(self.session_file, "w", encoding="utf-8") as f:
            json.dump(stats_dict, f, indent=2)

        return stats_dict

    def get_session_stats(self) -> dict:
        """
        Get current session statistics.

        Returns:
            Dictionary with session statistics
        """
        return self.session_stats.to_dict()

    def get_applied_count(self) -> int:
        """Get count of successful applications."""
        return self.session_stats.jobs_applied

    def get_failed_count(self) -> int:
        """Get count of failed applications."""
        return self.session_stats.jobs_failed

    def get_skipped_count(self) -> int:
        """Get count of skipped applications."""
        return self.session_stats.jobs_skipped

    def get_success_rate(self) -> float:
        """Get application success rate."""
        return self.session_stats.success_rate

    def get_results_dir(self) -> Path:
        """Get the results directory path."""
        return self.results_dir

    def get_applied_file(self) -> Path:
        """Get the applied jobs CSV file path."""
        return self.applied_file

    def get_failed_file(self) -> Path:
        """Get the failed jobs CSV file path."""
        return self.failed_file

    def get_session_file(self) -> Path:
        """Get the session JSON file path."""
        return self.session_file

    def reset_session(self) -> None:
        """Reset session statistics for a new session."""
        self.session_stats = SessionStats()


# Singleton instance for convenience
_default_tracker: Optional[ResultTracker] = None


def get_tracker(results_dir: str = "results") -> ResultTracker:
    """
    Get the default result tracker instance.

    Args:
        results_dir: Results directory path

    Returns:
        ResultTracker instance
    """
    global _default_tracker
    if _default_tracker is None:
        _default_tracker = ResultTracker(results_dir=Path(results_dir))
    return _default_tracker


def reset_tracker() -> None:
    """Reset the default tracker instance."""
    global _default_tracker
    _default_tracker = None


if __name__ == "__main__":
    # Demo/test the result tracker
    tracker = ResultTracker(results_dir="results")

    print(f"Results directory: {tracker.get_results_dir()}")
    print(f"Applied file: {tracker.get_applied_file()}")
    print(f"Failed file: {tracker.get_failed_file()}")
    print(f"Session file: {tracker.get_session_file()}")

    # Create a test job
    job = JobDetails(
        job_id="test123",
        title="Test Developer",
        company="Test Corp",
        work_location="Remote",
        work_style="Full-time",
        skills=["Python", "Testing"],
    )

    # Test saving
    tracker.save_applied(job, questions_answered=[{"Q": "Experience?", "A": "5 years"}])
    print(f"\nApplied count: {tracker.get_applied_count()}")
    print(f"Session stats: {tracker.get_session_stats()}")

    # Save session
    stats = tracker.save_session()
    print(f"\nSession saved to: {tracker.get_session_file()}")
    print(f"Final stats: {stats}")

    print("\n✅ Result tracker working correctly!")
