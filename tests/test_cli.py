import os
import json
import sqlite3
from pathlib import Path
from unittest.mock import patch
from datetime import datetime, timedelta

import pytest
from click.testing import CliRunner

from loggingutil.cli import main


@pytest.fixture
def sample_log_file(tmp_path):
    """Create a sample log file for testing"""
    log_file = tmp_path / "test.log"

    logs = [
        {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": "INFO",
            "tag": "test",
            "data": "Test message 1",
        },
        {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": "ERROR",
            "tag": "error",
            "data": "Error message",
        },
        {
            "timestamp": (datetime.now() - timedelta(days=2)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "level": "WARN",
            "tag": "test",
            "data": "Old warning",
        },
    ]

    with open(log_file, "w") as f:
        for log in logs:
            f.write(json.dumps(log) + "\n")

    return log_file


def test_analyze_basic(sample_log_file):
    """Test basic log analysis"""
    runner = CliRunner()
    result = runner.invoke(main, ["analyze", str(sample_log_file)])

    assert result.exit_code == 0
    assert "Total Logs: 3" in result.output
    assert "INFO: 1" in result.output
    assert "ERROR: 1" in result.output
    assert "WARN: 1" in result.output


def test_analyze_with_level(sample_log_file):
    """Test log analysis with level filter"""
    runner = CliRunner()
    result = runner.invoke(main, ["analyze", str(sample_log_file), "--level", "ERROR"])

    assert result.exit_code == 0
    assert "Total Logs: 1" in result.output
    assert "ERROR: 1" in result.output
    assert "INFO: " not in result.output


def test_analyze_with_tag(sample_log_file):
    """Test log analysis with tag filter"""
    runner = CliRunner()
    result = runner.invoke(main, ["analyze", str(sample_log_file), "--tag", "test"])

    assert result.exit_code == 0
    assert "Total Logs: 2" in result.output
    assert "test: 2" in result.output


def test_analyze_with_time_filter(sample_log_file):
    """Test log analysis with time filter"""
    runner = CliRunner()
    result = runner.invoke(main, ["analyze", str(sample_log_file), "--since", "1d"])

    assert result.exit_code == 0
    assert "Total Logs: 2" in result.output  # Should exclude old warning


def test_analyze_json_output(sample_log_file):
    """Test JSON output format"""
    runner = CliRunner()
    result = runner.invoke(main, ["analyze", str(sample_log_file), "--format", "json"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["total_logs"] == 3
    assert "levels" in data
    assert "tags" in data
    assert "time_distribution" in data


def test_convert_to_sqlite(sample_log_file, tmp_path):
    """Test converting log file to SQLite database"""
    db_file = tmp_path / "test.db"
    runner = CliRunner()
    result = runner.invoke(
        main, ["convert", str(sample_log_file), "--output", str(db_file)]
    )

    assert result.exit_code == 0
    assert db_file.exists()

    # Verify database contents
    conn = sqlite3.connect(db_file)
    cursor = conn.execute("SELECT COUNT(*) FROM logs")
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 3


def test_validate_yaml_config(tmp_path):
    """Test YAML config validation"""
    config_file = tmp_path / "config.yaml"
    config_content = """
filename: app.log
mode: json
level: INFO
rotate_time: daily
max_size_mb: 100
keep_days: 30
compress: true
    """

    config_file.write_text(config_content)

    runner = CliRunner()
    result = runner.invoke(main, ["validate", str(config_file)])

    assert result.exit_code == 0
    assert "Configuration is valid!" in result.output


def test_validate_invalid_config(tmp_path):
    """Test validation of invalid config"""
    config_file = tmp_path / "invalid.yaml"
    config_content = """
invalid: true
bad: config
    """

    config_file.write_text(config_content)

    runner = CliRunner()
    result = runner.invoke(main, ["validate", str(config_file)])

    assert result.exit_code == 1  # Should fail
    assert "Configuration is valid!" not in result.output


def test_analyze_invalid_log_file():
    """Test analysis of non-existent log file"""
    runner = CliRunner()
    result = runner.invoke(main, ["analyze", "nonexistent.log"])

    assert result.exit_code == 2  # Click's error code for file not found
    assert "Error" in result.output


def test_analyze_invalid_time_format(sample_log_file):
    """Test analysis with invalid time format"""
    runner = CliRunner()
    result = runner.invoke(
        main, ["analyze", str(sample_log_file), "--since", "invalid"]
    )

    assert result.exit_code == 1
    assert "Invalid time format" in result.output
