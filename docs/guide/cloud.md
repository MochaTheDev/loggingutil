# Cloud Integration Guide

LoggingUtil provides robust integration with popular cloud services for log management and analysis.

## AWS CloudWatch

### Basic Setup

```python
from loggingutil import LogFile
from loggingutil.handlers import CloudWatchHandler

logger = LogFile("app.log")
logger.add_handler(CloudWatchHandler(
    log_group="/myapp/prod",
    log_stream="api-server",
    region="us-west-2"
))
```

### Using AWS Credentials

1. Environment Variables:
```bash
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AWS_DEFAULT_REGION="us-west-2"
```

2. Direct Configuration:
```python
handler = CloudWatchHandler(
    log_group="/myapp/prod",
    log_stream="api-server",
    aws_access_key="your_access_key",
    aws_secret_key="your_secret_key",
    region="us-west-2"
)
```

3. IAM Role (recommended for EC2):
```python
# No credentials needed when using IAM roles
handler = CloudWatchHandler(
    log_group="/myapp/prod",
    log_stream="api-server"
)
```

### Best Practices

1. Use descriptive log group names:
```python
log_group = f"/myapp/{environment}/{component}"  # e.g., /myapp/prod/api
```

2. Dynamic log streams:
```python
import socket
from datetime import datetime

log_stream = f"{socket.gethostname()}-{datetime.now().strftime('%Y-%m-%d')}"
```

3. Error handling:
```python
try:
    handler = CloudWatchHandler(...)
    logger.add_handler(handler)
except Exception as e:
    # Fallback to local logging
    logger.log_exception(e)
    logger.add_handler(FileRotatingHandler("logs"))
```

## Elasticsearch

### Basic Setup

```python
from loggingutil import LogFile
from loggingutil.handlers import ElasticsearchHandler

logger = LogFile("app.log")
logger.add_handler(ElasticsearchHandler(
    es_url="http://elasticsearch:9200",
    index_prefix="myapp"
))
```

### Authentication

1. Basic Auth:
```python
handler = ElasticsearchHandler(
    es_url="https://elasticsearch:9200",
    index_prefix="myapp",
    auth=("user", "password")
)
```

2. API Key:
```python
handler = ElasticsearchHandler(
    es_url="https://elasticsearch:9200",
    index_prefix="myapp",
    auth=("api_key_id", "api_key")
)
```

### Index Management

1. Time-based indices:
```python
handler = ElasticsearchHandler(
    es_url="https://elasticsearch:9200",
    index_prefix="myapp-logs"  # Results in indices like myapp-logs-2024.03.21
)
```

2. Custom index naming:
```python
from datetime import datetime

class CustomElasticsearchHandler(ElasticsearchHandler):
    def _get_index_name(self) -> str:
        env = os.getenv("ENVIRONMENT", "dev")
        date = datetime.now().strftime("%Y.%m")
        return f"logs-{env}-{date}"
```

### Best Practices

1. Use index templates:
```json
{
  "index_patterns": ["myapp-*"],
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 1
  },
  "mappings": {
    "properties": {
      "timestamp": { "type": "date" },
      "level": { "type": "keyword" },
      "correlation_id": { "type": "keyword" },
      "message": { "type": "text" }
    }
  }
}
```

2. Configure retention:
```python
# Using ILM (Index Lifecycle Management)
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": {
            "max_size": "50GB",
            "max_age": "30d"
          }
        }
      },
      "delete": {
        "min_age": "90d",
        "actions": {
          "delete": {}
        }
      }
    }
  }
}
```

## Multiple Cloud Services

You can send logs to multiple cloud services simultaneously:

```python
from loggingutil import LogFile
from loggingutil.handlers import (
    CloudWatchHandler,
    ElasticsearchHandler,
    ConsoleHandler
)

logger = LogFile("app.log")

# Local console output
logger.add_handler(ConsoleHandler(color=True))

# CloudWatch for metrics and alerts
logger.add_handler(CloudWatchHandler(
    log_group="/myapp/prod",
    log_stream="api-server"
))

# Elasticsearch for search and analysis
logger.add_handler(ElasticsearchHandler(
    es_url="http://elasticsearch:9200",
    index_prefix="myapp"
))
```

## Error Handling and Fallbacks

Implement robust error handling for cloud services:

```python
class ResilientCloudWatchHandler(CloudWatchHandler):
    def __init__(self, *args, **kwargs):
        self.fallback = FileRotatingHandler("logs/cloudwatch-fallback")
        super().__init__(*args, **kwargs)
    
    async def handle(self, log_entry: dict):
        try:
            await super().handle(log_entry)
        except Exception as e:
            print(f"CloudWatch error: {e}")
            await self.fallback.handle(log_entry)
```

## Monitoring Cloud Costs

1. Use sampling to reduce volume:
```python
logger = LogFile(
    sampling_rate=0.1  # Only send 10% of logs
)
```

2. Implement log levels effectively:
```python
# Development
logger.setLevel(LogLevel.DEBUG)

# Production
logger.setLevel(LogLevel.INFO)
```

3. Use batching for efficiency:
```python
handler = CloudWatchHandler(
    log_group="/myapp/prod",
    log_stream="api-server",
    batch_size=100  # Send logs in batches
)
``` 