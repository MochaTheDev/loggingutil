import os
import yaml
import json
from pathlib import Path
from typing import Any, Dict, Optional
from enum import IntEnum

class LogLevel(IntEnum):
    """Enum for log levels with proper ordering."""
    TRACE = 10
    DEBUG = 20
    INFO = 30
    NOTICE = 35
    WARN = 40
    ERROR = 50
    FATAL = 60

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented

    def __str__(self):
        return self.name

class LogConfig:
    """Configuration manager for LoggingUtil.

    Supports loading config from:
    - YAML files
    - JSON files
    - Environment variables
    - Python dict

    Environment variables override file settings.
    """

    ENV_PREFIX = "LOGGINGUTIL_"

    REQUIRED_FIELDS = ["filename", "mode"]
    VALID_MODES = ["json", "text"]
    VALID_LEVELS = ["TRACE", "DEBUG", "INFO", "NOTICE", "WARN", "ERROR", "FATAL"]
    VALID_ROTATE_TIMES = [None, "hourly", "daily", "weekly", "monthly"]

    def __init__(self):
        self.config: Dict[str, Any] = {
            "filename": "logs.log",
            "mode": "json",
            "level": "INFO",
            "rotate_time": None,
            "max_size_mb": 5,
            "keep_days": 7,
            "compress": False,
            "sampling_rate": 1.0,
            "batch_size": 100,
            "sanitize_keys": ["password", "token", "secret", "key"],
            "schema_validation": False,
            "use_utc": False,
            "verbose": True,
            "handlers": [],
            "filters": [],
        }

    def validate(self):
        """Validate configuration."""
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in self.config:
                raise ValueError(f"Missing required field: {field}")

        # Validate mode
        if self.config["mode"] not in self.VALID_MODES:
            raise ValueError(f"Invalid mode: {self.config['mode']}. Must be one of {self.VALID_MODES}")

        # Validate level
        if self.config["level"] not in self.VALID_LEVELS:
            raise ValueError(f"Invalid level: {self.config['level']}. Must be one of {self.VALID_LEVELS}")

        # Validate rotate_time
        if self.config["rotate_time"] not in self.VALID_ROTATE_TIMES:
            raise ValueError(f"Invalid rotate_time: {self.config['rotate_time']}. Must be one of {self.VALID_ROTATE_TIMES}")

        # Validate numeric fields
        if not isinstance(self.config["max_size_mb"], (int, float)) or self.config["max_size_mb"] <= 0:
            raise ValueError("max_size_mb must be a positive number")

        if not isinstance(self.config["keep_days"], int) or self.config["keep_days"] <= 0:
            raise ValueError("keep_days must be a positive integer")

        if not isinstance(self.config["sampling_rate"], float) or not 0 <= self.config["sampling_rate"] <= 1:
            raise ValueError("sampling_rate must be a float between 0 and 1")

        if not isinstance(self.config["batch_size"], int) or self.config["batch_size"] <= 0:
            raise ValueError("batch_size must be a positive integer")

        # Validate boolean fields
        for field in ["compress", "schema_validation", "use_utc", "verbose"]:
            if not isinstance(self.config[field], bool):
                raise ValueError(f"{field} must be a boolean")

        # Validate lists
        if not isinstance(self.config["sanitize_keys"], list):
            raise ValueError("sanitize_keys must be a list")

        if not isinstance(self.config["handlers"], list):
            raise ValueError("handlers must be a list")

        if not isinstance(self.config["filters"], list):
            raise ValueError("filters must be a list")

    @classmethod
    def from_yaml(cls, path: str) -> "LogConfig":
        """Load config from YAML file."""
        config = cls()
        with open(path) as f:
            yaml_config = yaml.safe_load(f)
            if yaml_config is None:
                raise ValueError("Empty YAML file")
            if not isinstance(yaml_config, dict):
                raise ValueError("Invalid YAML: must be a dictionary")
            # Check for required fields
            for field in cls.REQUIRED_FIELDS:
                if field not in yaml_config:
                    raise ValueError(f"Missing required field: {field}")
            config.update(yaml_config)
            config.validate()
        return config

    @classmethod
    def from_json(cls, path: str) -> "LogConfig":
        """Load config from JSON file."""
        config = cls()
        with open(path) as f:
            json_config = json.load(f)
            if not isinstance(json_config, dict):
                raise ValueError("Invalid JSON: must be a dictionary")
            # Check for required fields
            for field in cls.REQUIRED_FIELDS:
                if field not in json_config:
                    raise ValueError(f"Missing required field: {field}")
            config.update(json_config)
            config.validate()
        return config

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "LogConfig":
        """Load config from Python dict."""
        config = cls()
        config.update(config_dict)
        config.validate()
        return config

    def update(self, config_dict: Dict[str, Any]):
        """Update config with new values."""
        if not isinstance(config_dict, dict):
            raise ValueError("Config update must be a dictionary")
        self.config.update(config_dict)
        self._load_env_vars()  # Environment variables take precedence

    def _load_env_vars(self):
        """Load configuration from environment variables."""
        for key in self.config.keys():
            env_key = f"{self.ENV_PREFIX}{key.upper()}"
            if env_key in os.environ:
                value = os.environ[env_key]
                # Convert string value to appropriate type
                if isinstance(self.config[key], bool):
                    self.config[key] = value.lower() in ("true", "1", "yes")
                elif isinstance(self.config[key], int):
                    self.config[key] = int(value)
                elif isinstance(self.config[key], float):
                    self.config[key] = float(value)
                elif isinstance(self.config[key], list):
                    self.config[key] = json.loads(value)
                else:
                    self.config[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value."""
        return self.config.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.config[key]

    def __str__(self) -> str:
        return f"LogConfig({self.config})"
