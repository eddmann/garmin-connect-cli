"""Training metrics commands."""

from __future__ import annotations

from datetime import date
from typing import Annotated

import typer

from garmin_connect_cli.client import GarminClient
from garmin_connect_cli.core import emit, with_client

app = typer.Typer(no_args_is_help=True)


@app.command("status")
@with_client
def training_status(
    client: GarminClient,
    date_str: Annotated[
        str | None,
        typer.Option("--date", "-d", help="Date for training status (YYYY-MM-DD)"),
    ] = None,
) -> None:
    """Get training status.

    Returns training status (Productive, Peaking, Recovery, Unproductive, etc.).

    Examples:
        garmin-connect training status
        garmin-connect training status --date 2025-01-01
    """
    target_date = date_str or date.today().isoformat()
    data = client.get_training_status(target_date)
    emit(data)


@app.command("readiness")
@with_client
def training_readiness(
    client: GarminClient,
    date_str: Annotated[
        str | None,
        typer.Option("--date", "-d", help="Date for training readiness (YYYY-MM-DD)"),
    ] = None,
) -> None:
    """Get training readiness score.

    Returns training readiness score (0-100) indicating recovery state.

    Examples:
        garmin-connect training readiness
        garmin-connect training readiness | jq '.readinessScore'
    """
    target_date = date_str or date.today().isoformat()
    data = client.get_training_readiness(target_date)
    emit(data)


@app.command("vo2max")
@with_client
def vo2max(
    client: GarminClient,
    date_str: Annotated[
        str | None,
        typer.Option("--date", "-d", help="Date for VO2 max data (YYYY-MM-DD)"),
    ] = None,
) -> None:
    """Get VO2 max estimates.

    Returns VO2 max estimates for running and cycling.

    Examples:
        garmin-connect training vo2max
        garmin-connect training vo2max | jq '.generic.vo2MaxValue'
    """
    target_date = date_str or date.today().isoformat()
    data = client.get_max_metrics(target_date)
    emit(data)


@app.command("lactate")
@with_client
def lactate_threshold(client: GarminClient) -> None:
    """Get lactate threshold data.

    Returns lactate threshold heart rate, pace, and power (if available).

    Examples:
        garmin-connect training lactate
        garmin-connect training lactate | jq '.lactateThresholdHeartRateInBeatsPerMinute'
    """
    data = client.get_lactate_threshold()
    emit(data)


@app.command("endurance")
@with_client
def endurance_score(
    client: GarminClient,
    date_str: Annotated[
        str | None,
        typer.Option("--date", "-d", help="Date for endurance score (YYYY-MM-DD)"),
    ] = None,
) -> None:
    """Get endurance score.

    Returns endurance score data.

    Examples:
        garmin-connect training endurance
        garmin-connect training endurance --date 2025-01-01
    """
    target_date = date_str or date.today().isoformat()
    data = client.get_endurance_score(target_date)
    emit(data)


@app.command("hill")
@with_client
def hill_score(
    client: GarminClient,
    date_str: Annotated[
        str | None,
        typer.Option("--date", "-d", help="Date for hill score (YYYY-MM-DD)"),
    ] = None,
) -> None:
    """Get hill score.

    Returns hill/climbing ability score.

    Examples:
        garmin-connect training hill
        garmin-connect training hill --date 2025-01-01
    """
    target_date = date_str or date.today().isoformat()
    data = client.get_hill_score(target_date)
    emit(data)


@app.command("hrv")
@with_client
def hrv_data(
    client: GarminClient,
    date_str: Annotated[
        str | None,
        typer.Option("--date", "-d", help="Date for HRV data (YYYY-MM-DD)"),
    ] = None,
) -> None:
    """Get heart rate variability data.

    Returns HRV metrics including RMSSD and status.

    Examples:
        garmin-connect training hrv
        garmin-connect training hrv | jq '.hrvSummary'
    """
    target_date = date_str or date.today().isoformat()
    data = client.get_hrv_data(target_date)
    emit(data)


@app.command("fitness-age")
@with_client
def fitness_age(client: GarminClient) -> None:
    """Get fitness age.

    Returns calculated fitness age based on VO2 max and activity.

    Examples:
        garmin-connect training fitness-age
        garmin-connect training fitness-age | jq '.fitnessAge'
    """
    data = client.get_fitnessage_data()
    emit(data)
