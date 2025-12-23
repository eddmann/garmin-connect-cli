"""Authentication commands."""

from __future__ import annotations

from typing import Annotated

import typer

from garmin_connect_cli.client import get_client
from garmin_connect_cli.config import Config, get_config_path, get_credentials, get_token_dir
from garmin_connect_cli.core import emit
from garmin_connect_cli.output import OutputFormat

app = typer.Typer(no_args_is_help=True)


@app.command("login")
def login(
    email: Annotated[
        str | None,
        typer.Option(
            "--email",
            "-e",
            help="Garmin account email (or set GARMIN_EMAIL env var)",
        ),
    ] = None,
    password: Annotated[
        str | None,
        typer.Option(
            "--password",
            "-p",
            help="Garmin account password (or set GARMIN_PASSWORD env var)",
            hide_input=True,
        ),
    ] = None,
    profile: Annotated[
        str | None,
        typer.Option(
            "--profile",
            help="Profile name for multi-account support",
        ),
    ] = None,
) -> None:
    """Authenticate with Garmin Connect.

    Logs in with email/password and stores OAuth tokens for future use.
    Tokens are valid for approximately one year.

    Examples:
        garmin-connect auth login --email user@example.com
        garmin-connect auth login  # Uses GARMIN_EMAIL/GARMIN_PASSWORD env vars
    """
    # Get credentials from args or environment
    env_email, env_password = get_credentials()
    final_email = email or env_email
    final_password = password or env_password

    if not final_email:
        final_email = typer.prompt("Email")
    if not final_password:
        final_password = typer.prompt("Password", hide_input=True)

    config = Config.load()
    client = get_client(config, profile)

    def mfa_callback() -> str:
        return typer.prompt("Enter MFA code")

    success = client.login(final_email, final_password, mfa_callback)

    if not success:
        raise typer.Exit(2)

    # Optionally save email to profile config
    if profile:
        from garmin_connect_cli.config import ProfileConfig

        config.profiles[profile] = ProfileConfig(email=final_email)
        config.save()

    # Output result
    try:
        full_name = client.get_full_name()
    except Exception:
        full_name = None

    output_data = {
        "authenticated": True,
        "full_name": full_name,
        "email": final_email,
        "token_dir": str(get_token_dir(profile)),
    }
    emit(output_data)


@app.command("logout")
def logout(
    profile: Annotated[
        str | None,
        typer.Option(
            "--profile",
            help="Profile to log out",
        ),
    ] = None,
) -> None:
    """Log out and clear stored tokens.

    Examples:
        garmin-connect auth logout
        garmin-connect auth logout --profile work
    """
    config = Config.load()
    client = get_client(config, profile)

    client.logout()

    emit({"authenticated": False})


@app.command("status")
def status(
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = OutputFormat.json,
    profile: Annotated[
        str | None,
        typer.Option(
            "--profile",
            help="Profile to check",
        ),
    ] = None,
) -> None:
    """Show current authentication status.

    Examples:
        garmin-connect auth status
        garmin-connect auth status --format human
    """
    from garmin_connect_cli.output import output

    config = Config.load()
    client = get_client(config, profile)

    data = {
        "authenticated": client.is_authenticated(),
        "token_dir": str(get_token_dir(profile)),
        "config_path": str(get_config_path()),
    }

    if client.is_authenticated():
        try:
            client.ensure_authenticated()
            data["full_name"] = client.get_full_name()
        except typer.Exit:
            data["authenticated"] = False
            data["error"] = "Tokens expired or invalid"

    # Use explicit format since this command has its own --format option
    output(data, format=format)
