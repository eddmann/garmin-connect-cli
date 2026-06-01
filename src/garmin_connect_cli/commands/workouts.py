"""Workout template and scheduling commands."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Annotated

import typer

from garmin_connect_cli.client import GarminClient
from garmin_connect_cli.core import emit, emit_result, with_client

app = typer.Typer(no_args_is_help=True)

_NO_TARGET = {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"}
_PACE_ZONE = {"workoutTargetTypeId": 6, "workoutTargetTypeKey": "pace.zone"}
_HR_ZONE = {"workoutTargetTypeId": 4, "workoutTargetTypeKey": "heart.rate.zone"}
_DIST = {"conditionTypeId": 3, "conditionTypeKey": "distance"}
_TIME = {"conditionTypeId": 2, "conditionTypeKey": "time"}
_ITER = {"conditionTypeId": 6, "conditionTypeKey": "iterations"}
_RUNNING = {"sportTypeId": 1, "sportTypeKey": "running"}


def _step(
    order: int,
    type_id: int,
    type_key: str,
    cond: dict,
    value: float,
    target: dict,
    t1: float | None = None,
    t2: float | None = None,
) -> dict:
    return {
        "type": "ExecutableStepDTO",
        "stepOrder": order,
        "stepType": {"stepTypeId": type_id, "stepTypeKey": type_key},
        "endCondition": cond,
        "endConditionValue": value,
        "targetType": target,
        "targetValueOne": t1,
        "targetValueTwo": t2,
    }


_EXAMPLES = {
    "easy_run": {
        "sportType": _RUNNING,
        "workoutName": "Easy run — Z2 pace",
        "description": "Warmup 500m → 3km at 8:00-9:00 min/km → Cooldown 500m",
        "workoutSegments": [
            {
                "segmentOrder": 1,
                "sportType": _RUNNING,
                "workoutSteps": [
                    _step(1, 1, "warmup", _DIST, 500.0, _NO_TARGET),
                    _step(2, 3, "interval", _DIST, 3000.0, _PACE_ZONE, 2.083, 1.852),
                    _step(3, 2, "cooldown", _DIST, 500.0, _NO_TARGET),
                ],
            }
        ],
    },
    "intervals": {
        "sportType": _RUNNING,
        "workoutName": "3×1km intervals",
        "description": "Warmup 1km → 3×(1km fast + 400m recovery) → Cooldown 1km",
        "workoutSegments": [
            {
                "segmentOrder": 1,
                "sportType": _RUNNING,
                "workoutSteps": [
                    _step(1, 1, "warmup", _DIST, 1000.0, _NO_TARGET),
                    {
                        "type": "RepeatGroupDTO",
                        "stepOrder": 2,
                        "stepType": {"stepTypeId": 6, "stepTypeKey": "repeat"},
                        "endCondition": _ITER,
                        "endConditionValue": 3,
                        "workoutSteps": [
                            _step(1, 3, "interval", _DIST, 1000.0, _PACE_ZONE, 2.222, 2.083),
                            _step(2, 4, "recovery", _DIST, 400.0, _NO_TARGET),
                        ],
                    },
                    _step(3, 2, "cooldown", _DIST, 1000.0, _NO_TARGET),
                ],
            }
        ],
    },
    "hr_zone_run": {
        "sportType": _RUNNING,
        "workoutName": "HR zone run — Z2",
        "description": "Warmup 5min → 30min in HR zone 2 (120-140 bpm) → Cooldown 5min",
        "workoutSegments": [
            {
                "segmentOrder": 1,
                "sportType": _RUNNING,
                "workoutSteps": [
                    _step(1, 1, "warmup", _TIME, 300.0, _NO_TARGET),
                    _step(2, 3, "interval", _TIME, 1800.0, _HR_ZONE, 140, 120),
                    _step(3, 2, "cooldown", _TIME, 300.0, _NO_TARGET),
                ],
            }
        ],
    },
}


@app.command("list")
@with_client
def list_workouts(
    client: GarminClient,
    limit: Annotated[
        int,
        typer.Option("--limit", "-n", help="Maximum number of workouts"),
    ] = 20,
    start: Annotated[
        int,
        typer.Option("--start", "-s", help="Start index for pagination"),
    ] = 0,
) -> None:
    """List workout templates.

    Examples:
        garmin-connect workouts list
        garmin-connect workouts list --limit 50
    """
    workouts = client.get_workouts(start=start, limit=limit)
    emit(workouts)


@app.command("get")
@with_client
def get_workout(
    client: GarminClient,
    workout_id: Annotated[str, typer.Argument(help="Workout ID")],
) -> None:
    """Get a single workout template by ID.

    Examples:
        garmin-connect workouts get 123456789
    """
    workout = client.get_workout(workout_id)
    emit(workout)


@app.command("create")
@with_client
def create_workout(
    client: GarminClient,
    source: Annotated[
        str | None,
        typer.Argument(help="JSON file path or '-' to read from stdin"),
    ] = None,
    examples: Annotated[
        bool,
        typer.Option("--examples", help="Print example JSON payloads and exit"),
    ] = False,
) -> None:
    """Create a workout from a JSON file or stdin.

    The JSON must match the Garmin workout API format.
    Use --examples to see ready-to-use templates.

    Examples:
        garmin-connect workouts create workout.json
        cat workout.json | garmin-connect workouts create -
        garmin-connect workouts create --examples
    """
    if examples:
        for name, payload in _EXAMPLES.items():
            print(f"# --- {name} ---")
            print(json.dumps(payload, indent=2))
            print()
        return

    if source is None or source == "-":
        raw = sys.stdin.read()
    else:
        path = Path(source)
        if not path.exists():
            print(f"error: File not found: {source}", file=sys.stderr)
            raise typer.Exit(1)
        raw = path.read_text()

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"error: Invalid JSON: {e}", file=sys.stderr)
        raise typer.Exit(1) from None

    result = client.create_workout(payload)
    workout_id = result.get("workoutId", "unknown")
    workout_name = result.get("workoutName", "")
    emit_result(result, f"Created workout '{workout_name}' (ID: {workout_id})")


@app.command("delete")
@with_client
def delete_workout(
    client: GarminClient,
    workout_id: Annotated[str, typer.Argument(help="Workout ID")],
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Skip confirmation"),
    ] = False,
) -> None:
    """Delete a workout template.

    Examples:
        garmin-connect workouts delete 123456789
        garmin-connect workouts delete 123456789 --force
    """
    if not force:
        confirm = typer.confirm(f"Delete workout {workout_id}?")
        if not confirm:
            raise typer.Abort()

    client.delete_workout(workout_id)
    emit_result({"workout_id": workout_id}, f"Workout {workout_id} deleted")


@app.command("schedule")
@with_client
def schedule_workout(
    client: GarminClient,
    workout_id: Annotated[str, typer.Argument(help="Workout ID")],
    date_arg: Annotated[str, typer.Argument(help="Date (YYYY-MM-DD)", metavar="DATE")],
) -> None:
    """Schedule a workout on a specific date.

    Examples:
        garmin-connect workouts schedule 123456789 2026-06-10
    """
    result = client.schedule_workout(workout_id, date_arg)
    scheduled_id = result.get("scheduledWorkoutId", "unknown")
    msg = f"Workout {workout_id} scheduled on {date_arg} (scheduled ID: {scheduled_id})"
    emit_result(result, msg)


@app.command("unschedule")
@with_client
def unschedule_workout(
    client: GarminClient,
    scheduled_id: Annotated[str, typer.Argument(help="Scheduled workout ID")],
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Skip confirmation"),
    ] = False,
) -> None:
    """Remove a workout from the schedule.

    Use 'workouts calendar' to find scheduled workout IDs.

    Examples:
        garmin-connect workouts unschedule 987654321
        garmin-connect workouts unschedule 987654321 --force
    """
    if not force:
        confirm = typer.confirm(f"Unschedule workout {scheduled_id}?")
        if not confirm:
            raise typer.Abort()

    client.unschedule_workout(scheduled_id)
    emit_result({"scheduled_id": scheduled_id}, f"Scheduled workout {scheduled_id} removed")


@app.command("calendar")
@with_client
def calendar(
    client: GarminClient,
    year: Annotated[
        int | None,
        typer.Option("--year", "-y", help="Year (default: current year)"),
    ] = None,
    month: Annotated[
        int | None,
        typer.Option("--month", "-m", help="Month 1-12 (default: current month)"),
    ] = None,
) -> None:
    """View scheduled workouts for a month.

    Examples:
        garmin-connect workouts calendar
        garmin-connect workouts calendar --year 2026 --month 6
    """
    today = date.today()
    y = year or today.year
    m = month or today.month
    data = client.get_workout_calendar(y, m)
    emit(data)


@app.command("download")
@with_client
def download_workout(
    client: GarminClient,
    workout_id: Annotated[str, typer.Argument(help="Workout ID")],
    output_path: Annotated[
        str | None,
        typer.Option("--output", "-o", help="Output file path (default: <workout_id>.fit)"),
    ] = None,
) -> None:
    """Download a workout as a FIT file.

    Examples:
        garmin-connect workouts download 123456789
        garmin-connect workouts download 123456789 -o my_workout.fit
    """
    data = client.download_workout(workout_id)
    out = output_path or f"{workout_id}.fit"
    Path(out).write_bytes(data)
    emit_result({"path": out, "bytes": len(data)}, f"Downloaded to {out}")
