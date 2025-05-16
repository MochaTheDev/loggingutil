# Handlers API Reference

## Base Handler

::: loggingutil.handlers.BaseHandler
    handler: python
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

## Console Handler

::: loggingutil.handlers.ConsoleHandler
    handler: python
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

### Example

```python
from loggingutil import LogFile
from loggingutil.handlers import ConsoleHandler

logger = LogFile("app.log")

# Add colored console output
logger.add_handler(ConsoleHandler(
    color=True,
    format="detailed"  # or "simple"
))
```

## SQLite Handler

::: loggingutil.handlers.SQLiteHandler
    handler: python
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

### Example

```python
from loggingutil.handlers import SQLiteHandler

logger.add_handler(SQLiteHandler("logs.db"))

# Query logs later
import sqlite3
conn = sqlite3.connect("logs.db")
cursor = conn.execute("SELECT * FROM logs WHERE level = 'ERROR'")
```

## Webhook Handler

::: loggingutil.handlers.WebhookHandler
    handler: python
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

### Example

```python
from loggingutil.handlers import WebhookHandler

logger.add_handler(WebhookHandler(
    webhook_url="https://api.example.com/logs",
    batch_size=10  # Send logs in batches of 10
))
```

## Email Handler

::: loggingutil.handlers.EmailHandler
    handler: python
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

### Example

```python
from loggingutil.handlers import EmailHandler

logger.add_handler(EmailHandler(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    username="alerts@example.com",
    password="app_password",
    from_addr="alerts@example.com",
    to_addrs=["admin@example.com"],
    min_level="ERROR"  # Only send ERROR and above
))
```

## File Rotating Handler

::: loggingutil.handlers.FileRotatingHandler
    handler: python
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

### Example

```python
from loggingutil.handlers import FileRotatingHandler

logger.add_handler(FileRotatingHandler(
    base_dir="logs",
    rotate_by="date",  # or "tag"
    max_files=30
))
```

## CloudWatch Handler

::: loggingutil.handlers.CloudWatchHandler
    handler: python
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

### Example

```python
from loggingutil.handlers import CloudWatchHandler

logger.add_handler(CloudWatchHandler(
    log_group="/myapp/prod",
    log_stream="api-server",
    aws_access_key="YOUR_ACCESS_KEY",
    aws_secret_key="YOUR_SECRET_KEY",
    region="us-west-2"
))
```

## Elasticsearch Handler

::: loggingutil.handlers.ElasticsearchHandler
    handler: python
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

### Example

```python
from loggingutil.handlers import ElasticsearchHandler

logger.add_handler(ElasticsearchHandler(
    es_url="http://elasticsearch:9200",
    index_prefix="myapp-logs",
    auth=("user", "pass")  # Optional authentication
))
``` 