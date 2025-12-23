"""Core utilities for CLI commands - decorators and helpers."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from garmin_connect_cli.output import OutputFormat

R = TypeVar("R")


class State:
    """Global CLI state."""

    format: OutputFormat = OutputFormat.json
    fields: list[str] | None = None
    no_header: bool = False
    verbose: bool = False
    quiet: bool = False
    config_path: str | None = None
    profile: str | None = None


state = State()


def with_client(func: Callable[..., R]) -> Callable[..., R]:
    """Decorator that injects an authenticated GarminClient as first argument.

    Usage:
        @app.command("list")
        @with_client
        def list_activities(client: GarminClient, limit: int = 30) -> None:
            activities = client.get_activities(limit=limit)
            emit(activities)
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> R:
        from garmin_connect_cli.client import get_client
        from garmin_connect_cli.config import Config

        config = Config.load(state.config_path)
        client = get_client(config, state.profile)
        return func(client, *args, **kwargs)

    # Typer inspects __signature__ for CLI args - modify to hide 'client' param
    sig = inspect.signature(func)
    params = list(sig.parameters.values())[1:]  # Skip 'client' param
    wrapper.__signature__ = sig.replace(parameters=params)  # type: ignore[attr-defined]

    return wrapper


def emit(data: Any) -> None:
    """Output data using current global format settings."""
    from garmin_connect_cli.output import output

    output(
        data,
        format=state.format,
        fields=state.fields,
        no_header=state.no_header,
    )


def emit_result(data: Any, human_msg: str) -> None:
    """Emit mutation result using global output settings.

    For human format: prints human_msg only.
    For machine formats: outputs full structured data.
    """
    from garmin_connect_cli.output import emit_result as _emit_result

    _emit_result(
        data,
        human_msg,
        format=state.format,
        fields=state.fields,
        no_header=state.no_header,
    )
