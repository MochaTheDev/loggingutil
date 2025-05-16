!!! note "Changelog"
    This is a copy of the project's changelog. The original can be found in the [repository root](https://github.com/mochathehuman/loggingutil/blob/main/CHANGELOG.md).

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-03-21

### Breaking Changes
- Complete overhaul of handler system with new implementations
- New configuration system supporting YAML, JSON, and environment variables
- Changed API for structured logging and context management
- Added mandatory correlation IDs for request tracking
- Modified log rotation and cleanup functionality

### Added
- Comprehensive handler implementations (Console, SQLite, Webhook, Email, File, CloudWatch, Elasticsearch)
- Advanced context management with correlation IDs
- Structured logging support with schema validation
- Log rotation and cleanup functionality
- Configuration system with YAML, JSON, and environment variable support
- CLI tool for log management
- Prometheus metrics integration
- Rich console output support
- Elasticsearch integration
- AWS CloudWatch integration
- MkDocs-based documentation

### Changed
- Improved code quality with Black formatting
- Enhanced error handling and exception logging
- Simplified GitHub Actions workflow
- Streamlined CI pipeline
- Reorganized project structure

### Fixed
- Unused imports and code style issues
- Line length compliance
- Whitespace consistency
- Documentation formatting

## [1.2.3] - 2024-03-21

### Added
- Comprehensive handler implementations (Console, SQLite, Webhook, Email, File, CloudWatch, Elasticsearch)
- Advanced context management with correlation IDs
- Structured logging support
- Log rotation and cleanup functionality
- Configuration system with YAML, JSON, and environment variable support
- CLI tool for log management
- Prometheus metrics integration
- Rich console output support
- Elasticsearch integration
- AWS CloudWatch integration

### Changed
- Semi-full overhaul of all major functions
- Improved code quality with Black formatting
- Enhanced error handling and exception logging
- Simplified GitHub Actions workflow
- Streamlined CI pipeline

### Fixed
- Unused imports and code style issues
- Line length compliance
- Whitespace consistency
- Documentation formatting

## [1.2.2] - Initial Release

- Initial public release with basic functionality 