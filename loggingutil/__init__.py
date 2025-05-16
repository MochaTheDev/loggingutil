# DEPENDENCIES
import gzip
import inspect
import json
import os
import random
import threading
import traceback
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional

# LEVEL CLASS


class LogLevel(Enum):
    TRACE = auto()
    DEBUG = auto()
    INFO = auto()
    NOTICE = auto()
    WARN = auto()
    ERROR = auto()
    FATAL = auto()

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented


class LogHandler:
    """Base class for custom log handlers"""

    async def handle(self, log_entry: dict) -> None:
        raise NotImplementedError


class LogFilter:
    """Base class for log filters"""

    def filter(self, log_entry: dict) -> bool:
        raise NotImplementedError


class LogMetrics:
    """Tracks logging metrics"""

    def __init__(self):
        self.log_counts: Dict[LogLevel, int] = {level: 0 for level in LogLevel}
        self.error_counts: Dict[str, int] = {}
        self.last_error_time: Dict[str, datetime] = {}
        self.start_time = datetime.now()

    def record_log(self, level: LogLevel):
        self.log_counts[level] += 1

    def record_error(self, error_type: str):
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        self.last_error_time[error_type] = datetime.now()

    def get_stats(self) -> dict:
        return {
            "uptime": str(datetime.now() - self.start_time),
            "log_counts": {k.name: v for k, v in self.log_counts.items()},
            "error_counts": self.error_counts,
            "last_errors": {k: str(v) for k, v in self.last_error_time.items()},
        }


class LogContext:
    """Thread-local storage for log context"""

    _context = threading.local()

    @classmethod
    def get_context(cls) -> dict:
        if not hasattr(cls._context, "data"):
            cls._context.data = {}
        return cls._context.data

    @classmethod
    def set(cls, **kwargs):
        cls.get_context().update(kwargs)

    @classmethod
    def clear(cls):
        if hasattr(cls._context, "data"):
            cls._context.data.clear()


# MAIN CLASS


