"""Main CLI entry point."""

from __future__ import annotations

import sys
from typing import Annotated

import typer

from garmin_connect_cli import __version__
from garmin_connect_cli.commands import (
    activities,
    athlete,
    auth,
    context,
    health,
    training,
    weight,
)
from garmin_connect_cli.core import state
from garmin_connect_cli.output import OutputFormat

# Exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_AUTH_ERROR = 2

app = typer.Typer(
    name="garmin-connect",
    help="Garmin Connect from your terminal. Pipe it, script it, automate it.",
    no_args_is_help=True,
    add_completion=True,
    rich_markup_mode="rich",
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        print(f"garmin-connect-cli {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    format: Annotated[
        OutputFormat,
        typer.Option(
            "--format",
            "-f",
            help="Output format",
            envvar="GARMIN_FORMAT",
        ),
    ] = OutputFormat.json,
    fields: Annotated[
        str | None,
        typer.Option(
            "--fields",
            help="Comma-separated list of fields to include in output",
        ),
    ] = None,
    no_header: Annotated[
        bool,
        typer.Option(
            "--no-header",
            help="Omit header row in CSV/TSV output",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Verbose output to stderr",
        ),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Suppress non-essential output",
        ),
    ] = False,
    config: Annotated[
        str | None,
        typer.Option(
            "--config",
            "-c",
            help="Path to config file",
            envvar="GARMIN_CONFIG",
        ),
    ] = None,
    profile: Annotated[
        str | None,
        typer.Option(
            "--profile",
            "-p",
            help="Named profile to use",
            envvar="GARMIN_PROFILE",
        ),
    ] = None,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit",
        ),
    ] = False,
) -> None:
    """Global options applied to all commands."""
    # Mutual exclusivity check
    if verbose and quiet:
        print("error: --verbose and --quiet are mutually exclusive", file=sys.stderr)
        raise typer.Exit(EXIT_ERROR)

    state.format = format
    state.fields = fields.split(",") if fields else None
    state.no_header = no_header
    state.verbose = verbose
    state.quiet = quiet
    state.config_path = config
    state.profile = profile


# Register subcommands
app.add_typer(auth.app, name="auth", help="Authentication commands")
app.add_typer(athlete.app, name="athlete", help="Athlete profile and stats")
app.add_typer(activities.app, name="activities", help="Activity management")
app.add_typer(health.app, name="health", help="Health data (sleep, HR, steps, etc.)")
app.add_typer(training.app, name="training", help="Training metrics (status, VO2max, HRV, etc.)")
app.add_typer(weight.app, name="weight", help="Weight and body composition")
app.add_typer(context.app, name="context", help="Aggregated context for LLMs")


def error(message: str, exit_code: int = EXIT_ERROR) -> None:
    """Print error message to stderr and exit."""
    print(f"error: {message}", file=sys.stderr)
    raise typer.Exit(exit_code)


def auth_error(message: str) -> None:
    """Print auth error message to stderr and exit."""
    error(message, EXIT_AUTH_ERROR)


if __name__ == "__main__":
    app()
