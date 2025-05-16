# LogFile API Reference

::: loggingutil.LogFile
    handler: python
    options:
      show_root_heading: true
      show_source: true
      heading_level: 2

## Examples

### Basic Usage

```python
from loggingutil import LogFile, LogLevel

# Create a logger
logger = LogFile("app.log")

# Log messages with different levels
logger.log("Hello world", level=LogLevel.INFO)
logger.log("Debug info", level=LogLevel.DEBUG)
logger.log("Warning!", level=LogLevel.WARN)

# Use context managers
with logger.context(user_id="123"):
    logger.log("User action")

# Use correlation IDs
with logger.correlation("txn-456"):
    logger.log("Transaction processing")

# Log structured data
logger.structured(
    event="user_login",
    user_id="123",
    ip="192.168.1.1"
)

# Log exceptions
try:
    raise ValueError("Something went wrong")
except Exception as e:
    logger.log_exception(e)
```

### Advanced Configuration

```python
logger = LogFile(
    filename="app.log",
    mode="json",
    level=LogLevel.INFO,
    rotate_time="daily",
    max_size_mb=100,
    keep_days=30,
    compress=True,
    batch_size=100,
    sampling_rate=0.1,
    sanitize_keys=["password", "token"],
    use_utc=True
)
```

### Using Multiple Handlers

```python
from loggingutil.handlers import ConsoleHandler, ElasticsearchHandler

logger = LogFile("app.log")

# Add console output with colors
logger.add_handler(ConsoleHandler(color=True))

# Add Elasticsearch integration
logger.add_handler(ElasticsearchHandler(
    "http://elasticsearch:9200",
    index_prefix="myapp"
))
```

### Performance Optimization

```python
# Use batching for better performance
logger = LogFile(
    batch_size=100,  # Buffer 100 logs before writing
    sampling_rate=0.1  # Only log 10% of messages
)

# Flush buffer manually if needed
logger.flush()
```

### Security Features

```python
# Automatically redact sensitive data
logger = LogFile(
    sanitize_keys=[
        "password",
        "token",
        "secret",
        "api_key"
    ]
)

# Log will automatically redact sensitive fields
logger.log({
    "user": "john",
    "password": "secret123"  # Will be replaced with "***REDACTED***"
})
``` 