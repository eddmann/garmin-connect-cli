"""Shared test fixtures for garmin-connect-cli."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a Typer CLI test runner."""
    return CliRunner()


@pytest.fixture
def tmp_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Set up a temporary config directory using XDG_CONFIG_HOME."""
    config_dir = tmp_path / "garmin-connect-cli"
    config_dir.mkdir(parents=True)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    return config_dir


@pytest.fixture
def tmp_token_dir(tmp_config_dir: Path) -> Path:
    """Set up a temporary token directory within the config directory."""
    # Tokens are now stored in ~/.config/garmin-connect-cli/tokens/
    token_dir = tmp_config_dir / "tokens"
    token_dir.mkdir(parents=True)

    # Create mock token files that garminconnect/Garth expects
    (token_dir / "oauth1_token.json").write_text('{"token": "mock_oauth1"}')
    (token_dir / "oauth2_token.json").write_text('{"token": "mock_oauth2"}')

    return token_dir


@pytest.fixture
def unauthenticated_env(tmp_config_dir: Path) -> Path:
    """Set up environment without tokens (unauthenticated state).

    Uses tmp_config_dir which sets XDG_CONFIG_HOME, but doesn't create
    the tokens subdirectory.
    """
    return tmp_config_dir


@pytest.fixture
def authenticated_config(tmp_config_dir: Path) -> Path:
    """Create a config file with defaults."""
    config_file = tmp_config_dir / "config.toml"
    config_file.write_text("""[defaults]
format = "json"
limit = 30
""")
    return config_file


@pytest.fixture
def unauthenticated_config(tmp_config_dir: Path) -> Path:
    """Create a config file without authentication."""
    config_file = tmp_config_dir / "config.toml"
    config_file.write_text("""[defaults]
