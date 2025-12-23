"""Health data commands."""

from __future__ import annotations

from datetime import date
from typing import Annotated

import typer

from garmin_connect_cli.client import GarminClient
from garmin_connect_cli.core import emit, with_client

app = typer.Typer(no_args_is_help=True)


@app.command("sleep")
@with_client
def sleep(
    client: GarminClient,
    date_str: Annotated[
        str | None,
        typer.Option("--date", "-d", help="Date for sleep data (YYYY-MM-DD, default: today)"),
    ] = None,
) -> None:
    """Get sleep data.

    Returns sleep stages, duration, and quality metrics.

    Examples:
        garmin-connect health sleep
        garmin-connect health sleep --date 2025-01-01
        garmin-connect health sleep | jq '.dailySleepDTO.sleepTimeSeconds'
    """
    target_date = date_str or date.today().isoformat()
    sleep_data = client.get_sleep_data(target_date)
    emit(sleep_data)


@app.command("heart-rate")
@with_client
def heart_rate(
    client: GarminClient,
    date_str: Annotated[
        str | None,
        typer.Option("--date", "-d", help="Date for heart rate data (YYYY-MM-DD)"),
    ] = None,
) -> None:
    """Get heart rate data.

    Returns resting, min, max heart rates and timestamped values.

    Examples:
        garmin-connect health heart-rate
        garmin-connect health heart-rate | jq '.restingHeartRate'
    """
    target_date = date_str or date.today().isoformat()
    hr_data = client.get_heart_rates(target_date)
    emit(hr_data)


@app.command("steps")
@with_client
def steps(
    client: GarminClient,
    date_str: Annotated[
        str | None,
        typer.Option("--date", "-d", help="Date for steps data (YYYY-MM-DD)"),
    ] = None,
) -> None:
    """Get steps data.

    Examples:
        garmin-connect health steps
        garmin-connect health steps --date 2025-01-01
    """
    target_date = date_str or date.today().isoformat()
    steps_data = client.get_steps_data(target_date)
    emit(steps_data)


@app.command("stress")
@with_client
def stress(
    client: GarminClient,
    date_str: Annotated[
        str | None,
        typer.Option("--date", "-d", help="Date for stress data (YYYY-MM-DD)"),
    ] = None,
) -> None:
    """Get stress data.

    Examples:
        garmin-connect health stress
        garmin-connect health stress | jq '.overallStressLevel'
    """
    target_date = date_str or date.today().isoformat()
    stress_data = client.get_stress_data(target_date)
    emit(stress_data)


@app.command("body-battery")
@with_client
def body_battery(
    client: GarminClient,
    date_str: Annotated[
        str | None,
        typer.Option("--date", "-d", help="Date for body battery data (YYYY-MM-DD)"),
    ] = None,
) -> None:
    """Get body battery data.

    Examples:
        garmin-connect health body-battery
        garmin-connect health body-battery | jq '.[0].bodyBatteryLevel'
    """
    target_date = date_str or date.today().isoformat()
    bb_data = client.get_body_battery(target_date)
    emit(bb_data)


@app.command("rhr")
@with_client
def resting_heart_rate(
    client: GarminClient,
    date_str: Annotated[
        str | None,
        typer.Option("--date", "-d", help="Date for RHR (YYYY-MM-DD)"),
    ] = None,
) -> None:
    """Get resting heart rate.

    Examples:
        garmin-connect health rhr
    """
    target_date = date_str or date.today().isoformat()
    rhr_data = client.get_rhr_day(target_date)
    emit(rhr_data)
