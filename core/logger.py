"""Logging system for Hades backup operations."""

from datetime import datetime
from typing import List, Tuple

from .constants import LOG_FILE, MAX_LOG_ENTRIES


class Logger:
    """Simple logging system for Hades backup operations."""

    def __init__(self) -> None:
        self.logs: List[Tuple[datetime, str, str]] = []  # (timestamp, level, message)
        self.max_logs = MAX_LOG_ENTRIES

    def log(self, level: str, message: str) -> None:
        """Add a log entry."""
        timestamp = datetime.now()
        entry = (timestamp, level, message)
        self.logs.append(entry)

        # Keep only the last max_logs entries
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs :]

        # Also write to file
        self._write_to_file(timestamp, level, message)

    def info(self, message: str) -> None:
        """Log an info message."""
        self.log("INFO", message)

    def error(self, message: str) -> None:
        """Log an error message."""
        self.log("ERROR", message)

    def success(self, message: str) -> None:
        """Log a success message."""
        self.log("SUCCESS", message)

    def debug(self, message: str) -> None:
        """Log a debug message."""
        # Debug mode is currently disabled by default
        # To enable, uncomment the settings check below
        # user_settings = get_settings()
        # if user_settings.get("debug_mode", False):
        self.log("DEBUG", message)

    def warning(self, message: str) -> None:
        """Log a warning message."""
        self.log("WARNING", message)

    def get_recent_logs(self, count: int = 10) -> List[str]:
        """Get recent log entries as formatted strings."""
        recent = self.logs[-count:] if self.logs else []
        return [
            f"[{ts.strftime('%H:%M:%S')}] {level}: {msg}" for ts, level, msg in recent
        ]

    def clear(self) -> None:
        """Clear all logs."""
        self.logs.clear()

    def _write_to_file(self, timestamp: datetime, level: str, message: str) -> None:
        """Write log entry to file."""
        try:
            from .constants import BACKUP_SAVE_ROOT

            BACKUP_SAVE_ROOT.mkdir(parents=True, exist_ok=True)
            log_line = f"{timestamp.isoformat()} {level}: {message}\n"
            with LOG_FILE.open("a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception:
            # Don't let logging errors break the application
            pass


# Global logger instance
logger = Logger()
