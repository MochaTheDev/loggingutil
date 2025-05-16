import logging
import pytest
from unittest.mock import Mock, patch, MagicMock

from loggingutil import LogFile, LogLevel
from loggingutil.adapter import LoggingUtilHandler


class TestLoggingUtilHandler:
    @pytest.fixture
    def logfile(self):
        mock = MagicMock(spec=LogFile)
        # Create a context manager mock that propagates exceptions
        context_mock = MagicMock()
        mock.context.return_value = context_mock
        mock.context.return_value.__enter__ = MagicMock()
        mock.context.return_value.__exit__ = MagicMock(
            return_value=False
        )  # Don't suppress exceptions
        # Set up log and log_exception methods
        mock.log = MagicMock(name="log")
        mock.log_exception = MagicMock(name="log_exception")
        return mock

    @pytest.fixture
    def handler(self, logfile):
        handler = LoggingUtilHandler(logfile)
        handler.setLevel(logging.INFO)
        handler.formatter = (
            logging.Formatter()
        )  # Set formatter to avoid NoneType errors
        return handler

    @pytest.fixture
    def logger(self, handler):
        logger = logging.getLogger("test_logger")
        logger.handlers = []  # Clear any existing handlers
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def test_level_mapping(self, handler):
        """Test mapping of stdlib logging levels to LoggingUtil levels"""
        assert handler.level_map[logging.DEBUG] == LogLevel.DEBUG
        assert handler.level_map[logging.INFO] == LogLevel.INFO
        assert handler.level_map[logging.WARNING] == LogLevel.WARN
        assert handler.level_map[logging.ERROR] == LogLevel.ERROR
        assert handler.level_map[logging.CRITICAL] == LogLevel.FATAL

    def test_basic_logging(self, logger, logfile):
        """Test basic logging functionality"""
        test_message = "Test log message"
        logger.info(test_message)

        logfile.log.assert_called_once()
        call_args = logfile.log.call_args
        assert call_args.args[0]["message"] == test_message
        assert call_args.kwargs["level"] == LogLevel.INFO

    def test_logging_with_extra(self, logger, logfile):
        """Test logging with extra context"""
        extra_data = {"user_id": "123"}
        logger.info("Test message", extra=extra_data)

        logfile.log.assert_called_once()
        call_args = logfile.log.call_args
        assert call_args.args[0]["user_id"] == "123"

    def test_exception_logging(self, logger, logfile):
        """Test exception logging"""
        try:
            raise ValueError("Test error")
        except ValueError:
            logger.exception("An error occurred")

        logfile.log.assert_called_once()
        call_args = logfile.log.call_args
        assert "exception" in call_args.args[0]
        assert call_args.args[0]["exception"]["type"] == "ValueError"
        assert "Test error" in call_args.args[0]["exception"]["message"]

    def test_structured_logging(self, logger, logfile):
        """Test structured logging with multiple fields"""
        extra_data = {"user_id": "123", "ip_address": "127.0.0.1", "action": "login"}
        logger.info("User logged in", extra=extra_data)

        logfile.log.assert_called_once()
        call_args = logfile.log.call_args
        assert call_args.args[0]["user_id"] == "123"
        assert call_args.args[0]["ip_address"] == "127.0.0.1"
        assert call_args.args[0]["action"] == "login"

    def test_error_handling(self, handler, logfile):
        """Test handler error handling"""
        record = logging.LogRecord(
            "test", logging.INFO, "test.py", 1, "Test message", (), None
        )

        # Set up the mock to raise an exception for log
        test_error = Exception("Test error")
        logfile.log.side_effect = test_error
        # Make sure context manager doesn't suppress exceptions
        logfile.context.return_value.__exit__.return_value = False

        # Call emit which should trigger error handling
        handler.emit(record)  # This should not raise since we handle the error

        # Print mock call info for debugging
        print(f"log_exception mock calls: {logfile.log_exception.mock_calls}")
        print(f"log_exception call count: {logfile.log_exception.call_count}")

        # Verify log_exception was called correctly
        assert logfile.log_exception.call_count == 1
        args, kwargs = logfile.log_exception.call_args
        assert isinstance(args[0], Exception)
        assert str(args[0]) == "Failed to process log record"
        assert kwargs["tag"] == "LOGGING_ADAPTER_ERROR"

    def test_context_handling(self, logger, logfile):
        """Test handling of logging context"""
        logger.info("Test message", extra={"request_id": "abc123"})

        # Verify context was used
        logfile.context.assert_called_once()
        assert "request_id" in logfile.context.call_args.kwargs
