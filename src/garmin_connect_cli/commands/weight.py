"""Weight and body composition commands."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Annotated

import typer

from garmin_connect_cli.client import GarminClient
from garmin_connect_cli.core import emit, emit_result, with_client

app = typer.Typer(no_args_is_help=True)


@app.command("list")
@with_client
def list_weights(
    client: GarminClient,
    start: Annotated[
        str | None,
        typer.Option("--start", "-s", help="Start date (YYYY-MM-DD, default: 30 days ago)"),
    ] = None,
    end: Annotated[
        str | None,
        typer.Option("--end", "-e", help="End date (YYYY-MM-DD, default: today)"),
    ] = None,
) -> None:
    """List weight entries.

    Returns weight measurements between start and end dates.

    Examples:
        garmin-connect weight list
        garmin-connect weight list --start 2025-01-01 --end 2025-01-31
        garmin-connect weight list | jq '.[].weight'
    """
    end_date = end or date.today().isoformat()
    start_date = start or (date.today() - timedelta(days=30)).isoformat()

    data = client.get_weigh_ins(start_date, end_date)
    emit(data)


@app.command("get")
@with_client
def get_weight(
    client: GarminClient,
    date_str: Annotated[
        str | None,
        typer.Option("--date", "-d", help="Date for weight data (YYYY-MM-DD)"),
    ] = None,
) -> None:
    """Get weight for a specific date.

    Returns weight measurement for the specified date.

    Examples:
        garmin-connect weight get
        garmin-connect weight get --date 2025-01-01
    """
    target_date = date_str or date.today().isoformat()
    data = client.get_daily_weigh_ins(target_date)
    emit(data)


@app.command("body-comp")
@with_client
def body_composition(
    client: GarminClient,
    date_str: Annotated[
        str | None,
        typer.Option("--date", "-d", help="Date for body composition (YYYY-MM-DD)"),
    ] = None,
) -> None:
    """Get body composition data.

    Returns body fat percentage, muscle mass, bone mass, water percentage.

    Examples:
        garmin-connect weight body-comp
        garmin-connect weight body-comp | jq '.bodyFat'
    """
    target_date = date_str or date.today().isoformat()
    data = client.get_body_composition(target_date)
    emit(data)


@app.command("log")
@with_client
def log_weight(
    client: GarminClient,
    weight: Annotated[float, typer.Argument(help="Weight in kilograms")],
    date_str: Annotated[
        str | None,
        typer.Option("--date", "-d", help="Date for weight entry (YYYY-MM-DD, default: today)"),
    ] = None,
) -> None:
    """Log a weight measurement.

    Records a weight measurement to Garmin Connect.

    Examples:
        garmin-connect weight log 70.5
        garmin-connect weight log 70.5 --date 2025-01-01
    """
    target_date = date_str or date.today().isoformat()
    result = client.add_weigh_in(weight=weight, unitKey="kg", date=target_date)
    data = result if result else {"weight": weight, "date": target_date}
    emit_result(data, f"Weight {weight} kg logged for {target_date}")


@app.command("delete")
@with_client
def delete_weight(
    client: GarminClient,
    pk: Annotated[int, typer.Argument(help="Weight entry primary key to delete")],
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Skip confirmation prompt"),
    ] = False,
) -> None:
    """Delete a weight entry.

    Deletes a specific weight entry by its primary key.

    Examples:
        garmin-connect weight delete 12345678
        garmin-connect weight delete 12345678 --force
    """
    if not force:
        confirm = typer.confirm(f"Delete weight entry {pk}?")
        if not confirm:
            raise typer.Abort()

    client.delete_weigh_in(pk)
    emit_result({"pk": pk}, f"Weight entry {pk} deleted")


@app.command("delete-date")
@with_client
def delete_weights_for_date(
    client: GarminClient,
    date_str: Annotated[str, typer.Argument(help="Date to delete weights for (YYYY-MM-DD)")],
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Skip confirmation prompt"),
    ] = False,
) -> None:
    """Delete all weight entries for a date.

    Deletes all weight measurements recorded on the specified date.

    Examples:
        garmin-connect weight delete-date 2025-01-01
        garmin-connect weight delete-date 2025-01-01 --force
    """
    if not force:
        confirm = typer.confirm(f"Delete all weight entries for {date_str}?")
        if not confirm:
            raise typer.Abort()

    client.delete_weigh_ins(date_str)
    emit_result({"date": date_str}, f"Weight entries for {date_str} deleted")
