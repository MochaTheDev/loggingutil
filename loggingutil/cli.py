import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import click

from .config import LogConfig


@click.group()
def main():
    """LoggingUtil CLI - Manage and analyze logs"""
    pass


@main.command()
@click.argument("log_file", type=click.Path(exists=True))
@click.option("--level", "-l", help="Filter by log level")
@click.option("--tag", "-t", help="Filter by tag")
@click.option("--since", "-s", help="Show logs since (e.g. 1h, 2d, 1w)")
@click.option("--format", "-f", default="text", type=click.Choice(["text", "json"]))
def analyze(
    log_file: str,
    level: Optional[str],
    tag: Optional[str],
    since: Optional[str],
    format: str,
):
    """Analyze logs and show statistics"""
    path = Path(log_file)

    # Parse time filter
    if since:
        now = datetime.now()
        unit = since[-1].lower()
        try:
            amount = int(since[:-1])
            if unit == "h":
                since_time = now - timedelta(hours=amount)
            elif unit == "d":
                since_time = now - timedelta(days=amount)
            elif unit == "w":
                since_time = now - timedelta(weeks=amount)
            else:
                click.echo(f"Invalid time unit: {unit}")
                sys.exit(1)
        except ValueError:
            click.echo(f"Invalid time format: {since}")
            sys.exit(1)
    else:
        since_time = None

    # Collect statistics
    stats = {
        "total_logs": 0,
        "levels": {},
        "tags": {},
        "errors": [],
        "time_distribution": {},
    }

    # Process logs
    with path.open() as f:
        for line in f:
            try:
                # Parse log entry
                if line.strip():
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        # Try parsing text format
                        parts = line.split("]")
                        if len(parts) >= 3:
                            timestamp = parts[0].strip("[")
                            level_str = parts[1].strip("[ ")
                            rest = "]".join(parts[2:])
                            entry = {
                                "timestamp": timestamp,
                                "level": level_str,
                                "data": rest.strip(),
                            }
                        else:
                            continue

                    # Apply filters
                    if level and entry.get("level") != level:
                        continue
                    if tag and entry.get("tag") != tag:
                        continue
                    if since_time:
                        try:
                            log_time = datetime.strptime(
                                entry["timestamp"].strip("[]"), "%Y-%m-%d %H:%M:%S"
                            )
                            if log_time < since_time:
                                continue
                        except ValueError:
                            continue

                    # Update statistics
                    stats["total_logs"] += 1

                    # Level stats
                    log_level = entry.get("level", "UNKNOWN")
                    stats["levels"][log_level] = stats["levels"].get(log_level, 0) + 1

                    # Tag stats
                    log_tag = entry.get("tag", "UNTAGGED")
                    stats["tags"][log_tag] = stats["tags"].get(log_tag, 0) + 1

                    # Collect errors
                    if log_level in ("ERROR", "FATAL"):
                        stats["errors"].append(
                            {
                                "timestamp": entry.get("timestamp"),
                                "message": entry.get("data"),
                                "tag": log_tag,
                            }
                        )

                    # Time distribution (by hour)
                    try:
                        hour = datetime.strptime(
                            entry["timestamp"].strip("[]"), "%Y-%m-%d %H:%M:%S"
                        ).hour
                        stats["time_distribution"][hour] = (
                            stats["time_distribution"].get(hour, 0) + 1
                        )
                    except ValueError:
                        pass

            except Exception as e:
                click.echo(f"Error processing line: {e}", err=True)
                continue

    # Output results
    if format == "json":
        click.echo(json.dumps(stats, indent=2))
    else:
        click.echo("\n=== Log Analysis ===")
        click.echo(f"\nTotal Logs: {stats['total_logs']}")

        click.echo("\nLog Levels:")
        for level, count in sorted(stats["levels"].items()):
            click.echo(f"  {level}: {count}")

        click.echo("\nTop Tags:")
        for tag, count in sorted(
            stats["tags"].items(), key=lambda x: x[1], reverse=True
        )[:10]:
            click.echo(f"  {tag}: {count}")

        if stats["errors"]:
            click.echo("\nRecent Errors:")
            for error in stats["errors"][-5:]:
                click.echo(f"  [{error['timestamp']}] {error['message']}")

        click.echo("\nTime Distribution:")
        max_count = max(stats["time_distribution"].values(), default=0)
        for hour in range(24):
            count = stats["time_distribution"].get(hour, 0)
            bar = "#" * int(20 * count / max_count) if max_count > 0 else ""
            click.echo(f"  {hour:02d}:00 {bar} ({count})")


@main.command()
@click.argument("log_file", type=click.Path(exists=True))
@click.option("--output", "-o", help="Output SQLite database file")
def convert(log_file: str, output: Optional[str]):
    """Convert log file to SQLite database for better querying"""
    if not output:
        output = str(Path(log_file).with_suffix(".db"))

    conn = sqlite3.connect(output)
    c = conn.cursor()

    # Create table
    c.execute(
        """CREATE TABLE IF NOT EXISTS logs
                 (timestamp TEXT, level TEXT, tag TEXT,
                  correlation_id TEXT, data TEXT)"""
    )

    # Process logs
    with open(log_file) as f:
        for line in f:
            try:
                if line.strip():
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        # Try parsing text format
                        parts = line.split("]")
                        if len(parts) >= 3:
                            timestamp = parts[0].strip("[")
                            level = parts[1].strip("[ ")
                            data = "]".join(parts[2:]).strip()
                            entry = {
                                "timestamp": timestamp,
                                "level": level,
                                "data": data,
                            }
                        else:
                            continue

                    c.execute(
                        "INSERT INTO logs VALUES (?, ?, ?, ?, ?)",
                        (
                            entry.get("timestamp"),
                            entry.get("level"),
                            entry.get("tag"),
                            entry.get("correlation_id"),
                            json.dumps(entry.get("data")),
                        ),
                    )

            except Exception as e:
                click.echo(f"Error processing line: {e}", err=True)
                continue

    conn.commit()
    conn.close()
    click.echo(f"Converted to SQLite database: {output}")


@main.command()
@click.argument("config_file", type=click.Path(exists=True))
def validate(config_file: str):
    """Validate logging configuration file"""
    path = Path(config_file)
    try:
        if path.suffix == ".yaml":
            config = LogConfig.from_yaml(config_file)
        elif path.suffix == ".json":
            config = LogConfig.from_json(config_file)
        else:
            click.echo("Unsupported config file format")
            sys.exit(1)

        click.echo("Configuration is valid!")
        click.echo("\nSettings:")
        for key, value in config.config.items():
            click.echo(f"  {key}: {value}")

    except Exception as e:
        click.echo(f"Invalid configuration: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
