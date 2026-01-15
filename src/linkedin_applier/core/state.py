"""
Application State for LinkedIn Auto Job Applier

This module manages application state - counters, flags, and session data.

Usage:
    from src.linkedin_applier.core.state import AppState

    state = AppState()
    state.increment_applied()
    state.increment_skipped()
    stats = state.get_stats()
"""

from datetime import datetime
from typing import Optional

from ..jobs import SessionStats


class AppState:
    """
    Manages application state during a job application session.

    Tracks counters, flags, and provides statistics.

    Attributes:
        stats: SessionStats instance for tracking metrics
        running: Whether the application is currently running
        start_time: When the session started
        current_job_index: Index of current job being processed
        blacklist_companies: Set of blacklisted company names
        rejected_jobs: Set of already rejected job IDs
    """

    def __init__(
        self, blacklist_companies: Optional[set] = None, rejected_jobs: Optional[set] = None
    ):
        """
        Initialize application state.

        Args:
            blacklist_companies: Set of company names to skip
            rejected_jobs: Set of job IDs to skip
        """
        self.stats = SessionStats()
        self.running = False
        self.start_time: Optional[datetime] = None
        self.current_job_index = 0
        self.blacklist_companies = blacklist_companies or set()
        self.rejected_jobs = rejected_jobs or set()

    def start_session(self) -> None:
        """Mark session as started."""
        self.running = True
        self.start_time = datetime.now()
        self.stats = SessionStats()

    def end_session(self) -> dict:
        """Mark session as ended and return final stats."""
        self.running = False
        return self.stats.to_dict()

    def increment_applied(self) -> None:
        """Increment successful applications counter."""
        self.stats.increment_applied()

    def increment_skipped(self) -> None:
        """Increment skipped jobs counter."""
        self.stats.increment_skipped()

    def increment_failed(self) -> None:
        """Increment failed applications counter."""
        self.stats.increment_failed()

    def increment_questions(self) -> None:
        """Increment questions answered counter."""
        self.stats.increment_questions()

    def increment_ai_calls(self) -> None:
        """Increment AI API calls counter."""
        self.stats.increment_ai_calls()

    def get_stats(self) -> dict:
        """Get current session statistics."""
        return self.stats.to_dict()

    def get_success_rate(self) -> float:
        """Get application success rate."""
        return self.stats.success_rate

    def add_blacklist_company(self, company: str) -> None:
        """Add a company to the blacklist."""
        self.blacklist_companies.add(company.lower())

    def is_blacklisted(self, company: str) -> bool:
        """Check if a company is blacklisted."""
        return company.lower() in self.blacklist_companies

    def add_rejected_job(self, job_id: str) -> None:
        """Add a job ID to rejected list."""
        self.rejected_jobs.add(job_id)

    def is_rejected(self, job_id: str) -> bool:
        """Check if a job ID is rejected."""
        return job_id in self.rejected_jobs

    def reset(self) -> None:
        """Reset all counters and flags."""
        self.running = False
        self.start_time = None
        self.current_job_index = 0
        self.stats = SessionStats()


# Global state instance
_state: Optional[AppState] = None


def get_state() -> AppState:
    """Get the global state instance."""
    global _state
    if _state is None:
        _state = AppState()
    return _state


def reset_state() -> None:
    """Reset the global state instance."""
    global _state
    _state = None


if __name__ == "__main__":
    print("Testing AppState...")

    state = AppState()

    # Test session management
    state.start_session()
    print("✓ Session started")

    # Test counters
    state.increment_applied()
    state.increment_applied()
    state.increment_skipped()
    state.increment_failed()

    stats = state.get_stats()
    print(f"✓ Stats: {stats}")
    print(f"✓ Success rate: {state.get_success_rate():.1f}%")

    # Test blacklist
    state.add_blacklist_company("BadCorp")
    print(f"✓ BadCorp blacklisted: {state.is_blacklisted('BadCorp')}")
    print(f"✓ GoodCorp not blacklisted: {not state.is_blacklisted('GoodCorp')}")

    # Test rejected jobs
    state.add_rejected_job("12345")
    print(f"✓ Job 12345 rejected: {state.is_rejected('12345')}")

    # End session
    final_stats = state.end_session()
    print(f"✓ Final stats: {final_stats}")

    print("\n✅ AppState module working correctly!")
