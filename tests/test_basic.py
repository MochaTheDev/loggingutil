import unittest
import os
import json
from datetime import datetime

from loggingutil import LogFile, LogLevel


class TestLoggingUtil(unittest.TestCase):
    def setUp(self):
        self.test_file = "test.log"
        self.logger = LogFile(self.test_file)
        with open(self.test_file, "r") as f:
            f.readline()

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_basic_logging(self):
        """Test basic logging functionality"""
        test_message = "Test log message"
        self.logger.log(test_message)

        with open(self.test_file, "r") as f:
            f.readline()
            log_line = f.readline()
            log_data = json.loads(log_line)

        self.assertEqual(log_data["data"], test_message)
        self.assertEqual(log_data["level"], "INFO")

    def test_log_levels(self):
        """Test different log levels"""
        levels = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARN, LogLevel.ERROR]
        messages = {level: f"Test {level.name}" for level in levels}

        for level, msg in messages.items():
            self.logger.log(msg, level=level)

        with open(self.test_file, "r") as f:
            f.readline()
            logs = [json.loads(line) for line in f]

        for log, (level, msg) in zip(logs, messages.items()):
            self.assertEqual(log["level"], level.name)
            self.assertEqual(log["data"], msg)

    def test_context_manager(self):
        """Test context manager functionality"""
        context_data = {"user_id": "123", "request_id": "abc"}

        with self.logger.context(**context_data):
            self.logger.log("Test with context")

        with open(self.test_file, "r") as f:
            f.readline()
            log_data = json.loads(f.readline())

        self.assertEqual(log_data["context"], context_data)

    def test_structured_logging(self):
        """Test structured logging"""
        structured_data = {
            "event": "user_login",
            "user_id": "123",
            "timestamp": datetime.now().isoformat(),
        }

        self.logger.structured(**structured_data)

        with open(self.test_file, "r") as f:
            f.readline()
            log_data = json.loads(f.readline())

        self.assertEqual(log_data["data"], structured_data)

    def test_correlation_id(self):
        """Test correlation ID functionality"""
        correlation_id = "test-correlation-123"

        with self.logger.correlation(correlation_id):
            self.logger.log("Test with correlation")

        with open(self.test_file, "r") as f:
            f.readline()
            log_data = json.loads(f.readline())

        self.assertEqual(log_data["correlation_id"], correlation_id)


if __name__ == "__main__":
    unittest.main()
