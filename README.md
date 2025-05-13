# loggingutil

![Python](https://img.shields.io/badge/python-3.7%2B-blue)
![License](https://img.shields.io/badge/license-MIT-yellow)
![PyPI](https://img.shields.io/pypi/v/loggingutil)

**Advanced Python Logging Utility**  
Flexible, efficient, and powerful logging with file rotation, JSON/text modes, async support, exception tracking, and HTTP response logging.

---

## 📦 Installation

```bash
pip install loggingutil
```

- Log rotation by file size

- Optional GZip compression

- Text or JSON output modes

- Buffering for performance

- Custom timestamp and formatting

- Auto-deletion of old logs

- Async logging and HTTP response support

- Exception logging with tracebacks

- External stream hooks (e.g., to Discord, console)

- Custom log levels and formatters

```python
from loggingutil import LogFile

log = LogFile(filename="mylog.log", mode="text")

log.log("System initialized.")
log.log("Something went wrong!", level=log.error)
log.flush()
```

## Output Formats
### Text (Default)

```txt
[2025-05-13 12:34:56] [INFO] [INIT] System initialized.
```

### JSON

```json
{
  "timestamp": "2025-05-13 12:34:56",
  "level": 1,
  "tag": "INIT",
  "data": "System initialized."
}
```

*Set with:*
```python
log = LogFile(mode="json")
```

### Options
```python
LogFile(
    filename="log.txt",
    verbose=True,
    max_size_mb=5,
    keep_days=7,
    timestamp_format="[%Y-%m-%d %H:%M:%S]",
    mode="text",  # or "json"
    compress=False,
    use_utc=False,
    include_timestamp=True,
    custom_formatter=None,
    external_stream=None
)
```

## Async Logging

```python
await log.async_log("Async message", tag="ASYNC")
```

### Log HTTP Responses

```python
async with aiohttp.ClientSession() as session:
    async with session.get("https://api.example.com") as resp:
        await log.async_log_http_response(resp)
```

### Log Exceptions

```python
try:
    1 / 0
except Exception as e:
    log.log_exception(e)
```

## Custom formatting

```python
def my_formatter(data, level, tag):
    return f"[CUSTOM] {data}\n"

log = LogFile(custom_formatter=my_formatter)
```