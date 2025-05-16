import unittest
from datetime import datetime, timedelta
from time import sleep

from loggingutil.filters import (
    LevelFilter,
    RegexFilter,
    RateLimitFilter,
    DuplicateFilter,
    ContextFilter,
    SamplingFilter,
    CompositeFilter,
)


class TestLevelFilter(unittest.TestCase):
    def setUp(self):
        self.filter = LevelFilter("INFO")

    def test_level_filtering(self):
        """Test level-based filtering"""
        # Test levels above INFO
        self.assertTrue(self.filter.filter({"level": "ERROR"}))
        self.assertTrue(self.filter.filter({"level": "WARN"}))

        # Test levels below INFO
        self.assertFalse(self.filter.filter({"level": "DEBUG"}))
        self.assertFalse(self.filter.filter({"level": "TRACE"}))

    def test_invalid_level(self):
        """Test handling of invalid levels"""
        self.assertFalse(self.filter.filter({"level": "INVALID"}))
        self.assertFalse(self.filter.filter({}))


class TestRegexFilter(unittest.TestCase):
    def setUp(self):
        self.patterns = {
            "message": r"error|warning",
            "user_id": r"\d{3}",
        }
        self.filter = RegexFilter(self.patterns)

    def test_regex_matching(self):
        """Test regex pattern matching"""
        # Test matching patterns
        self.assertTrue(
            self.filter.filter(
                {
                    "message": "This is an error message",
                    "user_id": "123",
                }
            )
        )

        # Test non-matching patterns
        self.assertFalse(
            self.filter.filter(
                {
                    "message": "This is a success message",
                    "user_id": "abc",
                }
            )
        )

    def test_match_all_mode(self):
        """Test match_all mode"""
        filter_all = RegexFilter(self.patterns, match_all=True)

        # Should match both patterns
        self.assertTrue(
            filter_all.filter(
                {
                    "message": "This is an error message",
                    "user_id": "123",
                }
            )
        )

        # Should not match (only matches one pattern)
        self.assertFalse(
            filter_all.filter(
                {
                    "message": "This is an error message",
                    "user_id": "abc",
                }
            )
        )


class TestRateLimitFilter(unittest.TestCase):
    def setUp(self):
        self.filter = RateLimitFilter(
            max_count=2,
            time_window=1,  # 1 second
            group_by="type",
        )

    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        log_entry = {"type": "error", "message": "test"}

        # First two logs should pass
        self.assertTrue(self.filter.filter(log_entry))
        self.assertTrue(self.filter.filter(log_entry))

        # Third log should be blocked
        self.assertFalse(self.filter.filter(log_entry))

    def test_window_expiration(self):
        """Test rate limit window expiration"""
        log_entry = {"type": "error", "message": "test"}

        # Fill up the limit
        self.assertTrue(self.filter.filter(log_entry))
        self.assertTrue(self.filter.filter(log_entry))

        # Wait for window to expire
        sleep(1.1)

        # Should allow new logs
        self.assertTrue(self.filter.filter(log_entry))


class TestDuplicateFilter(unittest.TestCase):
    def setUp(self):
        self.filter = DuplicateFilter(
            time_window=1,  # 1 second
            fields=["error_type", "user_id"],
        )

    def test_duplicate_detection(self):
        """Test duplicate log detection"""
        log_entry = {
            "error_type": "ValueError",
            "user_id": "123",
            "message": "test",
        }

        # First occurrence should pass
        self.assertTrue(self.filter.filter(log_entry))

        # Duplicate should be blocked
        self.assertFalse(self.filter.filter(log_entry))

    def test_different_fields(self):
        """Test logs with different field values"""
        # First log
        self.assertTrue(
            self.filter.filter(
                {
                    "error_type": "ValueError",
                    "user_id": "123",
                }
            )
        )

        # Different error type should pass
        self.assertTrue(
            self.filter.filter(
                {
                    "error_type": "TypeError",
                    "user_id": "123",
                }
            )
        )

        # Different user should pass
        self.assertTrue(
            self.filter.filter(
                {
                    "error_type": "ValueError",
                    "user_id": "456",
                }
            )
        )


class TestContextFilter(unittest.TestCase):
    def setUp(self):
        self.rules = [
            {"field": "env", "op": "eq", "value": "prod"},
            {"field": "user_id", "op": "startswith", "value": "admin"},
        ]
        self.filter = ContextFilter(self.rules)

    def test_context_matching(self):
        """Test context-based filtering"""
        # Should match all rules
        self.assertTrue(
            self.filter.filter(
                {
                    "context": {
                        "env": "prod",
                        "user_id": "admin123",
                    }
                }
            )
        )

        # Should not match (wrong environment)
        self.assertFalse(
            self.filter.filter(
                {
                    "context": {
                        "env": "dev",
                        "user_id": "admin123",
                    }
                }
            )
        )

    def test_missing_context(self):
        """Test handling of missing context"""
        self.assertFalse(self.filter.filter({}))
        self.assertFalse(self.filter.filter({"context": {}}))


class TestSamplingFilter(unittest.TestCase):
    def setUp(self):
        self.rules = [
            {
                "field": "level",
                "value": "DEBUG",
                "sample_rate": 0.5,
                "priority": 1,
            },
            {
                "field": "level",
                "value": "INFO",
                "sample_rate": 0.8,
                "priority": 2,
            },
        ]
        self.filter = SamplingFilter(self.rules)

    def test_sampling_rates(self):
        """Test sampling rate application"""
        debug_entry = {"level": "DEBUG"}
        info_entry = {"level": "INFO"}
        error_entry = {"level": "ERROR"}

        # Test multiple logs to verify sampling rates
        debug_passed = sum(1 for _ in range(100) if self.filter.filter(debug_entry))
        info_passed = sum(1 for _ in range(100) if self.filter.filter(info_entry))
        error_passed = sum(1 for _ in range(100) if self.filter.filter(error_entry))

        # Check if sampling rates are roughly correct
        self.assertGreater(debug_passed, 30)  # ~50%
        self.assertLess(debug_passed, 70)

        self.assertGreater(info_passed, 60)  # ~80%
        self.assertLess(info_passed, 90)

        self.assertEqual(error_passed, 100)  # 100% (no rule)
