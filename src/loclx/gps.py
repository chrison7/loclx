"""GPS coordinate processing, Haversine calculations, accuracy visualization, and formatting."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class GPSFix:
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    altitude: Optional[float] = None
    heading: Optional[float] = None
    speed: Optional[float] = None
    timestamp: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.latitude,
            "lon": self.longitude,
            "accuracy": self.accuracy,
            "altitude": self.altitude,
            "heading": self.heading,
            "speed": self.speed,
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


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> tuple[float, str]:
    """Calculate compass bearing (0-360 deg) and cardinal direction from (lat1, lon1) to (lat2, lon2)."""
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dlmb = math.radians(lon2 - lon1)
    x = math.sin(dlmb) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dlmb)
    bearing = (math.degrees(math.atan2(x, y)) + 360.0) % 360.0
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "N"]
    idx = int((bearing + 22.5) / 45.0) % 8
    return bearing, dirs[idx]


def generate_map_urls(lat: float, lon: float) -> dict[str, str]:
    """Generate mapping URLs for GPS coordinates."""
    lat_lon_9 = f"{lat:.9f},{lon:.9f}"
    lat_6 = f"{lat:.6f}"
    lon_6 = f"{lon:.6f}"
    return {
        "google_maps": f"https://www.google.com/maps?q={lat_lon_9}",
        "google_earth": f"https://earth.google.com/web/search/{lat_lon_9}",
        "openstreetmap": f"https://www.openstreetmap.org/?mlat={lat_6}&mlon={lon_6}",
        "geouri": f"geo:{lat_6},{lon_6}?z=16",
    }



def format_accuracy(acc: Any) -> str:
    if not is_valid_number(acc):
        return "n/a"
    val = float(acc)
    if val >= 1000:
        km = val / 1000.0
        if km == int(km):
            return f"±{int(km)} km"
        return f"±{km:.1f} km"
    if val == int(val):
        return f"±{int(val)} m"
    return f"±{val:.1f} m"



def classify_gps_quality(acc: Any) -> str:
    """Classify GPS accuracy into HIGH, GOOD, MODERATE, LOW, or COARSE quality levels."""
    if not is_valid_number(acc):
        return "UNKNOWN"
    val = float(acc)
    if val <= 25.0:
        return "HIGH"
    elif val <= 100.0:
        return "GOOD"
    elif val <= 1000.0:
        return "MODERATE"
    elif val <= 10000.0:
        return "LOW"
    else:
        return "COARSE"


def format_altitude(alt: Any) -> str:
    if not is_valid_number(alt):
        return "n/a"
    val = float(alt)
    if val == int(val):
        return f"{int(val)} m"
    return f"{val:.1f} m"


def render_accuracy_target(acc: Any) -> str:
    """Render an ASCII target accuracy diagram."""
    acc_str = format_accuracy(acc)
    return (
        f"  GPS ACCURACY TARGET\n"
        f"        {acc_str}\n"
        f"         ●\n"
        f"       (   )\n"
        f"      (     )"
    )


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
        ("heading", f"{gps_data.get('heading'):.1f}°" if is_valid_number(gps_data.get("heading")) else "n/a"),
        ("speed", f"{gps_data.get('speed'):.1f} m/s" if is_valid_number(gps_data.get("speed")) else "n/a"),
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
