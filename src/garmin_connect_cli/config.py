"""Configuration management with XDG-compliant paths."""

from __future__ import annotations

import os
import stat
import sys
from dataclasses import dataclass, field
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


# XDG Base Directory Specification
def get_config_dir() -> Path:
    """Get XDG config directory."""
    if xdg := os.environ.get("XDG_CONFIG_HOME"):
        return Path(xdg) / "garmin-connect-cli"
    return Path.home() / ".config" / "garmin-connect-cli"


def get_config_path() -> Path:
    """Get default config file path."""
    return get_config_dir() / "config.toml"


def get_token_dir(profile: str | None = None) -> Path:
    """Get Garth token directory path.

    Tokens are stored in the config directory for XDG compliance.
    For multi-profile support, we use subdirectories.

    Args:
        profile: Optional profile name for multi-account support

    Returns:
        Path to token directory
    """
    base = get_config_dir() / "tokens"
    if profile:
        return base / profile
    return base


@dataclass
class DefaultsConfig:
    """Default settings."""

    format: str = "json"
    limit: int = 30


@dataclass
class ProfileConfig:
    """Profile-specific settings."""

    email: str | None = None


@dataclass
class Config:
    """Main configuration.

    Note: Auth tokens are managed by Garth and stored in ~/.config/garmin-connect-cli/tokens/.
    We only store CLI preferences in config.toml.
    """

    defaults: DefaultsConfig = field(default_factory=DefaultsConfig)
    profiles: dict[str, ProfileConfig] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path | str | None = None) -> Config:
        """Load configuration from file and environment variables."""
        config = cls()

        # Load from file if it exists
        config_path = Path(path) if path is not None else get_config_path()

        if config_path.exists():
            config = cls._load_from_file(config_path)

        # Environment variable overrides
        config._apply_env_overrides()

        return config

    @classmethod
    def _load_from_file(cls, path: Path) -> Config:
        """Load configuration from TOML file."""
        with open(path, "rb") as f:
            data = tomllib.load(f)

        config = cls()

        # Parse defaults section
        if defaults_data := data.get("defaults"):
            config.defaults = DefaultsConfig(
                format=defaults_data.get("format", "json"),
                limit=defaults_data.get("limit", 30),
            )

        # Parse profiles
        if profiles_data := data.get("profiles"):
            for name, profile_data in profiles_data.items():
                config.profiles[name] = ProfileConfig(
                    email=profile_data.get("email"),
                )

        return config

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides."""
        if fmt := os.environ.get("GARMIN_FORMAT"):
            self.defaults.format = fmt

    def save(self, path: Path | str | None = None) -> None:
        """Save configuration to TOML file."""
        config_path = Path(path) if path is not None else get_config_path()

        config_path.parent.mkdir(parents=True, exist_ok=True)
        # Set directory permissions to owner-only (0o700) for security
        config_path.parent.chmod(stat.S_IRWXU)

        # Build TOML content
        lines = []

        # Defaults section
        lines.append("[defaults]")
        lines.append(f'format = "{self.defaults.format}"')
        lines.append(f"limit = {self.defaults.limit}")
        lines.append("")

        # Profiles
        for name, profile in self.profiles.items():
            lines.append(f"[profiles.{name}]")
            if profile.email:
                lines.append(f'email = "{profile.email}"')
            lines.append("")

        config_path.write_text("\n".join(lines))
        # Set file permissions to owner read/write only (0o600)
        config_path.chmod(stat.S_IRUSR | stat.S_IWUSR)

    def get_profile(self, name: str | None) -> ProfileConfig | None:
        """Get profile config by name."""
        if name and name in self.profiles:
            return self.profiles[name]
        return None


def get_credentials() -> tuple[str | None, str | None]:
    """Get email and password from environment."""
    email = os.environ.get("GARMIN_EMAIL")
    password = os.environ.get("GARMIN_PASSWORD")
    return email, password
