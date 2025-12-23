"""Athlete profile commands."""

from __future__ import annotations

from datetime import date
from typing import Annotated

import typer

from garmin_connect_cli.client import GarminClient
from garmin_connect_cli.core import emit, with_client

app = typer.Typer(invoke_without_command=True)


@app.callback(invoke_without_command=True)
@with_client
def athlete_profile(client: GarminClient, ctx: typer.Context) -> None:
    """Get athlete profile.

    When called without a subcommand, returns the user profile.

    Examples:
        garmin-connect athlete
        garmin-connect athlete | jq '.displayName'
    """
    if ctx.invoked_subcommand is not None:
        return

    profile = client.get_user_profile()
    emit(profile)


@app.command("stats")
@with_client
def stats(
    client: GarminClient,
    date_str: Annotated[
        str | None,
        typer.Option("--date", "-d", help="Date for stats (YYYY-MM-DD, default: today)"),
    ] = None,
) -> None:
    """Get daily statistics.

    Examples:
        garmin-connect athlete stats
        garmin-connect athlete stats --date 2025-01-01
        garmin-connect athlete stats | jq '.totalSteps'
    """
    target_date = date_str or date.today().isoformat()
    stats_data = client.get_user_summary(target_date)
    emit(stats_data)


@app.command("summary")
@with_client
def summary(
    client: GarminClient,
    date_str: Annotated[
        str | None,
        typer.Option("--date", "-d", help="Date for summary (YYYY-MM-DD, default: today)"),
    ] = None,
) -> None:
    """Get comprehensive daily summary with body metrics.

    Examples:
        garmin-connect athlete summary
        garmin-connect athlete summary --date 2025-01-01
    """
    target_date = date_str or date.today().isoformat()
    summary_data = client.get_stats_and_body(target_date)
    emit(summary_data)
