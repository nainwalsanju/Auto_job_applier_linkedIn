"""
Test Suite for LinkedIn Auto Job Applier Refactored Code

Run this to verify all components are working correctly:
    python3 test_refactored_code.py
"""

import sys
import unittest
from pathlib import Path
from datetime import datetime

sys.path.insert(0, "/Users/sanju/Projects/Auto_job_applier_linkedIn")


class TestJobModels(unittest.TestCase):
    """Test job-related data models."""

    def test_job_details_creation(self):
        from src.linkedin_applier.jobs import JobDetails

        job = JobDetails(
            job_id="123",
            title="Python Developer",
            company="Google",
            work_location="Remote",
            work_style="Full-time",
            experience_required=5,
            skills=["Python", "AWS"],
        )

        self.assertEqual(job.job_id, "123")
        self.assertEqual(job.title, "Python Developer")
        self.assertEqual(job.experience_required, 5)
        self.assertEqual(len(job.skills), 2)

    def test_job_details_csv_export(self):
        from src.linkedin_applier.jobs import JobDetails

        job = JobDetails(
            job_id="456",
            title="Backend Developer",
            company="Meta",
            work_location="Hybrid",
            work_style="Full-time",
            skills=["Python", "Go", "SQL"],
        )

        csv_dict = job.to_csv_dict()
        self.assertEqual(csv_dict["job_id"], "456")
        self.assertIn("Python", csv_dict["skills"])

    def test_application_result(self):
        from src.linkedin_applier.jobs import (
            JobDetails,
            ApplicationResult,
            ApplicationType,
        )

        job = JobDetails(
            job_id="789",
            title="DevOps Engineer",
            company="Amazon",
            work_location="Seattle",
            work_style="Full-time",
        )

        result = ApplicationResult(
            job=job,
            applied=True,
            application_type=ApplicationType.EASY_APPLY.value,
            questions_answered=[{"Q": "Experience?", "A": "3 years"}],
        )

        self.assertTrue(result.applied)
        self.assertEqual(result.application_type, "Easy Apply")
        self.assertEqual(len(result.questions_answered), 1)

    def test_session_stats(self):
        from src.linkedin_applier.jobs import SessionStats

        stats = SessionStats()
        stats.jobs_applied = 10
        stats.jobs_skipped = 5
        stats.jobs_failed = 2

        self.assertEqual(stats.jobs_applied, 10)
        self.assertAlmostEqual(stats.success_rate, 83.333, places=1)  # 10/12 * 100
        self.assertGreater(stats.duration_seconds, 0)


class TestExceptions(unittest.TestCase):
    """Test custom exception hierarchy."""

    def test_exception_hierarchy(self):
        from src.linkedin_applier.exceptions import (
            LinkedInApplierError,
            BrowserError,
            ElementNotFoundError,
            ApplicationError,
            AIError,
            ConfigurationError,
        )

        self.assertTrue(issubclass(ElementNotFoundError, BrowserError))
        self.assertTrue(issubclass(BrowserError, LinkedInApplierError))
        self.assertTrue(issubclass(ApplicationError, LinkedInApplierError))
        self.assertTrue(issubclass(AIError, LinkedInApplierError))
        self.assertTrue(issubclass(ConfigurationError, LinkedInApplierError))

    def test_element_not_found_exception(self):
        from src.linkedin_applier.exceptions import ElementNotFoundError

        exc = ElementNotFoundError(
            "Submit button not found", selector="#submit", timeout=10
        )

        self.assertEqual(exc.message, "Submit button not found")
        self.assertEqual(exc.details["selector"], "#submit")
        self.assertEqual(exc.details["timeout"], 10)

    def test_blacklist_match_exception(self):
        from src.linkedin_applier.exceptions import BlacklistMatchError

        exc = BlacklistMatchError(
            "Company in blacklist", details={"company": "BadCorp"}
        )

        self.assertIn("blacklist", exc.message.lower())
        self.assertEqual(exc.details["company"], "BadCorp")

    def test_exception_to_dict(self):
        from src.linkedin_applier.exceptions import AIConnectionError

        exc = AIConnectionError(
            "API failed", details={"provider": "openai"}, code="ERR_001"
        )

        exc_dict = exc.to_dict()
        self.assertEqual(exc_dict["error_type"], "AIConnectionError")
        self.assertEqual(exc_dict["message"], "API failed")
        self.assertEqual(exc_dict["code"], "ERR_001")


