import logging
import json
from typing import Any, Dict, Optional
from loggingutil import LogLevel, LogContext


class LoggingUtilHandler(logging.Handler):
    """Handler to bridge stdlib logging with LoggingUtil.

    This handler allows using LoggingUtil as a backend for the standard
    logging module while preserving all advanced features.

    Example:
        import logging
        import loggingutil

        # Create LogFile instance
        logfile = loggingutil.LogFile("app.log")

        # Create handler and add to logger
        handler = LoggingUtilHandler(logfile)
        logger = logging.getLogger("myapp")
        logger.addHandler(handler)

        # Use standard logging - it will use LoggingUtil features
        logger.info("Hello world", extra={"user_id": "123"})
    """

    def __init__(self, logfile_instance):
        super().__init__()
        self.logfile = logfile_instance

        # Map stdlib levels to LoggingUtil levels
        self.level_map = {
            logging.NOTSET: LogLevel.TRACE,
            logging.DEBUG: LogLevel.DEBUG,
            logging.INFO: LogLevel.INFO,
            logging.WARNING: LogLevel.WARN,
            logging.ERROR: LogLevel.ERROR,
            logging.CRITICAL: LogLevel.FATAL,
        }

    def _get_structured_data(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Extract structured data from the log record."""
        data = {
            "message": record.getMessage(),
            "logger_name": record.name,
            "module": record.module,
            "func_name": record.funcName,
            "line_no": record.lineno,
            "thread_id": record.thread,
            "thread_name": record.threadName,
            "process_id": record.process,
            "process_name": record.processName,
        }

        # Add exception info if present
        if record.exc_info:
            data["exception"] = {
                "type": str(record.exc_info[0].__name__),
                "message": str(record.exc_info[1]),
                "traceback": self.formatter.formatException(record.exc_info),
            }

        # Add any extra attributes from record
        if hasattr(record, "extra"):
            data.update(record.extra)

        # Add any custom attributes set via extra keyword
        for key, value in record.__dict__.items():
            if key not in logging.LogRecord.__dict__ and key not in data:
                data[key] = value

        return data

    def emit(self, record: logging.LogRecord):
        """Process a log record by converting it to LoggingUtil format."""
        try:
            # Get corresponding LoggingUtil level
            level = self.level_map.get(record.levelno, LogLevel.INFO)

            # Extract structured data
            data = self._get_structured_data(record)

            # If record has extra context, add it to LogContext
            context_data = {}
            for key, value in record.__dict__.items():
                if key not in logging.LogRecord.__dict__:
                    context_data[key] = value

            # Use context manager if we have extra context
            if context_data:
                with self.logfile.context(**context_data):
                    self.logfile.log(data, level=level, tag=record.name)
            else:
                self.logfile.log(data, level=level, tag=record.name)

        except Exception:
            self.handleError(record)

    def handleError(self, record: logging.LogRecord):
        """Enhanced error handling with structured error logging."""
        try:
            self.logfile.log_exception(
                Exception("Failed to process log record"), tag="LOGGING_ADAPTER_ERROR"
            )
        except Exception:
            # Fallback to base handler error handling
            super().handleError(record)
