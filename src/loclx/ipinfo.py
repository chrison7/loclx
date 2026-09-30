"""IP Intelligence provider abstraction and lookup implementations."""

from __future__ import annotations

import json
import urllib.request
from abc import ABC, abstractmethod
from typing import Any, Optional


class IPProvider(ABC):
    """Abstract base class for IP intelligence providers."""

    @abstractmethod
    def name(self) -> str:
        """Name of the provider."""
        pass

    @abstractmethod
    def lookup(self, timeout: float = 5.0) -> Optional[dict[str, Any]]:
        """Perform IP lookup and return normalized dictionary or None."""
        pass


class IPWhoIsProvider(IPProvider):
    """ipwho.is IP geolocation provider."""

    def name(self) -> str:
        return "ipwho.is"

    def lookup(self, timeout: float = 5.0) -> Optional[dict[str, Any]]:
        url = "https://ipwho.is/"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "LOCLX-SecurityLab/2.1"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status != 200:
                    return None
                data = json.loads(response.read().decode("utf-8"))
                if not data or data.get("success") is False:
                    return None
                conn = data.get("connection", {})
                timezone = data.get("timezone", {})
                lat = data.get("latitude")
                lon = data.get("longitude")
                return {
                    "ip": data.get("ip"),
                    "city": data.get("city"),
                    "region": data.get("region"),
                    "country": data.get("country"),
                    "postal": data.get("postal") or "—",
                    "timezone": timezone.get("id") or timezone.get("code") or "—",
                    "isp": conn.get("isp") or data.get("isp") or conn.get("org") or "—",
                    "org": conn.get("org") or data.get("org") or "—",
                    "asn": str(conn.get("asn") or data.get("asn") or "—"),
                    "hostname": conn.get("domain") or "—",
                    "lat": float(lat) if isinstance(lat, (int, float)) else None,
                    "lon": float(lon) if isinstance(lon, (int, float)) else None,
                    "provider": self.name(),
                    "precision": "APPROXIMATE",
                }
        except Exception:
            return None


class IPApiProvider(IPProvider):
    """ipapi.co IP geolocation provider (fallback)."""

    def name(self) -> str:
        return "ipapi.co"

    def lookup(self, timeout: float = 5.0) -> Optional[dict[str, Any]]:
        url = "https://ipapi.co/json/"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "LOCLX-SecurityLab/2.1"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status != 200:
                    return None
                data = json.loads(response.read().decode("utf-8"))
                if not data or "error" in data:
                    return None
                lat = data.get("latitude")
                lon = data.get("longitude")
                return {
                    "ip": data.get("ip"),
                    "city": data.get("city"),
                    "region": data.get("region"),
                    "country": data.get("country_name") or data.get("country"),
                    "postal": data.get("postal") or "—",
                    "timezone": data.get("timezone") or "—",
                    "isp": data.get("org") or data.get("isp") or "—",
                    "org": data.get("org") or "—",
                    "asn": str(data.get("asn") or "—"),
                    "hostname": data.get("hostname") or "—",
                    "lat": float(lat) if isinstance(lat, (int, float)) else None,
                    "lon": float(lon) if isinstance(lon, (int, float)) else None,
                    "provider": self.name(),
                    "precision": "APPROXIMATE",
                }
        except Exception:
            return None


class IPManager:
    """Registry and manager for IP providers."""

    def __init__(self) -> None:
        self.providers: list[IPProvider] = [
            IPWhoIsProvider(),
            IPApiProvider(),
        ]

    def add_provider(self, provider: IPProvider) -> None:
        self.providers.append(provider)

    def fetch_ip_info(self, timeout: float = 5.0) -> Optional[dict[str, Any]]:
        for provider in self.providers:
            info = provider.lookup(timeout=timeout)
            if info:
                return info
        return None
