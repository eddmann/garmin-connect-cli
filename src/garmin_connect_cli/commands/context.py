"""Context command - aggregated data for LLM prompts."""

from __future__ import annotations

import sys
from datetime import date
from typing import Annotated

import typer

from garmin_connect_cli.client import get_client
from garmin_connect_cli.core import emit, state


def _log_error(message: str, exc: Exception) -> None:
    """Log error to stderr if verbose mode is enabled."""
    if state.verbose:
        print(f"warning: {message}: {exc}", file=sys.stderr)


app = typer.Typer(invoke_without_command=True)


@app.callback(invoke_without_command=True)
def context(
    ctx: typer.Context,
    activities_limit: Annotated[
        int,
        typer.Option(
            "--activities",
            "-a",
            help="Number of recent activities to include",
        ),
    ] = 5,
    include_health: Annotated[
        bool,
        typer.Option(
            "--health/--no-health",
            help="Include health metrics",
        ),
    ] = True,
    include_stats: Annotated[
        bool,
        typer.Option(
            "--stats/--no-stats",
            help="Include daily stats",
        ),
    ] = True,
    include_training: Annotated[
        bool,
        typer.Option(
            "--training/--no-training",
            help="Include training metrics (status, readiness, VO2max)",
        ),
    ] = True,
    include_weight: Annotated[
        bool,
        typer.Option(
            "--weight/--no-weight",
            help="Include weight and body composition",
        ),
    ] = True,
    focus: Annotated[
        str | None,
        typer.Option(
            "--focus",
            "-f",
            help="Focus area: activities, stats, health, training, weight (comma-separated)",
        ),
    ] = None,
) -> None:
    """Get aggregated context for LLM prompts.

    Returns profile, stats, health metrics, training data, weight,
    and recent activities in a single call - optimized for LLM context windows.

    Examples:
        garmin-connect context
        garmin-connect context --activities 10
        garmin-connect context --focus stats,health,training
        garmin-connect context --no-health --no-weight
    """
    if ctx.invoked_subcommand is not None:
        return

    # Parse focus areas
    focus_areas = set(focus.split(",")) if focus else None

    # Initialize client
    from garmin_connect_cli.config import Config

    config = Config.load(state.config_path)
    client = get_client(config, state.profile)

    result = {}
    today = date.today().isoformat()

    # Always include basic profile info
    try:
        profile = client.get_user_profile()
        result["profile"] = {
            "displayName": profile.get("displayName"),
            "fullName": client.get_full_name(),
            "profileImageUrl": profile.get("profileImageUrlLarge"),
        }
    except Exception as e:
        _log_error("Failed to fetch profile", e)
        result["profile"] = None

    # Include stats
    if include_stats and (focus_areas is None or "stats" in focus_areas):
        try:
            summary = client.get_user_summary(today)
            result["today_stats"] = {
                "totalSteps": summary.get("totalSteps"),
                "totalDistanceMeters": summary.get("totalDistanceMeters"),
                "totalKilocalories": summary.get("totalKilocalories"),
                "floorsClimbed": summary.get("floorsClimbed"),
                "activeTimeInSeconds": summary.get("activeTimeInSeconds"),
                "minHeartRate": summary.get("minHeartRate"),
                "maxHeartRate": summary.get("maxHeartRate"),
                "restingHeartRate": summary.get("restingHeartRate"),
            }
        except Exception as e:
            _log_error("Failed to fetch stats", e)
            result["today_stats"] = None

    # Include health metrics
    if include_health and (focus_areas is None or "health" in focus_areas):
        health = {}

        try:
            hr = client.get_heart_rates(today)
            health["heart_rate"] = {
                "resting": hr.get("restingHeartRate"),
                "min": hr.get("minHeartRate"),
                "max": hr.get("maxHeartRate"),
            }
        except Exception as e:
            _log_error("Failed to fetch heart rate", e)
            health["heart_rate"] = None

        try:
            sleep = client.get_sleep_data(today)
            if sleep and "dailySleepDTO" in sleep:
                dto = sleep["dailySleepDTO"]
                health["sleep"] = {
                    "sleepTimeSeconds": dto.get("sleepTimeSeconds"),
                    "deepSleepSeconds": dto.get("deepSleepSeconds"),
                    "lightSleepSeconds": dto.get("lightSleepSeconds"),
                    "remSleepSeconds": dto.get("remSleepSeconds"),
                    "awakeSleepSeconds": dto.get("awakeSleepSeconds"),
                }
            else:
                health["sleep"] = None
        except Exception as e:
            _log_error("Failed to fetch sleep data", e)
            health["sleep"] = None

        try:
            bb = client.get_body_battery(today)
            if bb and isinstance(bb, list) and len(bb) > 0:
                # Get latest body battery reading
                health["body_battery"] = bb[-1] if bb else None
            else:
                health["body_battery"] = None
        except Exception as e:
            _log_error("Failed to fetch body battery", e)
            health["body_battery"] = None

        try:
            stress = client.get_stress_data(today)
            if stress:
                health["stress"] = {
                    "overallStressLevel": stress.get("overallStressLevel"),
                    "restStressLevel": stress.get("restStressLevel"),
                    "activityStressLevel": stress.get("activityStressLevel"),
                }
            else:
                health["stress"] = None
        except Exception as e:
            _log_error("Failed to fetch stress data", e)
            health["stress"] = None

        result["health"] = health

    # Include training metrics
    if include_training and (focus_areas is None or "training" in focus_areas):
        training = {}

        try:
            status = client.get_training_status(today)
            training["status"] = status.get("trainingStatusPhrase")
        except Exception as e:
            _log_error("Failed to fetch training status", e)
            training["status"] = None

        try:
            readiness = client.get_training_readiness(today)
            training["readiness"] = readiness.get("readinessScore")
        except Exception as e:
            _log_error("Failed to fetch training readiness", e)
            training["readiness"] = None

        try:
            metrics = client.get_max_metrics(today)
            if metrics:
                generic = metrics.get("generic", {})
                cycling = metrics.get("cycling", {})
                training["vo2max_running"] = generic.get("vo2MaxValue")
                training["vo2max_cycling"] = cycling.get("vo2MaxValue")
        except Exception as e:
            _log_error("Failed to fetch VO2max metrics", e)
            training["vo2max_running"] = None
            training["vo2max_cycling"] = None

        result["training"] = training

    # Include weight and body composition
    if include_weight and (focus_areas is None or "weight" in focus_areas):
        weight_data = {}

        try:
            body_comp = client.get_body_composition(today)
            if body_comp:
                # Weight is in grams, convert to kg
                weight_g = body_comp.get("weight")
                weight_data["current_kg"] = weight_g / 1000 if weight_g else None
                weight_data["body_fat_pct"] = body_comp.get("bodyFat")
                # Muscle mass is in grams, convert to kg
                muscle_g = body_comp.get("muscleMass")
                weight_data["muscle_mass_kg"] = muscle_g / 1000 if muscle_g else None
        except Exception as e:
            _log_error("Failed to fetch body composition", e)
            weight_data["current_kg"] = None
            weight_data["body_fat_pct"] = None
            weight_data["muscle_mass_kg"] = None

        result["weight"] = weight_data

    # Include recent activities
    if focus_areas is None or "activities" in focus_areas:
        try:
            activities = client.get_activities(start=0, limit=activities_limit)
            result["recent_activities"] = [
                {
                    "activityId": a.get("activityId"),
                    "activityName": a.get("activityName"),
                    "activityType": a.get("activityType", {}).get("typeKey")
                    if isinstance(a.get("activityType"), dict)
                    else a.get("activityType"),
                    "distance": a.get("distance"),
                    "duration": a.get("duration"),
                    "startTimeLocal": a.get("startTimeLocal"),
                    "averageHR": a.get("averageHR"),
                    "calories": a.get("calories"),
                    "elevationGain": a.get("elevationGain"),
                }
                for a in activities
            ]
        except Exception as e:
            _log_error("Failed to fetch activities", e)
            result["recent_activities"] = []

    emit(result)