class LogFile:
    """Enhanced logging utility that surpasses the standard library logging module."""

    def __init__(
        self,
        filename: str = "logs.log",
        verbose: bool = True,
        max_size_mb: int = 5,
        keep_days: int = 7,
        timestamp_format: str = "[%Y-%m-%d %H:%M:%S.%f]",
        mode: str = "json",
        compress: bool = False,
        use_utc: bool = False,
        include_timestamp: bool = True,
        custom_formatter: Optional[Callable] = None,
        external_stream: Optional[Callable[[str], None]] = None,
        sampling_rate: float = 1.0,
        batch_size: int = 100,
        rotate_time: Optional[str] = None,  # "daily", "hourly", None
        sanitize_keys: List[str] = None,
        schema_validation: bool = False,
    ):

        self.filename = filename
        self.verbose = verbose
        self.max_size = max_size_mb * 1024 * 1024
        self.keep_days = keep_days
        self.timestamp_format = timestamp_format
        self.mode = mode.lower()
        self.compress = compress
        self.use_utc = use_utc
        self.include_timestamp = include_timestamp
        self.custom_formatter = custom_formatter
        self.external_stream = external_stream
        self.sampling_rate = max(0.0, min(1.0, sampling_rate))
        self.batch_size = batch_size
        self.rotate_time = rotate_time
        self.sanitize_keys = sanitize_keys or ["password", "token", "secret", "key"]
        self.schema_validation = schema_validation

        self.buffer = []
        self.buffer_limit = batch_size
        self.level = LogLevel.INFO
        self.handlers: List[LogHandler] = []
        self.filters: List[LogFilter] = []
        self.metrics = LogMetrics()
        self._last_rotation_check = datetime.now()
        self._correlation_id = None

        self.loadfile()
        self.cleanup_old_logs()

    @property
    def correlation_id(self) -> str:
        """Get current correlation ID or generate a new one"""
        if not self._correlation_id:
            self._correlation_id = str(uuid.uuid4())
        return self._correlation_id

    @correlation_id.setter
    def correlation_id(self, value: str):
        self._correlation_id = value

    def add_handler(self, handler: LogHandler):
        """Add a custom log handler"""
        self.handlers.append(handler)

    def add_filter(self, log_filter: LogFilter):
        """Add a custom log filter"""
        self.filters.append(log_filter)

    def should_sample(self) -> bool:
        """Check if this log entry should be sampled."""
        return (
            self.sampling_rate >= 1.0
            or random.random() < self.sampling_rate
        )

    def _sanitize_data(self, data: Any) -> Any:
        """Recursively sanitize sensitive data"""
        if isinstance(data, dict):
            return {
                k: (
                    "***REDACTED***"
                    if k in self.sanitize_keys
                    else self._sanitize_data(v)
                )
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        return data

    def _get_caller_info(self) -> dict:
        """Get information about the calling function"""
        stack = inspect.stack()
        # Skip this function and internal logging functions
        for frame_info in stack[2:]:
            if "logging" not in frame_info.filename:
                return {
                    "file": os.path.basename(frame_info.filename),
                    "function": frame_info.function,
                    "line": frame_info.lineno,
                }
        return {}

    def format_log_entry(
        self,
        timestamp: str,
        level: LogLevel,
        tag: str,
        data: Any,
        context_str: str,
    ) -> str:
        """Format a log entry as a string."""
        return (
            f"{timestamp} [{level.name}] [{self.correlation_id}] "
            f"{tag or ''} {context_str} {data}\n"
        )

    async def _handle_async(self, entry: dict):
        """Process log entry through async handlers"""
        for handler in self.handlers:
            try:
                await handler.handle(entry)
            except Exception as e:
                print(f"Handler error: {e}")

    @contextmanager
    def context(self, **kwargs):
        """Context manager for adding temporary context to logs"""
        previous = dict(LogContext.get_context())
        LogContext.set(**kwargs)
        try:
            yield
        finally:
            LogContext._context.data = previous

    @contextmanager
    def correlation(self, correlation_id: str):
        """Context manager for setting correlation ID"""
        previous = self._correlation_id
        self._correlation_id = correlation_id
        try:
            yield
        finally:
            self._correlation_id = previous

    def get_metrics(self) -> dict:
        """Get current logging metrics"""
        return self.metrics.get_stats()

    def structured(self, **kwargs):
        """Log structured data with schema validation"""
        if self.schema_validation:
            # Add schema validation logic here
            pass
        self.log(kwargs)

    def _print(self, msg):
        if self.verbose:
            print(f"LoggingUtility :: {msg}")

    def loadfile(self):
        """Initialize/create log file if it is destroyed."""
        if not os.path.exists(self.filename):
            with open(self.filename, "w") as f:
                f.write("LoggingUtility::LOGFILE_INIT\n")
            self._print(f"Created new log file: {self.filename}")

    def setLevel(self, level: LogLevel) -> None:
        """Sets default output level (used if no level passed to .log())
        
        Example:
        logfile = loggingutil.LogFile()
        logfile.setLevel(logfile.notice)
        """
        if isinstance(level, LogLevel):
            self.level = level

    def getLevel(self):
        return self.level

    def levelEquiv(self, level):
        return level.name if isinstance(level, LogLevel) else str(level)

    def _rotate_if_needed(self):
        if (
            os.path.exists(self.filename)
            and os.path.getsize(self.filename) >= self.max_size
        ):
            timestamp = (
                datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                if self.use_utc
                else datetime.now().strftime("%Y%m%d_%H%M%S")
            )
            base, ext = os.path.splitext(self.filename)
            rotated_name = (
                f"{base}_{timestamp}{ext}.gz"
                if self.compress
                else f"{base}_{timestamp}{ext}"
            )
            with open(self.filename, "rb") as f_in:
                with (
                    gzip.open(rotated_name, "wb")
                    if self.compress
                    else open(rotated_name, "wb")
                ) as f_out:
                    f_out.write(f_in.read())
            os.remove(self.filename)
            self._print(f"Log rotated: {rotated_name}")

    def cleanup_old_logs(self):
        base, _ = os.path.splitext(self.filename)
        now = datetime.utcnow() if self.use_utc else datetime.now()
        for file in os.listdir("."):
            if file.startswith(base + "_"):
                try:
                    timestamp_str = file.split("_")[-1].split(".")[0]
                    file_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    if now - file_time > timedelta(days=self.keep_days):
                        os.remove(file)
                        self._print(f"Deleted old log file: {file}")
                except Exception:
                    continue

    def _get_timestamp(self):
        now = datetime.utcnow() if self.use_utc else datetime.now()
        return now.strftime(self.timestamp_format) if self.include_timestamp else ""

    def _check_time_rotation(self):
        """Check if log file should be rotated based on time"""
        if not self.rotate_time:
            return

        now = datetime.now()
        if self.rotate_time == "daily":
            if now.date() > self._last_rotation_check.date():
                self._rotate_log()
        elif self.rotate_time == "hourly":
            if now.hour > self._last_rotation_check.hour:
                self._rotate_log()

        self._last_rotation_check = now

    def _rotate_log(self):
        """Rotate log file"""
        if not os.path.exists(self.filename):
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base, ext = os.path.splitext(self.filename)
        rotated_name = f"{base}_{timestamp}{ext}"

        if self.compress:
            rotated_name += ".gz"
            with open(self.filename, "rb") as f_in:
                with gzip.open(rotated_name, "wb") as f_out:
                    f_out.write(f_in.read())
        else:
            os.rename(self.filename, rotated_name)

        with open(self.filename, "w") as f:
            f.write(f"Log file rotated from {rotated_name}\n")

        self._print(f"Log rotated: {rotated_name}")

    def log(self, data: Any, level: LogLevel = None, tag: str = None):
        """Enhanced log method with filtering and metrics"""
        if level is None:
            level = self.level

        if not self.should_sample():
            return

        if not data:
            raise ValueError("No data provided")

        # Apply filters
        log_entry = {
            "level": level,
            "tag": tag,
            "data": data,
            "timestamp": self._get_timestamp(),
        }

        for log_filter in self.filters:
            if not log_filter.filter(log_entry):
                return

        entry = self.format_log_entry(
            self._get_timestamp(),
            level,
            tag,
            self._sanitize_data(data),
            " ".join(f"{k}={v}" for k, v in LogContext.get_context().items())
        )
        self.buffer.append(entry)
        self.metrics.record_log(level)

        if len(self.buffer) >= self.buffer_limit:
            self.flush()

        # Check for time-based rotation
        self._check_time_rotation()

    async def async_batch_log(self, entries: List[tuple]):
        """Log multiple entries asynchronously"""

        async def process_batch(batch):
            for data, level, tag in batch:
                await self.async_log(data, level, tag)

        batch_size = self.batch_size
        for i in range(0, len(entries), batch_size):
            batch = entries[i : i + batch_size]
            await process_batch(batch)

    def flush(self):
        """Clears the buffer and dumps current buffer data to log file."""
        if not self.buffer:
            return

        for entry in self.buffer:
            self._write(entry)
        self.buffer.clear()
        self._print("Buffer flushed to file.")

    async def async_log(self, data, level: LogLevel = None, tag=None):
        if level is None:
            level = self.getLevel()

        """Coroutine log function"""
        self.log(data, level, tag)

    async def async_log_http_response(self, resp, level: LogLevel = None, tag="HTTP"):
        """Log HTTP responses from APIs"""
        if level == None:
            level = self.getLevel()
        try:
            info = {
                "status": resp.status,
                "headers": dict(resp.headers),
                "body": await resp.text(),
            }
            self.log(info, level=level, tag=tag)
        except Exception as e:
            self.log_exception(e)

    def log_exception(self, err, tag="EXCEPTION"):
        """For logging specifically exceptions as errors."""
        tb = traceback.format_exc()
        data = {"error": str(err), "traceback": tb}
        self.log(data, level=LogLevel.ERROR, tag=tag)

    def wipe(self):
        """Completely clear the log file."""
        self.flush()
        with open(self.filename, "w"):
            pass
        self._print(f"File {self.filename} has been wiped.")

    def __enter__(self):
        self._correlation_id = str(uuid.uuid4())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.flush()
        if exc_type:
            self.log_exception(exc_val)
        self._correlation_id = None

    def __repr__(self):
        return f"<LogFile filename='{self.filename}' mode='{self.mode}' level='{self.levelEquiv(self.getLevel())}'>"

    def __str__(self):
        return f"LogFile({self.filename})"

    def increment_error_count(self, error_type: str) -> None:
        """Increment error count for a specific error type."""
        self.metrics.record_error(error_type)

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp from filename."""
        file_time = datetime.strptime(
            timestamp_str,
            "%Y%m%d_%H%M%S"
        )
        return file_time

    def _format_timestamp(self) -> str:
        """Format current timestamp."""
        now = datetime.now()
        return (
            now.strftime(self.timestamp_format)
            if self.include_timestamp
            else ""
        )

    def _process_batch(self, entries: List[dict], batch_size: int = 100):
        """Process a batch of log entries."""
        for i in range(0, len(entries), batch_size):
            batch = entries[i:i + batch_size]
            # ... rest of the method
