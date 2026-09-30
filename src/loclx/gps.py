"""GPS coordinate processing, Haversine calculations, and formatting."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class GPSFix:
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    altitude: Optional[float] = None
    timestamp: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.latitude,
            "lon": self.longitude,
            "accuracy": self.accuracy,
            "altitude": self.altitude,
            "timestamp": self.timestamp or datetime.now().strftime("%H:%M:%S"),
        }


def is_valid_number(val: Any) -> bool:
    return isinstance(val, (int, float)) and not isinstance(val, bool) and math.isfinite(val)


def validate_coordinates(lat: Any, lon: Any) -> bool:
    if not is_valid_number(lat) or not is_valid_number(lon):
        return False
    return -90.0 <= float(lat) <= 90.0 and -180.0 <= float(lon) <= 180.0


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Haversine distance between two coordinates in meters."""
    radius = 6371000.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def format_accuracy(acc: Any) -> str:
    if not is_valid_number(acc):
        return "n/a"
    val = float(acc)
    if val == int(val):
        return f"±{int(val)} m"
    return f"±{val:.1f} m"


def format_altitude(alt: Any) -> str:
    if not is_valid_number(alt):
        return "n/a"
    val = float(alt)
    if val == int(val):
        return f"{int(val)} m"
    return f"{val:.1f} m"


def gps_box_lines(gps_data: dict[str, Any], when: Optional[str] = None) -> list[str]:
    lat = gps_data.get("lat")
    lon = gps_data.get("lon")
    lat_s = f"{float(lat):.6f}" if is_valid_number(lat) else "n/a"
    lon_s = f"{float(lon):.6f}" if is_valid_number(lon) else "n/a"
    rows = [
        ("latitude", lat_s),
        ("longitude", lon_s),
        ("accuracy", format_accuracy(gps_data.get("accuracy"))),
        ("altitude", format_altitude(gps_data.get("altitude"))),
        ("time", when or gps_data.get("timestamp") or "n/a"),
    ]
    inner = 41
    title = " GPS FIX "
    top_fill = inner - 1 - len(title)
    top = "╭─" + title + ("─" * max(0, top_fill)) + "╮"
    bottom = "╰" + ("─" * inner) + "╯"
    lines = [top]
    for key, val in rows:
        body = f" {key:<10}{val}"
        body = body[:inner].ljust(inner)
        lines.append("│" + body + "│")
    lines.append(bottom)
    return lines