class TestStructuredLogger(unittest.TestCase):
    """Test structured logging."""

    def test_logger_initialization(self):
        from src.linkedin_applier.utils.logger import setup_logging, log

        logger = setup_logging(log_dir="logs", log_level="INFO", console_output=False)

        self.assertIsNotNone(logger)

    def test_logger_methods(self):
        from src.linkedin_applier.utils.logger import setup_logging

        logger = setup_logging(log_dir="logs", log_level="DEBUG", console_output=False)

        # These should not raise errors
        logger.debug("Debug message", key="value")
        logger.info("Info message", count=5)
        logger.warning("Warning message")
        logger.error("Error message", error="test")
        logger.critical("Critical message")

    def test_convenience_methods(self):
        from src.linkedin_applier.utils.logger import setup_logging

        logger = setup_logging(log_dir="logs", log_level="INFO", console_output=False)

        logger.job_applied(job_id="123", title="Developer", company="TechCorp")

        logger.job_skipped(job_id="456", reason="Blacklisted")

        logger.job_failed(job_id="789", error="Timeout")

        logger.session_started(search_terms=["Python"], location="Remote")

        logger.session_ended(stats={"applied": 5, "failed": 1})


class TestResultTracker(unittest.TestCase):
    """Test result tracking."""

    def setUp(self):
        from src.linkedin_applier.utils.result_tracker import reset_tracker

        reset_tracker()

    def test_tracker_initialization(self):
        from src.linkedin_applier.utils.result_tracker import ResultTracker

        tracker = ResultTracker(results_dir=Path("results/test"))

        self.assertTrue(tracker.get_results_dir().exists())
        self.assertTrue(tracker.get_applied_file().exists())
        self.assertTrue(tracker.get_failed_file().exists())

    def test_save_applied(self):
        from src.linkedin_applier.utils.result_tracker import ResultTracker
        from src.linkedin_applier.jobs import JobDetails

        tracker = ResultTracker(results_dir=Path("results/test2"))

        job = JobDetails(
            job_id="test001",
            title="Developer",
            company="TestCorp",
            work_location="Remote",
            work_style="Full-time",
        )

        tracker.save_applied(job, questions_answered=[{"Q": "Exp?", "A": "5y"}])

        self.assertEqual(tracker.get_applied_count(), 1)

    def test_save_failed(self):
        from src.linkedin_applier.utils.result_tracker import ResultTracker
        from src.linkedin_applier.jobs import JobDetails

        tracker = ResultTracker(results_dir=Path("results/test3"))

        job = JobDetails(
            job_id="test002",
            title="Developer",
            company="TestCorp",
            work_location="Remote",
            work_style="Full-time",
        )

        tracker.save_failed(job, error="Timeout")

        self.assertEqual(tracker.get_failed_count(), 1)

    def test_session_stats(self):
        from src.linkedin_applier.utils.result_tracker import ResultTracker
        from src.linkedin_applier.jobs import JobDetails

        tracker = ResultTracker(results_dir=Path("results/test4"))

        job = JobDetails(
            job_id="test003",
            title="Developer",
            company="TestCorp",
            work_location="Remote",
            work_style="Full-time",
        )

        tracker.save_applied(job)
        tracker.save_applied(job)
        tracker.save_skipped(job, "Test reason")
        tracker.save_failed(job, "Error")

        stats = tracker.get_session_stats()
        self.assertEqual(stats["jobs_applied"], "2")
        self.assertEqual(stats["jobs_skipped"], "1")
        self.assertEqual(stats["jobs_failed"], "1")

    def test_singleton(self):
        from src.linkedin_applier.utils.result_tracker import get_tracker

        tracker1 = get_tracker()
        tracker2 = get_tracker()

        self.assertIs(tracker1, tracker2)


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with original code."""

    def test_original_imports(self):
        from config import personals, questions, search, settings, secrets
        from modules import helpers, clickers_and_finders, validator
        from modules.ai import openaiConnections, deepseekConnections, geminiConnections

        self.assertTrue(True)  # If we got here, imports work

    def test_secrets_compatibility(self):
        from config.secrets import username, password, use_AI, ai_provider

        # These should be loaded from secure_config
        self.assertIsInstance(username, str)
        self.assertIsInstance(password, str)
        self.assertIsInstance(use_AI, bool)
        self.assertIsInstance(ai_provider, str)

    def test_runaibot_import(self):
        import runAiBot

        # Should have all original functions
        self.assertTrue(hasattr(runAiBot, "main"))
        self.assertTrue(hasattr(runAiBot, "run"))

    def test_flask_import(self):
        import app

        self.assertTrue(hasattr(app, "app"))


if __name__ == "__main__":
    print("=" * 60)
    print("Running LinkedIn Auto Job Applier Test Suite")
    print("=" * 60)

    # Run tests with verbosity
    unittest.main(verbosity=2, exit=False)

    print("\\n" + "=" * 60)
    print("Test run complete!")
    print("=" * 60)
