# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-05-20

### Changed

- Update Garmin authentication to use the python-garminconnect 0.3 token flow
- Require Python 3.12+ to match the latest python-garminconnect release

## [0.1.1] - 2026-01-20

### Changed

- Release workflow now extracts version and release notes automatically from CHANGELOG.md

## [0.1.0] - 2025-12-23

### Added

- Initial garmin-connect-cli implementation
- Access Garmin Connect data from your terminal
- Machine-readable output (JSON, JSONL, CSV, TSV)
- Human-friendly table output
- Session-based authentication with token persistence
- Activities, health metrics, training status, weight tracking
- LLM-optimized context aggregation

### Fixed

- Use macos-15-intel instead of deprecated macos-13 in release workflow

[1.0.0]: https://github.com/eddmann/garmin-connect-cli/compare/v0.1.1...v1.0.0
[0.1.1]: https://github.com/eddmann/garmin-connect-cli/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/eddmann/garmin-connect-cli/releases/tag/v0.1.0
