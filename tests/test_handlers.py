import unittest
import os
import json
import sqlite3
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from yarl import URL

import pytest
import aiohttp
from aioresponses import aioresponses

from loggingutil.handlers import (
    ConsoleHandler,
    SQLiteHandler,
    WebhookHandler,
    EmailHandler,
    FileRotatingHandler,
    CloudWatchHandler,
    ElasticsearchHandler,
)


class TestConsoleHandler:
    @pytest.fixture
    def handler(self):
        return ConsoleHandler(color=True)

    @pytest.fixture
    def log_entry(self):
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": "INFO",
            "data": "Test message",
            "correlation_id": "test-123",
            "tag": "test",
        }

    @pytest.mark.asyncio
    async def test_console_output(self, handler, log_entry, capsys):
        """Test console output with colors"""
        await handler.handle(log_entry)
        captured = capsys.readouterr()
        assert log_entry["data"] in captured.out
        assert log_entry["level"] in captured.out

    @pytest.mark.asyncio
    async def test_console_no_color(self, log_entry, capsys):
        """Test console output without colors"""
        handler = ConsoleHandler(color=False)
        await handler.handle(log_entry)
        captured = capsys.readouterr()
        assert "\033[" not in captured.out


class TestSQLiteHandler:
    @pytest.fixture
    def db_file(self):
        return "test.db"

    @pytest.fixture
    def handler(self, db_file):
        handler = SQLiteHandler(db_file)
        yield handler
        if os.path.exists(db_file):
            os.remove(db_file)

    @pytest.fixture
    def log_entry(self):
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": "INFO",
            "data": "Test message",
            "correlation_id": "test-123",
            "tag": "test",
        }

    @pytest.mark.asyncio
    async def test_sqlite_logging(self, handler, log_entry, db_file):
        """Test SQLite logging and retrieval"""
        await handler.handle(log_entry)

        conn = sqlite3.connect(db_file)
        cursor = conn.execute("SELECT * FROM logs")
        row = cursor.fetchone()
        conn.close()

        assert row[1] == log_entry["level"]
        assert row[2] == log_entry["tag"]
        assert row[3] == log_entry["correlation_id"]


class TestWebhookHandler:
    @pytest.mark.asyncio
    async def test_webhook_handler(self):
        """Test webhook handler with mocked HTTP response"""
        webhook_url = "http://example.com/logs"
        with aioresponses() as m:
            handler = WebhookHandler(webhook_url, batch_size=1)
            m.post(webhook_url, status=200)

            log_entry = {
                "level": "INFO",
                "data": "Test message",
            }
            
            # Handle the log entry
            await handler.handle(log_entry)
            
            # Verify the request was made
            requests = m.requests.get(("POST", URL(webhook_url)))
            assert requests is not None
            assert len(requests) == 1
            assert requests[0].kwargs["json"]["logs"][0] == log_entry


class TestEmailHandler:
    @pytest.mark.asyncio
    @patch("smtplib.SMTP")
    async def test_email_handler(self, mock_smtp):
        """Test email handler with mocked SMTP"""
        handler = EmailHandler(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="test",
            password="test",
            from_addr="from@example.com",
            to_addrs=["to@example.com"],
            min_level="ERROR",
        )

        log_entry = {
            "level": "ERROR",
            "data": "Test error message",
            "tag": "test",
        }
        await handler.handle(log_entry)

        # Verify SMTP interactions
        mock_smtp.assert_called_once_with("smtp.example.com", 587)
        mock_smtp_instance = mock_smtp.return_value.__enter__.return_value
        mock_smtp_instance.starttls.assert_called_once()
        mock_smtp_instance.login.assert_called_once_with("test", "test")
        mock_smtp_instance.send_message.assert_called_once()


class TestFileRotatingHandler:
    @pytest.fixture
    def base_dir(self):
        return "test_logs"

    @pytest.fixture
    def handler(self, base_dir):
        handler = FileRotatingHandler(
            base_dir=base_dir,
            rotate_by="date",
            max_files=2,
        )
        yield handler
        import shutil
        if os.path.exists(base_dir):
            shutil.rmtree(base_dir)

    @pytest.mark.asyncio
    async def test_file_rotation(self, handler, base_dir):
        """Test file rotation by date"""
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": "INFO",
            "data": "Test message",
        }
        
        # Write multiple logs
        for _ in range(3):
            await handler.handle(log_entry)

        # Check directory exists
        assert os.path.exists(base_dir)
        
        # Check files were created
        files = os.listdir(base_dir)
        assert len(files) > 0


class TestCloudWatchHandler:
    @pytest.mark.asyncio
    @patch("boto3.client")
    async def test_cloudwatch_handler(self, mock_boto3_client):
        """Test CloudWatch handler with mocked boto3"""
        handler = CloudWatchHandler(
            log_group="test-group",
            log_stream="test-stream",
            aws_access_key="test",
            aws_secret_key="test",
            region="us-west-2",
        )

        log_entry = {
            "level": "INFO",
            "data": "Test message",
        }
        await handler.handle(log_entry)

        # Verify AWS interactions
        mock_client = mock_boto3_client.return_value
        mock_client.put_log_events.assert_called_once()
        args = mock_client.put_log_events.call_args[1]
        assert args["logGroupName"] == "test-group"
        assert args["logStreamName"] == "test-stream"


class TestElasticsearchHandler:
    @pytest.mark.asyncio
    async def test_elasticsearch_handler(self):
        """Test Elasticsearch handler with mocked HTTP response"""
        with aioresponses() as m:
            es_url = "http://elasticsearch:9200"
            handler = ElasticsearchHandler(es_url, index_prefix="test-logs")
            
            # Mock the index API endpoint
            m.post(f"{es_url}/test-logs-*/_doc", status=201)

            log_entry = {
                "level": "INFO",
                "data": "Test message",
                "timestamp": datetime.now().isoformat(),
            }
            await handler.handle(log_entry)

            # Verify the request was made
            requests = m.requests.values()
            assert len(requests) == 1
            request = list(requests)[0][0]
            assert request.kwargs["json"] == log_entry 