# LoggingUtil Documentation

Welcome to LoggingUtil, a powerful Python logging utility that surpasses the standard library logging module.

## Features

- **Advanced Handlers**: Console, SQLite, Webhook, Email, File Rotation, CloudWatch, Elasticsearch
- **Context Management**: Add context to logs with correlation IDs and custom fields
- **Structured Logging**: Support for JSON and structured log formats
- **Cloud Integration**: Native support for AWS CloudWatch and Elasticsearch
- **Performance**: Batching, sampling, and async logging support
- **Security**: Automatic sensitive data redaction and secure credential handling
- **Flexibility**: Easy to extend with custom handlers and formatters
- **Standard Library Compatible**: Drop-in replacement for Python's logging module

## Quick Start

### Installation

```bash
pip install loggingutil
```

### Basic Usage

```python
from loggingutil import LogFile, LogLevel

# Create a logger
logger = LogFile("app.log")

# Log messages
logger.log("Hello world", level=LogLevel.INFO)

# Add context
with logger.context(user_id="123"):
    logger.log("User action")

# Track transactions
with logger.correlation("txn-456"):
    logger.log("Processing payment")
```

### Multiple Outputs

```python
from loggingutil.handlers import ConsoleHandler, ElasticsearchHandler

# Add colored console output
logger.add_handler(ConsoleHandler(color=True))

# Add Elasticsearch integration
logger.add_handler(ElasticsearchHandler(
    "http://elasticsearch:9200",
    index_prefix="myapp"
))
```

## Documentation Structure

- **User Guide**: Step-by-step guides and tutorials
- **API Reference**: Detailed API documentation
- **Cloud Integration**: AWS and Elasticsearch integration guides
- **Best Practices**: Recommendations for production use

## Contributing

We welcome contributions! Please check our [GitHub repository](https://github.com/mochathehuman/loggingutil) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/mochathehuman/loggingutil/blob/main/LICENSE) file for details. 