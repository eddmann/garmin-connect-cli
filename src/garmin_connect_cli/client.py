"""Garmin Connect client wrapper with token management."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

import typer
from garminconnect import Garmin

from garmin_connect_cli.config import Config, get_token_dir

if TYPE_CHECKING:
    from collections.abc import Callable


class GarminClient:
    """Wrapper around garminconnect.Garmin with token management."""

    def __init__(self, config: Config, profile: str | None = None):
        """Initialize the Garmin client.

        Args:
            config: Application configuration
            profile: Optional profile name for multi-account support
        """
        self.config = config
        self.profile = profile
        self.token_dir = get_token_dir(profile)
        self._client: Garmin | None = None

    @property
    def client(self) -> Garmin:
        """Get or create the Garmin client."""
        if self._client is None:
            self._client = Garmin()
        return self._client

    def is_authenticated(self) -> bool:
        """Check if we have stored tokens."""
        # Garth stores oauth2_token.json in the token directory
        token_file = self.token_dir / "oauth2_token.json"
        return token_file.exists()

    def ensure_authenticated(self) -> None:
        """Ensure we have valid authentication, loading tokens if available."""
        if not self.is_authenticated():
            print(
                "error: Not authenticated. Run 'garmin-connect auth login' first.",
                file=sys.stderr,
            )
            raise typer.Exit(2)

        try:
            # Create client and load tokens from tokenstore
            self._client = Garmin()
            self._client.login(str(self.token_dir))
        except Exception as e:
            print(f"error: Authentication failed: {e}", file=sys.stderr)
            print(
                "Try running 'garmin-connect auth login' to re-authenticate.",
                file=sys.stderr,
            )
            raise typer.Exit(2) from None

    def login(
        self,
        email: str,
        password: str,
        mfa_callback: Callable[[], str] | None = None,
    ) -> bool:
        """Perform login with email/password.

        Args:
            email: Garmin account email
            password: Garmin account password
            mfa_callback: Optional callback for MFA code input

        Returns:
            True if login successful
        """
        try:
            # Ensure token directory exists
            self.token_dir.mkdir(parents=True, exist_ok=True)

            # Initialize client with credentials
            self._client = Garmin(email, password)

            # Attempt login
            self._client.login()

            # Save tokens using Garth
            self._client.garth.dump(str(self.token_dir))
            return True

        except Exception as e:
            error_str = str(e).lower()

            # Check for MFA requirement
            if "mfa" in error_str or "verification" in error_str:
                if mfa_callback is None:
                    print("error: MFA required but no callback provided", file=sys.stderr)
                    return False

                try:
                    mfa_code = mfa_callback()
                    # Reinitialize with MFA handling
                    self._client = Garmin(email, password)
                    self._client.login(mfa_code)
                    self._client.garth.dump(str(self.token_dir))
                    return True
                except Exception as mfa_e:
                    print(f"error: MFA authentication failed: {mfa_e}", file=sys.stderr)
                    return False

            print(f"error: Login failed: {e}", file=sys.stderr)
            return False

    def logout(self) -> None:
        """Clear stored tokens."""
        import shutil

        if self.token_dir.exists():
            shutil.rmtree(self.token_dir)

    # Profile methods
    def get_full_name(self) -> str:
        """Get user's full name."""
        self.ensure_authenticated()
        return self.client.get_full_name()

    def get_user_profile(self) -> dict[str, Any]:
        """Get user profile."""
        self.ensure_authenticated()
        return self.client.get_user_profile()

    def get_unit_system(self) -> dict[str, Any]:
        """Get user's unit system preference."""
        self.ensure_authenticated()
        return self.client.get_unit_system()

    # Activity methods
    def get_activities(self, start: int = 0, limit: int = 30) -> list[dict[str, Any]]:
        """Get activities with pagination.

        Args:
            start: Starting index
            limit: Maximum number of activities

        Returns:
            List of activity dictionaries
        """
        self.ensure_authenticated()
        return self.client.get_activities(start=start, limit=limit)

    def get_activities_by_date(
        self,
        start_date: str,
        end_date: str,
        activity_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get activities within a date range.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            activity_type: Optional activity type filter

        Returns:
            List of activity dictionaries
        """
        self.ensure_authenticated()
        return self.client.get_activities_by_date(
            startdate=start_date,
            enddate=end_date,
            activitytype=activity_type,
        )

    def get_activity(self, activity_id: int) -> dict[str, Any]:
        """Get a single activity by ID."""
        self.ensure_authenticated()
        return self.client.get_activity(activity_id)

    def get_activity_details(self, activity_id: int) -> dict[str, Any]:
        """Get detailed activity data including metrics."""
        self.ensure_authenticated()
        return self.client.get_activity_details(activity_id)

    def get_activity_splits(self, activity_id: int) -> dict[str, Any]:
        """Get activity splits/laps."""
        self.ensure_authenticated()
        return self.client.get_activity_splits(activity_id)

    def download_activity(self, activity_id: int, dl_fmt: str = "TCX") -> bytes:
        """Download activity in specified format.

        Args:
            activity_id: Activity ID
            dl_fmt: Download format (TCX, GPX, ORIGINAL, CSV)

        Returns:
            Activity data as bytes
        """
        self.ensure_authenticated()
        fmt_map = {
            "TCX": Garmin.ActivityDownloadFormat.TCX,
            "GPX": Garmin.ActivityDownloadFormat.GPX,
            "ORIGINAL": Garmin.ActivityDownloadFormat.ORIGINAL,
            "CSV": Garmin.ActivityDownloadFormat.CSV,
        }
        fmt = fmt_map.get(dl_fmt.upper(), Garmin.ActivityDownloadFormat.TCX)
        return self.client.download_activity(activity_id, dl_fmt=fmt)

    def upload_activity(self, file_path: str) -> dict[str, Any]:
        """Upload an activity file.

        Args:
            file_path: Path to activity file (FIT, GPX, TCX)

        Returns:
            Upload response
        """
        self.ensure_authenticated()
        return self.client.upload_activity(file_path)

    def delete_activity(self, activity_id: int) -> None:
        """Delete an activity."""
        self.ensure_authenticated()
        self.client.delete_activity(activity_id)

    # Stats methods
    def get_stats(self, date_str: str) -> dict[str, Any]:
        """Get daily stats.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Stats dictionary
        """
        self.ensure_authenticated()
        return self.client.get_stats(date_str)

    def get_user_summary(self, date_str: str) -> dict[str, Any]:
        """Get user summary for a date.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Summary dictionary
        """
        self.ensure_authenticated()
        return self.client.get_user_summary(date_str)

    def get_stats_and_body(self, date_str: str) -> dict[str, Any]:
        """Get comprehensive daily stats and body metrics.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Combined stats and body data
        """
        self.ensure_authenticated()
        return self.client.get_stats_and_body(date_str)

    # Health methods
    def get_sleep_data(self, date_str: str) -> dict[str, Any]:
        """Get sleep data for a date.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Sleep data dictionary
        """
        self.ensure_authenticated()
        return self.client.get_sleep_data(date_str)

    def get_heart_rates(self, date_str: str) -> dict[str, Any]:
        """Get heart rate data for a date.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Heart rate data dictionary
        """
        self.ensure_authenticated()
        return self.client.get_heart_rates(date_str)

    def get_steps_data(self, date_str: str) -> dict[str, Any]:
        """Get steps data for a date.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Steps data dictionary
        """
        self.ensure_authenticated()
        return self.client.get_steps_data(date_str)

    def get_rhr_day(self, date_str: str) -> dict[str, Any]:
        """Get resting heart rate for a date.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            RHR data dictionary
        """
        self.ensure_authenticated()
        return self.client.get_rhr_day(date_str)

    def get_stress_data(self, date_str: str) -> dict[str, Any]:
        """Get stress data for a date.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Stress data dictionary
        """
        self.ensure_authenticated()
        return self.client.get_stress_data(date_str)

    def get_body_battery(self, date_str: str) -> list[dict[str, Any]]:
        """Get body battery data for a date.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Body battery data list
        """
        self.ensure_authenticated()
        return self.client.get_body_battery(date_str)

    # Training metrics methods
    def get_training_status(self, date_str: str) -> dict[str, Any]:
        """Get training status for a date.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Training status data
        """
        self.ensure_authenticated()
        return self.client.get_training_status(date_str)

    def get_training_readiness(self, date_str: str) -> dict[str, Any]:
        """Get training readiness for a date.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Training readiness data
        """
        self.ensure_authenticated()
        return self.client.get_training_readiness(date_str)

    def get_max_metrics(self, date_str: str) -> dict[str, Any]:
        """Get max metrics (VO2 max) for a date.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Max metrics data including VO2 max
        """
        self.ensure_authenticated()
        return self.client.get_max_metrics(date_str)

    def get_lactate_threshold(self) -> dict[str, Any]:
        """Get lactate threshold data.

        Returns:
            Lactate threshold data (HR, pace, power)
        """
        self.ensure_authenticated()
        return self.client.get_lactate_threshold()

    def get_endurance_score(self, date_str: str) -> dict[str, Any]:
        """Get endurance score for a date.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Endurance score data
        """
        self.ensure_authenticated()
        return self.client.get_endurance_score(date_str)

    def get_hill_score(self, date_str: str) -> dict[str, Any]:
        """Get hill score for a date.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Hill score data
        """
        self.ensure_authenticated()
        return self.client.get_hill_score(date_str)

    def get_hrv_data(self, date_str: str) -> dict[str, Any]:
        """Get HRV data for a date.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            HRV data
        """
        self.ensure_authenticated()
        return self.client.get_hrv_data(date_str)

    def get_fitnessage_data(self) -> dict[str, Any]:
        """Get fitness age data.

        Returns:
            Fitness age data
        """
        self.ensure_authenticated()
        return self.client.get_fitnessage_data()

    # Weight and body composition methods
    def get_weigh_ins(self, start_date: str, end_date: str) -> list[dict[str, Any]]:
        """Get weight entries between dates.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            List of weight entries
        """
        self.ensure_authenticated()
        return self.client.get_weigh_ins(start_date, end_date)

    def get_daily_weigh_ins(self, date_str: str) -> dict[str, Any]:
        """Get weight for a specific date.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Weight data for the date
        """
        self.ensure_authenticated()
        return self.client.get_daily_weigh_ins(date_str)

    def get_body_composition(self, date_str: str) -> dict[str, Any]:
        """Get body composition data for a date.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Body composition data (fat %, muscle, bone, water)
        """
        self.ensure_authenticated()
        return self.client.get_body_composition(date_str)

    def add_weigh_in(
        self, weight: float, unitKey: str = "kg", date: str | None = None
    ) -> dict[str, Any]:
        """Add a weight entry.

        Args:
            weight: Weight value
            unitKey: Unit (kg or lb)
            date: Date in YYYY-MM-DD format

        Returns:
            Result of the operation
        """
        self.ensure_authenticated()
        return self.client.add_weigh_in(weight=weight, unitKey=unitKey, date=date)

    def delete_weigh_in(self, pk: int) -> None:
        """Delete a weight entry by primary key.

        Args:
            pk: Weight entry primary key
        """
        self.ensure_authenticated()
        self.client.delete_weigh_in(pk)

    def delete_weigh_ins(self, date_str: str) -> None:
        """Delete all weight entries for a date.

        Args:
            date_str: Date in YYYY-MM-DD format
        """
        self.ensure_authenticated()
        self.client.delete_weigh_ins(date_str)


def get_client(config: Config | None = None, profile: str | None = None) -> GarminClient:
    """Get a configured Garmin client.

    Args:
        config: Optional config, loads default if not provided
        profile: Optional profile name

    Returns:
        Configured GarminClient
    """
    if config is None:
        config = Config.load()
    return GarminClient(config, profile)
