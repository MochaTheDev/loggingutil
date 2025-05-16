import os
import json
import aiohttp
import asyncio
import smtplib
import sqlite3
from email.message import EmailMessage
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

class BaseHandler:
    """Base class for all handlers with common functionality."""
    async def handle(self, log_entry: dict) -> None:
        raise NotImplementedError

class SQLiteHandler(BaseHandler):
    """Handler that stores logs in SQLite database."""
    def __init__(self, db_path: str = "logs.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS logs
                    (timestamp TEXT, level TEXT, tag TEXT, 
                     correlation_id TEXT, data TEXT)''')
        conn.commit()
        conn.close()

    async def handle(self, log_entry: dict):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "INSERT INTO logs VALUES (?, ?, ?, ?, ?)",
            (log_entry["timestamp"], log_entry["level"],
             log_entry.get("tag"), log_entry.get("correlation_id"),
             json.dumps(log_entry["data"]))
        )
        conn.commit()
        conn.close()

class WebhookHandler(BaseHandler):
    """Handler that sends logs to a webhook URL."""
    def __init__(self, webhook_url: str, batch_size: int = 10):
        self.webhook_url = webhook_url
        self.batch_size = batch_size
        self.batch: List[dict] = []
        
    async def handle(self, log_entry: dict):
        self.batch.append(log_entry)
        
        if len(self.batch) >= self.batch_size:
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(
                        self.webhook_url,
                        json={"logs": self.batch}
                    ) as response:
                        if response.status >= 400:
                            print(f"Webhook error: {response.status}")
                finally:
                    self.batch = []

class EmailHandler(BaseHandler):
    """Handler that sends critical logs via email."""
    def __init__(self, 
                 smtp_host: str,
                 smtp_port: int,
                 username: str,
                 password: str,
                 from_addr: str,
                 to_addrs: List[str],
                 min_level: str = "ERROR"):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_addr = from_addr
        self.to_addrs = to_addrs
        self.min_level = min_level

    async def handle(self, log_entry: dict):
        if log_entry["level"] < self.min_level:
            return

        msg = EmailMessage()
        msg.set_content(json.dumps(log_entry, indent=2))
        msg["Subject"] = f"Log Alert: {log_entry['level']} - {log_entry.get('tag', 'No Tag')}"
        msg["From"] = self.from_addr
        msg["To"] = ", ".join(self.to_addrs)

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)

class FileRotatingHandler(BaseHandler):
    """Handler that writes logs to rotating files by date or tag."""
    def __init__(self, 
                 base_dir: str = "logs",
                 rotate_by: str = "date",  # or "tag"
                 max_files: int = 30):
        self.base_dir = Path(base_dir)
        self.rotate_by = rotate_by
        self.max_files = max_files
        self.base_dir.mkdir(exist_ok=True)

    def _get_filename(self, log_entry: dict) -> Path:
        if self.rotate_by == "date":
            date_str = datetime.now().strftime("%Y-%m-%d")
            return self.base_dir / f"{date_str}.log"
        else:  # rotate by tag
            tag = log_entry.get("tag", "notag")
            return self.base_dir / f"{tag}.log"

    async def handle(self, log_entry: dict):
        filepath = self._get_filename(log_entry)
        with open(filepath, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        # Cleanup old files if needed
        self._cleanup_old_files()

    def _cleanup_old_files(self):
        files = sorted(self.base_dir.glob("*.log"), 
                      key=lambda x: x.stat().st_mtime)
        if len(files) > self.max_files:
            for f in files[:-self.max_files]:
                f.unlink()

class CloudWatchHandler(BaseHandler):
    """Handler that sends logs to AWS CloudWatch."""
    def __init__(self, 
                 log_group: str,
                 log_stream: str,
                 aws_access_key: Optional[str] = None,
                 aws_secret_key: Optional[str] = None,
                 region: Optional[str] = None):
        try:
            import boto3
            self.client = boto3.client(
                'logs',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=region
            )
        except ImportError:
            raise ImportError("boto3 required for CloudWatch handler")
            
        self.log_group = log_group
        self.log_stream = log_stream
        self._ensure_log_group()

    def _ensure_log_group(self):
        try:
            self.client.create_log_group(logGroupName=self.log_group)
        except self.client.exceptions.ResourceAlreadyExistsException:
            pass
        
        try:
            self.client.create_log_stream(
                logGroupName=self.log_group,
                logStreamName=self.log_stream
            )
        except self.client.exceptions.ResourceAlreadyExistsException:
            pass

    async def handle(self, log_entry: dict):
        event = {
            'timestamp': int(datetime.now().timestamp() * 1000),
            'message': json.dumps(log_entry)
        }
        
        try:
            self.client.put_log_events(
                logGroupName=self.log_group,
                logStreamName=self.log_stream,
                logEvents=[event]
            )
        except Exception as e:
            print(f"CloudWatch error: {e}")

class ElasticsearchHandler(BaseHandler):
    """Handler that sends logs to Elasticsearch."""
    def __init__(self, 
                 es_url: str,
                 index_prefix: str = "logs",
                 auth: Optional[tuple] = None):
        self.es_url = es_url
        self.index_prefix = index_prefix
        self.auth = auth

    def _get_index_name(self) -> str:
        return f"{self.index_prefix}-{datetime.now().strftime('%Y.%m.%d')}"

    async def handle(self, log_entry: dict):
        index = self._get_index_name()
        url = f"{self.es_url}/{index}/_doc"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=log_entry, auth=self.auth) as resp:
                    if resp.status >= 400:
                        print(f"Elasticsearch error: {resp.status}")
            except Exception as e:
                print(f"Elasticsearch error: {e}")

class ConsoleHandler(BaseHandler):
    """Handler that prints logs to console with colors and formatting."""
    COLORS = {
        "TRACE": "\033[37m",  # white
        "DEBUG": "\033[36m",  # cyan
        "INFO": "\033[32m",   # green
        "NOTICE": "\033[34m", # blue
        "WARN": "\033[33m",   # yellow
        "ERROR": "\033[31m",  # red
        "FATAL": "\033[35m",  # magenta
        "RESET": "\033[0m"
    }

    def __init__(self, color: bool = True, format: str = "detailed"):
        self.color = color and os.name != 'nt'  # Disable colors on Windows
        self.format = format

    async def handle(self, log_entry: dict):
        level = log_entry["level"]
        color_start = self.COLORS[level] if self.color else ""
        color_reset = self.COLORS["RESET"] if self.color else ""
        
        if self.format == "detailed":
            print(f"{color_start}[{log_entry['timestamp']}] "
                  f"[{level}] "
                  f"[{log_entry.get('correlation_id', 'no-correlation')}] "
                  f"{log_entry.get('tag', '')} "
                  f"{json.dumps(log_entry['data'])}"
                  f"{color_reset}")
        else:
            print(f"{color_start}{json.dumps(log_entry)}{color_reset}") 