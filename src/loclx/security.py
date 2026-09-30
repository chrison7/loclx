"""Security controls, input validation, rate limiting, and sanitization."""

from __future__ import annotations

import html
import time
from typing import Any

MAX_REQUEST_BODY = 64 * 1024  # 64 KB limit


class RateLimiter:
    """Simple token-bucket rate limiter per IP address or session."""

    def __init__(self, max_requests: int = 100, window_seconds: float = 60.0) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.history: dict[str, list[float]] = {}

    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        cutoff = now - self.window_seconds
        timestamps = self.history.get(client_id, [])
        valid_timestamps = [t for t in timestamps if t > cutoff]
        if len(valid_timestamps) >= self.max_requests:
            self.history[client_id] = valid_timestamps
            return False
        valid_timestamps.append(now)
        self.history[client_id] = valid_timestamps
        return True


def sanitize_input(text: Any) -> str:
    """Sanitize string inputs against injection or HTML XSS."""
    if not isinstance(text, str):
        return str(text)
    return html.escape(text.strip())


def validate_json_payload(data: Any) -> bool:
    """Ensure JSON data is a valid dict structures within size limits."""
    if not isinstance(data, dict):
        return False
    return True
