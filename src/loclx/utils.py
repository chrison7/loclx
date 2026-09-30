"""Utility functions and formatting helpers for LOCLX."""

from __future__ import annotations

import os
import sys
import threading
from typing import Any


def configure_stdio() -> None:
    """Configure stdout and stderr streams for UTF-8 output."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass


def use_color() -> bool:
    """Determine whether ANSI color output should be enabled."""
    return sys.stdout.isatty() and not os.environ.get("NO_COLOR")


class Ansi:
    """ANSI color code helper."""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled

    def wrap(self, code: str, text: str) -> str:
        if not self.enabled:
            return text
        return f"\033[{code}m{text}\033[0m"

    def green(self, text: str) -> str:
        return self.wrap("32", text)

    def cyan(self, text: str) -> str:
        return self.wrap("36", text)

    def amber(self, text: str) -> str:
        return self.wrap("33", text)

    def red(self, text: str) -> str:
        return self.wrap("31", text)

    def dim(self, text: str) -> str:
        return self.wrap("2", text)

    def bold(self, text: str) -> str:
        return self.wrap("1", text)


_print_lock = threading.Lock()


def emit(*parts: str, end: str = "\n") -> None:
    """Thread-safe stdout write helper."""
    text = "".join(parts) + end
    with _print_lock:
        try:
            sys.stdout.write(text)
        except UnicodeEncodeError:
            sys.stdout.write(text.encode("utf-8", "replace").decode("ascii", "replace"))
        sys.stdout.flush()


def format_distance(meters: float) -> str:
    """Format distance in meters or kilometers."""
    if meters < 1000:
        if meters < 10:
            return f"{meters:.1f} m"
        return f"{meters:.0f} m"
    return f"{meters / 1000.0:.1f} km"


def format_uptime(seconds: float) -> str:
    """Format uptime in hours, minutes, and seconds."""
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"
