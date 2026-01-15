"""
Structured Logging Module for LinkedIn Auto Job Applier

This module provides structured logging using structlog for better
log analysis, debugging, and monitoring.

Usage:
    from src.linkedin_applier.utils.logger import setup_logging, log

    setup_logging(log_dir="logs", log_level="INFO")
    log.info("job_applied", job_id="123", company="Google")
    log.error("application_failed", error="Timeout", job_id="456")
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

try:
    import structlog

    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False
    structlog = None


class Logger:
    """
    Structured logger wrapper that provides both structured and simple logging.

    Attributes:
        logger: The underlying logger instance
        log_file: Path to the current log file
    """

    def __init__(self, name: str = "linkedin_applier"):
        self.name = name
        self.logger = None
        self.log_file: Optional[Path] = None
        self._initialized = False

    def setup(
        self,
        log_dir: Path = Path("logs"),
        log_level: str = "INFO",
        json_format: bool = False,
        console_output: bool = True,
    ) -> None:
        """
        Initialize structured logging.

        Args:
            log_dir: Directory for log files
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            json_format: Use JSON format (True) or console format (False)
            console_output: Also output to console
        """
        if self._initialized:
            return

        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create timestamped log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = log_dir / f"applier_{timestamp}.log"

        if STRUCTLOG_AVAILABLE:
            # PHASE 2: Lightweight processors for performance (removed heavy ones)
            processors = [
                structlog.processors.add_log_level,
                # Simplified timestamp (removed ISO format complexity)
                structlog.processors.TimeStamper(fmt="%H:%M:%S", key="time"),
            ]

            if json_format:
                processors.append(structlog.processors.JSONRenderer())
            elif console_output:
                # Disabled colors for speed
                processors.append(structlog.dev.ConsoleRenderer(colors=False))

            # PHASE 3: Async buffered file writer (replaces blocking write_to_file)
            import threading
            import queue

            self._log_queue = queue.Queue()
            self._stop_event = threading.Event()

            def async_file_writer():
                """Background thread for buffered file writing."""
                buffer = []
                while not self._stop_event.is_set() or not self._log_queue.empty():
                    try:
                        # Collect logs in buffer
                        while len(buffer) < 10 and not self._log_queue.empty():
                            log_entry = self._log_queue.get(timeout=0.1)
                            if log_entry:
                                buffer.append(log_entry)

                        # Batch write to file
                        if buffer and self.log_file:
                            try:
                                with open(self.log_file, "a", encoding="utf-8") as f:
                                    f.write("\n".join(buffer) + "\n")
                                buffer.clear()
                            except Exception:
                                pass
                    except:
                        pass

            # Start background writer thread
            self._writer_thread = threading.Thread(target=async_file_writer, daemon=True)
            self._writer_thread.start()

            def write_to_file_async(logger, method_name, event_dict):
                """Async file writer - queues logs instead of blocking."""
                if self.log_file and event_dict:
                    self._log_queue.put(str(event_dict))
                return event_dict

            processors.append(write_to_file_async)

            # Use standard logging levels since structlog doesn't have them
            import logging

            log_level_map = {
                "DEBUG": logging.DEBUG,
                "INFO": logging.INFO,
                "WARNING": logging.WARNING,
                "ERROR": logging.ERROR,
                "CRITICAL": logging.CRITICAL,
            }
            log_level_enum = log_level_map.get(log_level.upper(), logging.INFO)

            try:
                structlog.configure(
                    processors=processors,
                    wrapper_class=structlog.make_filtering_bound_logger(log_level_enum),
                    logger_factory=structlog.PrintLoggerFactory(
                        file=sys.stderr if console_output else open(os.devnull, "w")
                    ),
                    cache_logger_on_first_use=True,
                )
            except AttributeError:
                # Fallback if structlog methods don't exist
                structlog.configure(
                    processors=processors,
                    logger_factory=structlog.PrintLoggerFactory(
                        file=sys.stderr if console_output else open(os.devnull, "w")
                    ),
                    cache_logger_on_first_use=True,
                )

        self.logger = structlog.get_logger(self.name) if STRUCTLOG_AVAILABLE else None

    def close(self):
        """Clean shutdown - flush logs and stop background thread."""
        if hasattr(self, "_stop_event"):
            self._stop_event.set()
        if hasattr(self, "_writer_thread") and self._writer_thread.is_alive():
            self._writer_thread.join(timeout=1.0)
        self._initialized = True

    def _log(self, level: str, message: str, **kwargs) -> None:
        """Internal logging method."""
        if not self._initialized:
            self.setup()

        if self.logger and STRUCTLOG_AVAILABLE:
            getattr(self.logger, level.lower())(message, **kwargs)
        else:
            # Fallback to simple print
            timestamp = datetime.now().isoformat()
            log_line = f"[{timestamp}] {level}: {message}"
            if kwargs:
                log_line += f" | {kwargs}"
            print(log_line)

            # Write to file
            if self.log_file:
                try:
                    with open(self.log_file, "a", encoding="utf-8") as f:
                        f.write(log_line + "\n")
                except Exception:
                    pass

    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message."""
        self._log("DEBUG", message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log an info message."""
        self._log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message."""
        self._log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log an error message."""
        self._log("ERROR", message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Log a critical message."""
        self._log("CRITICAL", message, **kwargs)

    def exception(self, message: str, exc: Exception, **kwargs) -> None:
        """Log an exception with traceback."""
        self._log("ERROR", message, exception=str(exc), **kwargs)

    def job_applied(self, job_id: str, title: str, company: str, **kwargs) -> None:
        """Log a successful job application."""
        self.info(
            "Job applied successfully",
            job_id=job_id,
            title=title,
            company=company,
            **kwargs,
        )

    def job_skipped(self, job_id: str, reason: str, **kwargs) -> None:
        """Log a skipped job."""
        self.info("Job skipped", job_id=job_id, reason=reason, **kwargs)

    def job_failed(self, job_id: str, error: str, **kwargs) -> None:
        """Log a failed job application."""
        self.error("Job application failed", job_id=job_id, error=error, **kwargs)

    def session_started(self, search_terms: list[str], location: str, **kwargs) -> None:
        """Log session start."""
        self.info("Session started", search_terms=search_terms, location=location, **kwargs)

    def session_ended(self, stats: dict, **kwargs) -> None:
        """Log session end with statistics."""
        self.info("Session ended", stats=stats, **kwargs)


# Global logger instance
log = Logger()


def setup_logging(
    log_dir: str = "logs",
    log_level: str = "INFO",
    json_format: bool = False,
    console_output: bool = True,
) -> Logger:
    """
    Set up structured logging for the application.

    Args:
        log_dir: Directory for log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        json_format: Use JSON format for logs
        console_output: Output logs to console

    Returns:
        Configured Logger instance
    """
    log.setup(
        log_dir=Path(log_dir),
        log_level=log_level,
        json_format=json_format,
        console_output=console_output,
    )
    return log


def get_logger(name: str = "linkedin_applier") -> Logger:
    """
    Get a named logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return Logger(name)


# Convenience function for backward compatibility
def print_lg(*msgs: Any, end: str = "\n", pretty: bool = False, flush: bool = False) -> None:
    """
    Legacy logging function for backward compatibility.
    Maps to the new structured logger.

    Args:
        *msgs: Messages to log
        end: Line ending
        pretty: Use pretty printing (ignored in new logger)
        flush: Flush immediately
    """
    if not log._initialized:
        log.setup()

    for msg in msgs:
        if isinstance(msg, Exception):
            log.exception("Error occurred", msg)
        else:
            log.info(str(msg))


# Import os for file operations
import os


if __name__ == "__main__":
    # Demo/test the logger
    setup_logging(log_dir="logs", log_level="INFO", console_output=True)

    log.info("Logger initialized", module="logger")
    log.job_applied(job_id="12345", title="Python Developer", company="Google")
    log.job_skipped(job_id="67890", reason="Blacklisted company")
    log.job_failed(job_id="11111", error="Timeout waiting for element")

    log.session_started(search_terms=["Python Developer", "Software Engineer"], location="Remote")

    stats = {
        "jobs_applied": 10,
        "jobs_skipped": 5,
        "jobs_failed": 2,
        "success_rate": "83.3%",
    }
    log.session_ended(stats=stats)

    print(f"\nLog file: {log.log_file}")
