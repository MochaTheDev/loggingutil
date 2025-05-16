import os
import yaml
import json
from typing import Dict, Any, Optional
from pathlib import Path


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

    @classmethod
    def from_yaml(cls, path: str) -> "LogConfig":
        """Load config from YAML file."""
        config = cls()
        with open(path) as f:
            yaml_config = yaml.safe_load(f)
            config.update(yaml_config)
        return config

    @classmethod
    def from_json(cls, path: str) -> "LogConfig":
        """Load config from JSON file."""
        config = cls()
        with open(path) as f:
            json_config = json.load(f)
            config.update(json_config)
        return config

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "LogConfig":
        """Load config from Python dict."""
        config = cls()
        config.update(config_dict)
        return config

    def update(self, config_dict: Dict[str, Any]):
        """Update config with new values."""
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
