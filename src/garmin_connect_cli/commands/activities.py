"""Activity commands."""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Annotated

import typer

from garmin_connect_cli.client import GarminClient
from garmin_connect_cli.core import emit, emit_result, with_client

app = typer.Typer(no_args_is_help=True)


@app.command("list")
@with_client
def list_activities(
    client: GarminClient,
    limit: Annotated[
        int,
        typer.Option("--limit", "-n", help="Maximum number of activities"),
    ] = 30,
    start: Annotated[
        int,
        typer.Option("--start", "-s", help="Start index for pagination"),
    ] = 0,
    after: Annotated[
        str | None,
        typer.Option("--after", "-a", help="Only activities after this date (YYYY-MM-DD)"),
    ] = None,
    before: Annotated[
        str | None,
        typer.Option("--before", "-b", help="Only activities before this date (YYYY-MM-DD)"),
    ] = None,
    activity_type: Annotated[
        str | None,
        typer.Option("--type", "-t", help="Filter by activity type (running, cycling, etc.)"),
    ] = None,
) -> None:
    """List activities.

    Returns activities in reverse chronological order.

    Examples:
        garmin-connect activities list --limit 10
        garmin-connect activities list --after 2025-01-01 --type running
        garmin-connect activities list | jq '.[].activityName'
    """
    if after or before:
        # Use date range query
        end_date = before or date.today().isoformat()
        start_date = after or (date.today() - timedelta(days=365)).isoformat()
        activities = client.get_activities_by_date(
            start_date=start_date,
            end_date=end_date,
            activity_type=activity_type,
        )
        # Apply limit manually for date-based query
        activities = activities[:limit]
    else:
        activities = client.get_activities(start=start, limit=limit)

    emit(activities)


@app.command("get")
@with_client
def get_activity(
    client: GarminClient,
    activity_id: Annotated[int, typer.Argument(help="Activity ID")],
    details: Annotated[
        bool,
        typer.Option("--details", "-d", help="Include detailed metrics"),
    ] = False,
) -> None:
    """Get a single activity by ID.

    Examples:
        garmin-connect activities get 12345678
        garmin-connect activities get 12345678 --details
    """
    if details:
        activity = client.get_activity_details(activity_id)
    else:
        activity = client.get_activity(activity_id)

    emit(activity)


@app.command("splits")
@with_client
def get_splits(
    client: GarminClient,
    activity_id: Annotated[int, typer.Argument(help="Activity ID")],
) -> None:
    """Get activity splits (lap data).

    Examples:
        garmin-connect activities splits 12345678
    """
    splits = client.get_activity_splits(activity_id)
    emit(splits)


@app.command("download")
@with_client
def download_activity(
    client: GarminClient,
    activity_id: Annotated[int, typer.Argument(help="Activity ID")],
    dl_format: Annotated[
        str,
        typer.Option("--format", "-f", help="Download format: TCX, GPX, ORIGINAL (FIT zip), CSV"),
    ] = "TCX",
    output_path: Annotated[
        str | None,
        typer.Option("--output", "-o", help="Output file path"),
    ] = None,
) -> None:
    """Download activity data file.

    Examples:
        garmin-connect activities download 12345678 --format GPX
        garmin-connect activities download 12345678 -o activity.tcx
    """
    data = client.download_activity(activity_id, dl_fmt=dl_format.upper())

    if output_path:
        Path(output_path).write_bytes(data)
        emit_result(
            {"path": output_path, "bytes": len(data)},
            f"Downloaded to {output_path}",
        )
    else:
        # Write to stdout for piping
        sys.stdout.buffer.write(data)


@app.command("upload")
@with_client
def upload_activity(
    client: GarminClient,
    file_path: Annotated[str, typer.Argument(help="Path to activity file (FIT, GPX, TCX)")],
) -> None:
    """Upload an activity file.

    Examples:
        garmin-connect activities upload morning_run.fit
        garmin-connect activities upload workout.gpx
    """
    if not Path(file_path).exists():
        print(f"error: File not found: {file_path}", file=sys.stderr)
        raise typer.Exit(1)

    response = client.upload_activity(file_path)
    successes = response.get("detailedImportResult", {}).get("successes", [{}])
    activity_id = successes[0].get("internalId", "unknown") if successes else "unknown"
    emit_result(response, f"Uploaded: activity {activity_id}")


@app.command("delete")
@with_client
def delete_activity(
    client: GarminClient,
    activity_id: Annotated[int, typer.Argument(help="Activity ID")],
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Skip confirmation"),
    ] = False,
) -> None:
    """Delete an activity.

    Examples:
        garmin-connect activities delete 12345678
        garmin-connect activities delete 12345678 --force
    """
    if not force:
        confirm = typer.confirm(f"Delete activity {activity_id}?")
        if not confirm:
            raise typer.Abort()

    client.delete_activity(activity_id)
    emit_result({"activity_id": activity_id}, f"Activity {activity_id} deleted")
