"""CLI tests for garmin-connect-cli.

These tests exercise the CLI through its public interface (the command line).
We mock only at the HTTP boundary (garminconnect.Garmin).
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

from typer.testing import CliRunner

from garmin_connect_cli import __version__
from garmin_connect_cli.cli import app


class TestVersion:
    """Tests for version display."""

    def test_version_flag(self, cli_runner: CliRunner) -> None:
        """--version shows the version number."""
        result = cli_runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.stdout

    def test_version_short_flag(self, cli_runner: CliRunner) -> None:
        """-V shows the version number."""
        result = cli_runner.invoke(app, ["-V"])
        assert result.exit_code == 0
        assert __version__ in result.stdout


class TestHelp:
    """Tests for help output."""

    def test_help_shows_commands(self, cli_runner: CliRunner) -> None:
        """--help shows available commands."""
        result = cli_runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "activities" in result.stdout
        assert "athlete" in result.stdout
        assert "auth" in result.stdout
        assert "health" in result.stdout
        assert "context" in result.stdout

    def test_subcommand_help(self, cli_runner: CliRunner) -> None:
        """Subcommand --help shows subcommand options."""
        result = cli_runner.invoke(app, ["activities", "--help"])
        assert result.exit_code == 0
        assert "list" in result.stdout
        assert "get" in result.stdout
        assert "download" in result.stdout


class TestAuth:
    """Tests for authentication commands."""

    def test_status_shows_not_authenticated(
        self,
        cli_runner: CliRunner,
        unauthenticated_env: Path,
    ) -> None:
        """auth status shows not authenticated when no tokens exist."""
        result = cli_runner.invoke(app, ["auth", "status"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["authenticated"] is False

    def test_logout_clears_tokens(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """auth logout clears authentication tokens."""
        result = cli_runner.invoke(app, ["auth", "logout"])
        assert result.exit_code == 0
        assert "authenticated" in result.stdout
        assert "false" in result.stdout


class TestActivities:
    """Tests for activity commands."""

    def test_list_returns_activities(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """activities list returns activity data."""
        result = cli_runner.invoke(app, ["activities", "list"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["activityName"] == "Morning Run"

    def test_list_with_limit(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """activities list respects --limit option."""
        result = cli_runner.invoke(app, ["activities", "list", "--limit", "5"])
        assert result.exit_code == 0
        mock_garminconnect.get_activities.assert_called_once()
        call_kwargs = mock_garminconnect.get_activities.call_args
        assert call_kwargs.kwargs.get("limit") == 5

    def test_list_with_format_csv(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """activities list outputs CSV format."""
        result = cli_runner.invoke(app, ["--format", "csv", "activities", "list"])
        assert result.exit_code == 0
        lines = result.stdout.strip().split("\n")
        assert len(lines) >= 2  # Header + data
        assert "," in lines[0]

    def test_get_single_activity(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """activities get returns a single activity."""
        result = cli_runner.invoke(app, ["activities", "get", "123456789"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["activityId"] == 123456789
        assert data["activityName"] == "Morning Run"

    def test_get_activity_with_details(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """activities get --details returns detailed activity data."""
        result = cli_runner.invoke(app, ["activities", "get", "123456789", "--details"])
        assert result.exit_code == 0
        mock_garminconnect.get_activity_details.assert_called_once_with(123456789)

    def test_delete_activity_with_confirm(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """activities delete requires confirmation."""
        result = cli_runner.invoke(app, ["activities", "delete", "123456789"], input="y\n")
        assert result.exit_code == 0
        mock_garminconnect.delete_activity.assert_called_once_with(123456789)


class TestAthlete:
    """Tests for athlete commands."""

    def test_profile(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """athlete (without subcommand) returns user profile."""
        result = cli_runner.invoke(app, ["athlete"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["displayName"] == "testuser"

    def test_stats(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """athlete stats returns daily statistics."""
        result = cli_runner.invoke(app, ["athlete", "stats"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "totalSteps" in data

    def test_summary(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """athlete summary returns comprehensive stats."""
        result = cli_runner.invoke(app, ["athlete", "summary"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "totalSteps" in data


class TestHealth:
    """Tests for health commands."""

    def test_heart_rate(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """health heart-rate returns heart rate data."""
        result = cli_runner.invoke(app, ["health", "heart-rate"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["restingHeartRate"] == 55

    def test_sleep(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """health sleep returns sleep data."""
        result = cli_runner.invoke(app, ["health", "sleep"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "dailySleepDTO" in data

    def test_steps(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """health steps returns steps data."""
        result = cli_runner.invoke(app, ["health", "steps"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "totalSteps" in data

    def test_stress(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """health stress returns stress data."""
        result = cli_runner.invoke(app, ["health", "stress"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "overallStressLevel" in data

    def test_body_battery(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """health body-battery returns body battery data."""
        result = cli_runner.invoke(app, ["health", "body-battery"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert data[0]["bodyBatteryLevel"] == 75


class TestContext:
    """Tests for context command (LLM aggregation)."""

    def test_context_aggregates_data(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """context command aggregates user data."""
        result = cli_runner.invoke(app, ["context"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "profile" in data
        assert "today_stats" in data
        assert "health" in data
        assert "recent_activities" in data

    def test_context_with_activities_limit(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """context --activities limits recent activities."""
        result = cli_runner.invoke(app, ["context", "--activities", "10"])
        assert result.exit_code == 0
        mock_garminconnect.get_activities.assert_called_with(start=0, limit=10)

    def test_context_no_health(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """context --no-health excludes health data."""
        result = cli_runner.invoke(app, ["context", "--no-health"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "health" not in data


class TestOutputFormats:
    """Tests for different output formats."""

    def test_json_format(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """JSON format outputs valid JSON."""
        result = cli_runner.invoke(app, ["--format", "json", "activities", "list"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)

    def test_jsonl_format(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """JSONL format outputs one JSON object per line."""
        result = cli_runner.invoke(app, ["--format", "jsonl", "activities", "list"])
        assert result.exit_code == 0
        lines = result.stdout.strip().split("\n")
        for line in lines:
            if line:
                json.loads(line)

    def test_tsv_format(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """TSV format uses tab separators."""
        result = cli_runner.invoke(app, ["--format", "tsv", "activities", "list"])
        assert result.exit_code == 0
        assert "\t" in result.stdout

    def test_fields_filter(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """--fields filters output to specified fields."""
        result = cli_runner.invoke(
            app, ["--fields", "activityId,activityName", "activities", "list"]
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "activityId" in data[0]
        assert "activityName" in data[0]


class TestTraining:
    """Tests for training commands."""

    def test_status(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """training status returns training status data."""
        result = cli_runner.invoke(app, ["training", "status"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["trainingStatusPhrase"] == "PRODUCTIVE"

    def test_readiness(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """training readiness returns readiness score."""
        result = cli_runner.invoke(app, ["training", "readiness"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["readinessScore"] == 72

    def test_vo2max(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """training vo2max returns VO2 max estimates."""
        result = cli_runner.invoke(app, ["training", "vo2max"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "generic" in data
        assert data["generic"]["vo2MaxValue"] == 52.0

    def test_lactate(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """training lactate returns lactate threshold data."""
        result = cli_runner.invoke(app, ["training", "lactate"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["lactateThresholdHeartRateInBeatsPerMinute"] == 165

    def test_hrv(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """training hrv returns HRV data."""
        result = cli_runner.invoke(app, ["training", "hrv"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["hrvStatus"] == "BALANCED"

    def test_fitness_age(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """training fitness-age returns fitness age."""
        result = cli_runner.invoke(app, ["training", "fitness-age"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["fitnessAge"] == 32


class TestWeight:
    """Tests for weight commands."""

    def test_list(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """weight list returns weight entries."""
        result = cli_runner.invoke(app, ["weight", "list"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["weight"] == 70500.0

    def test_get(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """weight get returns weight for a date."""
        result = cli_runner.invoke(app, ["weight", "get"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["weight"] == 70500.0

    def test_body_comp(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """weight body-comp returns body composition data."""
        result = cli_runner.invoke(app, ["weight", "body-comp"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["bodyFat"] == 15.2
        assert data["muscleMass"] == 32100.0

    def test_log(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """weight log adds a weight entry."""
        result = cli_runner.invoke(app, ["weight", "log", "70.5"])
        assert result.exit_code == 0
        mock_garminconnect.add_weigh_in.assert_called_once()

    def test_delete_with_confirm(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """weight delete requires confirmation."""
        result = cli_runner.invoke(app, ["weight", "delete", "12345678"], input="y\n")
        assert result.exit_code == 0
        mock_garminconnect.delete_weigh_in.assert_called_once_with(12345678)


class TestMutationDualOutput:
    """Tests for mutation command dual output (human vs machine formats)."""

    def test_delete_activity_human_format(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """delete activity with human format shows human message."""
        result = cli_runner.invoke(
            app,
            ["--format", "human", "activities", "delete", "123456789", "--force"],
        )
        assert result.exit_code == 0
        assert "deleted" in result.stdout.lower()
        assert "123456789" in result.stdout

    def test_delete_activity_json_format(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """delete activity with JSON format outputs structured data."""
        result = cli_runner.invoke(
            app,
            ["--format", "json", "activities", "delete", "123456789", "--force"],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["activity_id"] == 123456789

    def test_log_weight_human_format(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """log weight with human format shows human message."""
        result = cli_runner.invoke(
            app,
            ["--format", "human", "weight", "log", "70.5"],
        )
        assert result.exit_code == 0
        assert "70.5" in result.stdout
        assert "logged" in result.stdout.lower()

    def test_delete_weight_human_format(
        self,
        cli_runner: CliRunner,
        authenticated_env: Path,
        mock_garminconnect: MagicMock,
    ) -> None:
        """delete weight with human format shows human message."""
        result = cli_runner.invoke(
            app,
            ["--format", "human", "weight", "delete", "12345678", "--force"],
        )
        assert result.exit_code == 0
        assert "deleted" in result.stdout.lower()
