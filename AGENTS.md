# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

## Project Overview

garmin-connect-cli lets you access Garmin Connect from your terminal. Pipe it, script it, automate it. Supports multiple output formats (JSON, JSONL, CSV, TSV, human-readable tables).

## Development Commands

```bash
make install                              # Install dependencies
make run CMD="activities list --limit 5"  # Run CLI command
make test                                 # Run all tests
make test/test_cli.py::test_function_name # Run single test
make lint                                 # Check linting
make fmt                                  # Format and auto-fix
make can-release                          # Run all CI checks (lint + test)
```

## Architecture

### Source Layout

```
src/garmin_connect_cli/
├── cli.py           # Main Typer app, global options
├── core.py          # State singleton, @with_client decorator, emit() helper
├── client.py        # GarminClient wrapper with token management via Garth
├── config.py        # XDG-compliant config (TOML), token path helpers
├── output.py        # Output formatters (JSON, JSONL, CSV, TSV, human tables)
└── commands/        # Subcommand modules (each exports a Typer app)
    ├── activities.py
    ├── athlete.py
    ├── auth.py
    ├── context.py
    ├── health.py
    ├── training.py
    └── weight.py
```

### Key Patterns

**Command Structure**: Each command module creates a `typer.Typer()` app and registers commands using `@app.command()`. Commands access global state via `core.state` for format/fields/profile options.

**Client Pattern**: Commands use the `@with_client` decorator from `core.py` to inject an authenticated `GarminClient`. This decorator hides the `client` parameter from Typer's CLI parser and handles authentication automatically:

```python
@app.command("list")
@with_client
def list_activities(client: GarminClient, limit: int = 30) -> None:
    activities = client.get_activities(limit=limit)
    emit(activities)
```

**Output**: garminconnect returns JSON-serializable dicts, no model serialization needed.

**Authentication**: Tokens are stored in `~/.config/garmin-connect-cli/tokens/` (managed by the Garth library). CLI preferences are in `config.toml`. Authentication uses email/password with optional MFA support.

### Testing

Tests mock garminconnect.Garmin at the class boundary. Key fixtures:
- `mock_garminconnect`: Patches `garmin_connect_cli.client.Garmin`
- `authenticated_env`: Creates temp config and mock token files
- `cli_runner`: Typer's CliRunner for testing commands
- `tmp_token_dir`: Creates mock token directory with token files

### Data Units

Metric: distances (m), times (s), speeds (m/s), elevation (m), dates (ISO8601), HR (BPM).
