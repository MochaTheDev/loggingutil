# LoggingUtil

[![PyPI version](https://badge.fury.io/py/loggingutil.svg)](https://badge.fury.io/py/loggingutil)
[![Tests](https://github.com/mochathehuman/loggingutil/actions/workflows/tests.yml/badge.svg)](https://github.com/mochathehuman/loggingutil/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/mochathehuman/loggingutil/branch/main/graph/badge.svg)](https://codecov.io/gh/mochathehuman/loggingutil)
[![Python Versions](https://img.shields.io/pypi/pyversions/loggingutil)](https://pypi.org/project/loggingutil)
[![License](https://img.shields.io/github/license/mochathehuman/loggingutil)](https://github.com/mochathehuman/loggingutil/blob/main/LICENSE)
[![Downloads](https://pepy.tech/badge/loggingutil)](https://pepy.tech/project/loggingutil)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue)](https://mochathehuman.github.io/loggingutil)

```bash
pip install loggingutil
```

A powerful Python logging utility that combines simplicity with advanced features. Perfect for both simple scripts and enterprise applications.

## Quick Start

```python
from loggingutil import LogFile

# Simple usage
logger = LogFile("app.log")
logger.log("Hello, World!")

# With context and structured data
with logger.context(user_id="123"):
    logger.structured(
        event="user_login",
        ip="1.2.3.4",
        status="success"
    )
```

## Features

- **Simple Interface** - Easy to use, hard to misuse
- **Smart Rotation** - By size, time, or custom rules
- **Structured Logging** - JSON format with schema validation
- **Multiple Outputs** - Console, File, Database, Cloud
- **Context Management** - Track request flow
- **Smart Filtering** - Rate limiting, sampling, deduplication
- **Async Support** - High-performance logging
- **Data Safety** - Automatic sensitive data redaction
- **Metrics** - Built-in logging statistics
- **Extensible** - Custom handlers and filters

## Installation

```bash
pip install loggingutil

# With all extras (elasticsearch, cloudwatch, etc)
pip install loggingutil[all]
```

## Common Use Cases

### Basic Logging
```python
from loggingutil import LogFile, LogLevel

logger = LogFile("app.log")

# Simple logging
logger.log("System started")

# With level and tag
logger.log("Invalid input", level=LogLevel.ERROR, tag="VALIDATION")

# Structured data
logger.structured(
    event="order_created",
    order_id="123",
    amount=99.99
)
```

### Request Tracking
```python
with logger.context(request_id="req-123", user="john"):
    with logger.correlation("txn-456"):
        logger.log("Processing payment")
        try:
            process_payment()
        except Exception as e:
            logger.log_exception(e)
```

### Multiple Outputs
```python
from loggingutil.handlers import ConsoleHandler, ElasticsearchHandler

logger = LogFile("app.log")

# Colored console output
logger.add_handler(ConsoleHandler(color=True))

# Elasticsearch for search
logger.add_handler(ElasticsearchHandler(
    "http://elasticsearch:9200",
    index_prefix="myapp"
))
```

### Smart Filtering
```python
from loggingutil.filters import RateLimitFilter, DuplicateFilter

# Limit error rates
logger.add_filter(RateLimitFilter(
    max_count=100,  # max 100 logs
    time_window=60,  # per minute
    group_by="error_type"  # per error type
))

# Prevent duplicate errors
logger.add_filter(DuplicateFilter(
    time_window=300,  # 5 minutes
    fields=["error_type", "user_id"]
))
```

### Configuration
```python
# From YAML
from loggingutil import LogConfig
config = LogConfig.from_yaml("logging.yaml")
logger = LogFile(**config)

# From environment
# LOGGINGUTIL_FILENAME=app.log
# LOGGINGUTIL_MODE=json
logger = LogFile()  # auto-loads from env
```

### Cloud Integration
```python
from loggingutil.handlers import CloudWatchHandler

logger.add_handler(CloudWatchHandler(
    log_group="myapp",
    log_stream="prod"
))
```

## Advanced Configuration

```python
logger = LogFile(
    # Basic settings
    filename="app.log",
    mode="json",  # or "text"
    level=LogLevel.INFO,
    
    # Rotation settings
    rotate_time="daily",  # or "hourly", None
    max_size_mb=100,
    keep_days=30,
    compress=True,
    
    # Performance settings
    batch_size=100,
    sampling_rate=0.1,  # sample 10% of logs
    
    # Security settings
    sanitize_keys=["password", "token", "key"],
    
    # Time settings
    use_utc=True,
    timestamp_format="[%Y-%m-%d %H:%M:%S.%f]"
)
```

## Migration from stdlib logging

```python
import logging
from loggingutil.adapter import LoggingUtilHandler

# Create LoggingUtil logger
logutil = LogFile("app.log")

# Create handler
handler = LoggingUtilHandler(logutil)

# Add to existing logger
logger = logging.getLogger("myapp")
logger.addHandler(handler)

# Use standard logging - it will use LoggingUtil
logger.info("Hello world", extra={"user_id": "123"})
```

## Metrics and Monitoring

```python
# Get logging statistics
stats = logger.get_metrics()
print(f"Error rate: {stats['log_counts']['ERROR']}/minute")
print(f"Uptime: {stats['uptime']}")
```

## Custom Formatting

```python
def my_formatter(log_entry: dict) -> str:
    return f"[CUSTOM] {log_entry['data']}\n"

logger = LogFile(custom_formatter=my_formatter)
```

## Security Best Practices

1. Use `sanitize_keys` to automatically redact sensitive data
2. Enable compression for log files
3. Use structured logging for better security analysis
4. Implement rate limiting for error logs
5. Set appropriate file permissions

## License

MIT License - see [LICENSE](LICENSE) for details.