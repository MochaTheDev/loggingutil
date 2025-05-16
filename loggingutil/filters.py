import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .config import LogLevel  # Import LogLevel enum


class BaseFilter:
    """Base class for all filters."""

    def filter(self, log_entry: dict) -> bool:
        raise NotImplementedError


class LevelFilter(BaseFilter):
    """Filter logs based on level."""

    def __init__(self, min_level: str):
        self.min_level = min_level
        try:
            # Try to convert string to LogLevel enum
            self.min_level_enum = LogLevel[min_level.upper()]
        except (KeyError, AttributeError):
            # If conversion fails, keep the string value
            self.min_level_enum = None

    def filter(self, log_entry: dict) -> bool:
        try:
            log_level = log_entry.get("level", "")
            if self.min_level_enum is not None:
                # If we have enum values, use them for comparison
                log_level_enum = LogLevel[log_level.upper()]
                return log_level_enum >= self.min_level_enum
            # Fall back to string comparison
            return log_level >= self.min_level
        except (KeyError, AttributeError):
            # If level comparison fails, treat as below minimum
            return False


class RegexFilter(BaseFilter):
    """Filter logs based on regex patterns."""

    def __init__(self, patterns: Dict[str, str], match_all: bool = False):
        self.patterns = {
            field: re.compile(pattern) for field, pattern in patterns.items()
        }
        self.match_all = match_all

    def filter(self, log_entry: dict) -> bool:
        matches = []
        for field, pattern in self.patterns.items():
            value = str(log_entry.get(field, ""))
            match = bool(pattern.search(value))
            matches.append(match)

        return all(matches) if self.match_all else any(matches)


class RateLimitFilter(BaseFilter):
    """Filter logs based on rate limits."""

    def __init__(
        self,
        max_count: int,
        time_window: int,  # seconds
        group_by: Optional[str] = None,
    ):
        self.max_count = max_count
        self.time_window = time_window
        self.group_by = group_by
        self.counters: Dict[str, List[datetime]] = {}

    def filter(self, log_entry: dict) -> bool:
        now = datetime.now()
        key = str(log_entry.get(self.group_by)) if self.group_by else "default"

        if key not in self.counters:
            self.counters[key] = []

        # Remove old timestamps
        self.counters[key] = [
            ts
            for ts in self.counters[key]
            if now - ts < timedelta(seconds=self.time_window)
        ]

        if len(self.counters[key]) >= self.max_count:
            return False

        self.counters[key].append(now)
        return True


class DuplicateFilter(BaseFilter):
    """Filter duplicate logs within a time window."""

    def __init__(self, time_window: int, fields: List[str]):  # seconds
        self.time_window = time_window
        self.fields = fields
        self.seen: Dict[str, datetime] = {}

    def _get_key(self, log_entry: dict) -> str:
        values = []
        for field in self.fields:
            value = log_entry.get(field)
            if isinstance(value, dict):
                value = str(sorted(value.items()))
            values.append(str(value))
        return "|".join(values)

    def filter(self, log_entry: dict) -> bool:
        now = datetime.now()
        key = self._get_key(log_entry)

        if key in self.seen:
            if now - self.seen[key] < timedelta(seconds=self.time_window):
                return False

        self.seen[key] = now
        return True


class ContextFilter(BaseFilter):
    """Filter logs based on context values."""

    def __init__(self, rules: List[Dict[str, Any]], match_all: bool = True):
        self.rules = rules
        self.match_all = match_all

    def _matches_rule(self, context: dict, rule: Dict[str, Any]) -> bool:
        field = rule["field"]
        op = rule["op"]
        value = rule["value"]

        if field not in context:
            return False

        actual = context[field]

        if op == "eq":
            return actual == value
        elif op == "ne":
            return actual != value
        elif op == "contains":
            return value in str(actual)
        elif op == "startswith":
            return str(actual).startswith(str(value))
        elif op == "endswith":
            return str(actual).endswith(str(value))
        elif op == "matches":
            return bool(re.search(value, str(actual)))
        elif op == "gt":
            return actual > value
        elif op == "lt":
            return actual < value

        return False

    def filter(self, log_entry: dict) -> bool:
        context = log_entry.get("context", {})
        matches = [self._matches_rule(context, rule) for rule in self.rules]
        return all(matches) if self.match_all else any(matches)


class SamplingFilter(BaseFilter):
    """Filter logs based on sampling rules."""

    def __init__(self, rules: List[Dict[str, Any]]):
        self.rules = sorted(rules, key=lambda x: x["priority"])
        self.counters: Dict[str, Dict[str, int]] = {}

    def _get_rule_key(self, rule: Dict[str, Any]) -> str:
        return f"{rule['field']}:{rule['value']}"

    def filter(self, log_entry: dict) -> bool:
        for rule in self.rules:
            field = rule["field"]
            value = rule["value"]
            rate = rule["sample_rate"]

            if field in log_entry and log_entry[field] == value:
                key = self._get_rule_key(rule)

                if key not in self.counters:
                    self.counters[key] = {"count": 0, "total": 0}

                self.counters[key]["total"] += 1
                if self.counters[key]["count"] / self.counters[key]["total"] < rate:
                    self.counters[key]["count"] += 1
                    return True
                return False

        return True  # No matching rules


class CompositeFilter(BaseFilter):
    """Combine multiple filters with AND/OR logic."""

    def __init__(self, filters: List[BaseFilter], operator: str = "and"):
        self.filters = filters
        self.operator = operator.lower()

    def filter(self, log_entry: dict) -> bool:
        results = [f.filter(log_entry) for f in self.filters]
        return all(results) if self.operator == "and" else any(results)
