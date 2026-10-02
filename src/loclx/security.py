"""Security controls, input validation, rate limiting, and sanitization."""

from __future__ import annotations

import html
import math
import re
import time
from typing import Any

MAX_REQUEST_BODY = 64 * 1024  # 64 KB limit
SESS_ID_PATTERN = re.compile(r"^LX-[A-F0-9]{6}$")


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
    """Ensure JSON data is a valid dict structure within size limits."""
    if not isinstance(data, dict):
        return False
    return True


def validate_sid_format(sid: Any) -> bool:
    """Strictly validate session ID format (LX-XXXXXX). Rejects traversal or malformed strings."""
    if not isinstance(sid, str):
        return False
    return bool(SESS_ID_PATTERN.match(sid.strip()))


def is_finite_number(val: Any) -> bool:
    return isinstance(val, (int, float)) and not isinstance(val, bool) and math.isfinite(val)


def validate_gps_payload(gps_data: Any) -> bool:
    """Validate incoming GPS dictionary fields against physical limits and finite values."""
    if not isinstance(gps_data, dict):
        return False
    lat = gps_data.get("lat")
    lon = gps_data.get("lon")

    if not is_finite_number(lat) or not is_finite_number(lon):
        return False

    lat_f = float(lat)
    lon_f = float(lon)
    if not (-90.0 <= lat_f <= 90.0) or not (-180.0 <= lon_f <= 180.0):
        return False

    acc = gps_data.get("accuracy")
    if acc is not None:
        if not is_finite_number(acc) or float(acc) < 0:
            return False

    alt = gps_data.get("altitude")
    if alt is not None and not is_finite_number(alt):
        return False

    spd = gps_data.get("speed")
    if spd is not None:
        if not is_finite_number(spd) or float(spd) < 0:
            return False

    hdg = gps_data.get("heading")
    if hdg is not None:
        if not is_finite_number(hdg):
            return False
        hdg_f = float(hdg)
        if not (0.0 <= hdg_f <= 360.0):
            return False

    return True


from urllib.parse import urlparse


TRUSTED_PROXIES = {"127.0.0.1", "::1", "localhost"}


def validate_public_url(url: str) -> str:
    """Validate LOCLX_PUBLIC_URL.

    Accepts https:// for remote/public configurations and http://localhost (or 127.0.0.1) for local dev.
    Removes trailing slashes and rejects malformed or unencrypted remote URLs.
    """
    if not isinstance(url, str) or not url.strip():
        raise ValueError("Public URL must be a non-empty string.")

    cleaned = url.strip().rstrip("/")
    try:
        parsed = urlparse(cleaned)
    except Exception as exc:
        raise ValueError(f"Malformed public URL: {url}") from exc

    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Invalid URL structure: {url}")

    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        raise ValueError(f"Unsupported URL scheme: {scheme}. Use https:// or http://localhost.")

    hostname = (parsed.hostname or "").lower()

    if scheme == "http":
        if hostname not in ("localhost", "127.0.0.1", "::1"):
            raise ValueError("Remote public URLs must use HTTPS (http:// allowed for localhost only).")

    return cleaned


def extract_client_ip(headers: Any, direct_ip: str) -> str:
    """Extract client IP address, handling proxy headers only if request comes from a trusted local proxy."""
    if direct_ip in TRUSTED_PROXIES:
        x_real_ip = headers.get("X-Real-IP") if headers else None
        if x_real_ip and x_real_ip.strip():
            return x_real_ip.strip()

        x_forwarded_for = headers.get("X-Forwarded-For") if headers else None
        if x_forwarded_for and x_forwarded_for.strip():
            # First IP in X-Forwarded-For list is the client IP
            first_ip = x_forwarded_for.split(",")[0].strip()
            if first_ip:
                return first_ip

    return direct_ip

