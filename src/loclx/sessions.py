"""Session management, lifecycle tracking, and session isolation."""

from __future__ import annotations

import os
import secrets
import time
from typing import Any, Optional

from loclx.browser import BrowserInfo
from loclx.gps import haversine_m
from loclx.storage import SessionStorage

DEFAULT_SESSION_TTL = 1800.0


def get_default_ttl() -> float:
    try:
        val = float(os.environ.get("LOCLX_SESSION_TTL", DEFAULT_SESSION_TTL))
        return val if val > 0 else DEFAULT_SESSION_TTL
    except Exception:
        return DEFAULT_SESSION_TTL


class Session:
    """Represents a single LOCLX lab session."""

    def __init__(self, sid: str, timeout_seconds: Optional[float] = None) -> None:
        self.sid = sid
        self.created_at = time.time()
        self.timeout_seconds = timeout_seconds if timeout_seconds is not None else get_default_ttl()
        self.expires_at = self.created_at + self.timeout_seconds
        self.last_activity = self.created_at
        self.first_seen: Optional[float] = None
        self.last_seen: Optional[float] = None
        self.client_ip: str = "—"
        self.connected: bool = False
        self.status = "ACTIVE"
        self.gps_updates = 0
        self.current_fix: Optional[dict[str, Any]] = None
        self.ip_info: Optional[dict[str, Any]] = None
        self.browser_info: Optional[BrowserInfo] = None
        self.storage = SessionStorage()

    def touch(self) -> None:
        now = time.time()
        self.last_activity = now
        self.last_seen = now
        if self.first_seen is None:
            self.first_seen = now
        self.expires_at = now + self.timeout_seconds

    def mark_connected(self, ip: str) -> None:
        now = time.time()
        self.connected = True
        self.client_ip = ip
        if self.first_seen is None:
            self.first_seen = now
        self.touch()

    def is_expired(self) -> bool:
        if self.status == "EXPIRED":
            return True
        if time.time() > self.expires_at or time.time() - self.last_activity > self.timeout_seconds:
            self.status = "EXPIRED"
            return True
        return False

    def update_gps(self, gps_data: dict[str, Any]) -> None:
        if self.is_expired() or self.status == "STOPPED":
            return
        self.touch()
        self.gps_updates += 1
        self.current_fix = {
            "lat": float(gps_data["lat"]),
            "lon": float(gps_data["lon"]),
            "accuracy": float(gps_data["accuracy"]) if gps_data.get("accuracy") is not None else None,
            "altitude": float(gps_data["altitude"]) if gps_data.get("altitude") is not None else None,
            "heading": float(gps_data["heading"]) if gps_data.get("heading") is not None else None,
            "speed": float(gps_data["speed"]) if gps_data.get("speed") is not None else None,
            "timestamp": time.strftime("%H:%M:%S"),
        }
        self.storage.add_record(self.current_fix)

    def set_ip_info(self, ip_data: dict[str, Any]) -> None:
        self.touch()
        self.ip_info = ip_data

    def set_browser_info(self, browser_data: dict[str, Any]) -> None:
        self.touch()
        self.browser_info = BrowserInfo.from_dict(browser_data)

    def calculate_ip_gps_diff(self) -> Optional[float]:
        if not self.ip_info or not self.current_fix:
            return None
        ip_lat = self.ip_info.get("lat")
        ip_lon = self.ip_info.get("lon")
        gps_lat = self.current_fix.get("lat")
        gps_lon = self.current_fix.get("lon")
        if ip_lat is None or ip_lon is None or gps_lat is None or gps_lon is None:
            return None
        return haversine_m(float(ip_lat), float(ip_lon), float(gps_lat), float(gps_lon))

    def stop(self) -> None:
        self.status = "STOPPED"
        self.touch()

    def to_dict(self) -> dict[str, Any]:
        uptime = time.time() - self.created_at
        first_s = time.strftime("%H:%M:%S", time.localtime(self.first_seen)) if self.first_seen else "—"
        last_s = time.strftime("%H:%M:%S", time.localtime(self.last_seen)) if self.last_seen else "—"
        return {
            "id": self.sid,
            "status": self.status,
            "connected": self.connected,
            "client_ip": self.client_ip,
            "created": time.strftime("%H:%M:%S", time.localtime(self.created_at)),
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "first_seen": first_s,
            "last_seen": last_s,
            "lastActivity": time.strftime("%H:%M:%S", time.localtime(self.last_activity)),
            "gpsUpdates": self.gps_updates,
            "update_count": self.gps_updates,
            "currentFix": self.current_fix,
            "gps_fix": self.current_fix,
            "ipInfo": self.ip_info,
            "ip_information": self.ip_info,
            "browserInfo": self.browser_info.to_dict() if self.browser_info else None,
            "browser_information": self.browser_info.to_dict() if self.browser_info else None,
            "diffMeters": self.calculate_ip_gps_diff(),
            "uptimeSeconds": uptime,
        }


class SessionManager:
    """Manages active, expired, and stopped LOCLX sessions."""

    def __init__(self, default_timeout: Optional[float] = None) -> None:
        self.default_timeout = default_timeout if default_timeout is not None else get_default_ttl()
        self.sessions: dict[str, Session] = {}

    def create_session(self) -> Session:
        sid = f"LX-{secrets.token_hex(3).upper()}"
        session = Session(sid, timeout_seconds=self.default_timeout)
        self.sessions[sid] = session
        return session

    def get_session(self, sid: str) -> Optional[Session]:
        session = self.sessions.get(sid)
        if not session:
            return None
        if session.is_expired():
            return None
        return session

    def list_sessions(self) -> list[Session]:
        active = []
        for session in list(self.sessions.values()):
            if not session.is_expired():
                active.append(session)
        return active

    def stop_session(self, sid: str) -> bool:
        session = self.sessions.get(sid)
        if session:
            session.stop()
            return True
        return False

    def delete_session(self, sid: str) -> bool:
        if sid in self.sessions:
            del self.sessions[sid]
            return True
        return False