format = "json"
limit = 30
""")
    return config_file


@pytest.fixture
def authenticated_env(
    tmp_config_dir: Path,
    tmp_token_dir: Path,
    authenticated_config: Path,
) -> Path:
    """Create fully authenticated environment with config and tokens."""
    return authenticated_config


class MockModel:
    """A simple mock object that serializes properly via __dict__."""

    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)


@pytest.fixture
def mock_garminconnect() -> Generator[MagicMock, None, None]:
    """Mock garminconnect.Garmin at the module boundary."""
    with patch("garmin_connect_cli.client.Garmin") as mock_garmin_class:
        mock_client = MagicMock()
        mock_garmin_class.return_value = mock_client

        # Configure default return values
        mock_client.get_full_name.return_value = "Test User"

        mock_client.get_user_profile.return_value = {
            "displayName": "testuser",
            "fullName": "Test User",
            "userName": "testuser",
            "profileImageUrlLarge": "https://example.com/image.jpg",
        }

        mock_client.get_unit_system.return_value = {
            "unitSystem": "METRIC",
        }

        mock_client.get_activities.return_value = [
            {
                "activityId": 123456789,
                "activityName": "Morning Run",
                "activityType": {"typeKey": "running"},
                "distance": 5000.0,
                "duration": 1800.0,
                "startTimeLocal": "2025-01-15 08:00:00",
                "averageHR": 145,
                "calories": 350,
                "elevationGain": 50.0,
            }
        ]

        mock_client.get_activities_by_date.return_value = [
            {
                "activityId": 123456789,
                "activityName": "Morning Run",
                "activityType": {"typeKey": "running"},
                "distance": 5000.0,
                "duration": 1800.0,
                "startTimeLocal": "2025-01-15 08:00:00",
                "averageHR": 145,
                "calories": 350,
            }
        ]

        mock_client.get_activity.return_value = {
            "activityId": 123456789,
            "activityName": "Morning Run",
            "activityType": {"typeKey": "running"},
            "distance": 5000.0,
            "duration": 1800.0,
        }

        mock_client.get_activity_details.return_value = {
            "activityId": 123456789,
            "activityName": "Morning Run",
            "activityType": {"typeKey": "running"},
            "distance": 5000.0,
            "duration": 1800.0,
            "metrics": {"heartRate": [120, 145, 160]},
        }

        mock_client.get_activity_splits.return_value = {
            "splits": [
                {"distance": 1000, "duration": 360},
                {"distance": 1000, "duration": 350},
            ]
        }

        mock_client.get_user_summary.return_value = {
            "totalSteps": 10000,
            "totalDistanceMeters": 8000,
            "totalKilocalories": 2500,
            "floorsClimbed": 10,
            "activeTimeInSeconds": 3600,
            "minHeartRate": 50,
            "maxHeartRate": 165,
            "restingHeartRate": 55,
        }

        mock_client.get_stats.return_value = {
            "totalSteps": 10000,
            "totalDistanceMeters": 8000,
        }

        mock_client.get_stats_and_body.return_value = {
            "totalSteps": 10000,
            "weight": 70.5,
            "bodyFat": 15.0,
        }

        mock_client.get_heart_rates.return_value = {
            "restingHeartRate": 55,
            "minHeartRate": 45,
            "maxHeartRate": 165,
            "heartRateValues": [],
        }

        mock_client.get_sleep_data.return_value = {
            "dailySleepDTO": {
                "sleepTimeSeconds": 28800,
                "deepSleepSeconds": 7200,
                "lightSleepSeconds": 14400,
                "remSleepSeconds": 7200,
                "awakeSleepSeconds": 600,
            }
        }

        mock_client.get_steps_data.return_value = {
            "totalSteps": 10000,
            "stepGoal": 10000,
        }

        mock_client.get_stress_data.return_value = {
            "overallStressLevel": 35,
            "restStressLevel": 25,
            "activityStressLevel": 45,
        }

        mock_client.get_body_battery.return_value = [
            {"bodyBatteryLevel": 75, "timestamp": "2025-01-15T08:00:00"},
            {"bodyBatteryLevel": 80, "timestamp": "2025-01-15T12:00:00"},
        ]

        mock_client.get_rhr_day.return_value = {
            "restingHeartRate": 55,
            "date": "2025-01-15",
        }

        # Mock Garth for token operations
        mock_client.garth = MagicMock()
        mock_client.garth.dump = MagicMock()

        # Mock ActivityDownloadFormat enum
        mock_garmin_class.ActivityDownloadFormat = MagicMock()
        mock_garmin_class.ActivityDownloadFormat.TCX = "TCX"
        mock_garmin_class.ActivityDownloadFormat.GPX = "GPX"
        mock_garmin_class.ActivityDownloadFormat.ORIGINAL = "ORIGINAL"
        mock_garmin_class.ActivityDownloadFormat.CSV = "CSV"

        mock_client.download_activity.return_value = b"<tcx>mock data</tcx>"
        mock_client.upload_activity.return_value = {"id": 999999}
        mock_client.delete_activity.return_value = None

        # Training metrics mocks
        mock_client.get_training_status.return_value = {
            "trainingStatusPhrase": "PRODUCTIVE",
            "trainingStatusPhraseDescription": "Your training is productive",
            "primaryLoadType": "ANAEROBIC",
        }

        mock_client.get_training_readiness.return_value = {
            "readinessScore": 72,
            "readinessLevel": "MODERATE",
            "sleepScore": 78,
            "recoveryScore": 68,
        }

        mock_client.get_max_metrics.return_value = {
            "generic": {
                "vo2MaxValue": 52.0,
                "vo2MaxPreciseValue": 52.3,
            },
            "cycling": {
                "vo2MaxValue": 48.0,
            },
        }

        mock_client.get_lactate_threshold.return_value = {
            "lactateThresholdHeartRateInBeatsPerMinute": 165,
            "lactateThresholdSpeed": 4.2,
        }

        mock_client.get_endurance_score.return_value = {
            "enduranceScore": 68,
            "enduranceScoreDate": "2025-01-15",
        }

        mock_client.get_hill_score.return_value = {
            "hillScore": 45,
            "hillScoreDate": "2025-01-15",
        }

        mock_client.get_hrv_data.return_value = {
            "hrvSummary": {
                "lastNightAvg": 45.5,
                "lastNight5MinHigh": 62.0,
                "baseline": {"balancedLow": 40, "balancedUpper": 55},
            },
            "hrvStatus": "BALANCED",
        }

        mock_client.get_fitnessage_data.return_value = {
            "fitnessAge": 32,
            "chronologicalAge": 35,
        }

        # Weight and body composition mocks
        mock_client.get_weigh_ins.return_value = [
            {
                "samplePk": 12345678,
                "weight": 70500.0,
                "date": "2025-01-15",
                "sourceType": "INDEX_SCALE",
            },
            {
                "samplePk": 12345679,
                "weight": 70300.0,
                "date": "2025-01-14",
                "sourceType": "INDEX_SCALE",
            },
        ]

        mock_client.get_daily_weigh_ins.return_value = {
            "samplePk": 12345678,
            "weight": 70500.0,
            "date": "2025-01-15",
        }

        mock_client.get_body_composition.return_value = {
            "weight": 70500.0,
            "bodyFat": 15.2,
            "muscleMass": 32100.0,
            "boneMass": 3200.0,
            "bodyWater": 55.5,
            "date": "2025-01-15",
        }

        mock_client.add_weigh_in.return_value = {"samplePk": 12345680}
        mock_client.delete_weigh_in.return_value = None
        mock_client.delete_weigh_ins.return_value = None

        yield mock_client
