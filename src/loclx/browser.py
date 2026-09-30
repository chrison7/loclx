"""Browser information model and data parsing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BrowserInfo:
    user_agent: str = "Unknown"
    browser: str = "Unknown"
    browser_version: str = "Unknown"
    platform: str = "Unknown"
    screen_resolution: str = "Unknown"
    device_pixel_ratio: str = "1"
    cpu_cores: str = "Unknown"
    language: str = "Unknown"
    timezone: str = "Unknown"
    timezone_offset: str = "Unknown"
    viewport_size: str = "Unknown"
    color_depth: str = "Unknown"
    touch_capability: str = "Unknown"
    online_status: str = "Online"
    device_type: str = "Desktop"
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BrowserInfo:
        if not isinstance(data, dict):
            return cls()

        ua = str(data.get("userAgent") or data.get("user_agent") or "Unknown")
        browser_name, browser_ver = cls._parse_ua_browser(ua, data.get("browser"))
        is_mobile = any(m in ua.lower() for m in ["mobile", "android", "iphone", "ipad", "ipod"])

        return cls(
            user_agent=ua,
            browser=browser_name,
            browser_version=browser_ver,
            platform=str(data.get("platform") or "Unknown"),
            screen_resolution=str(data.get("screenResolution") or data.get("screen") or "Unknown"),
            device_pixel_ratio=str(data.get("devicePixelRatio") or data.get("dpr") or "1"),
            cpu_cores=str(data.get("hardwareConcurrency") or data.get("cpu_cores") or "Unknown"),
            language=str(data.get("language") or "Unknown"),
            timezone=str(data.get("timezone") or "Unknown"),
            timezone_offset=str(data.get("timezoneOffset") or "Unknown"),
            viewport_size=str(data.get("viewportSize") or data.get("viewport") or "Unknown"),
            color_depth=str(data.get("colorDepth") or "Unknown"),
            touch_capability=str(data.get("touchSupport") or data.get("touch") or "Unknown"),
            online_status=str(data.get("onlineStatus") or data.get("online") or "Online"),
            device_type="Mobile" if is_mobile else "Desktop",
            extra=data,
        )

    @staticmethod
    def _parse_ua_browser(ua: str, override_browser: Any = None) -> tuple[str, str]:
        if override_browser and override_browser != "Unknown":
            return str(override_browser), "Unknown"
        ua_lower = ua.lower()
        if "firefox/" in ua_lower:
            parts = ua.split("Firefox/")
            ver = parts[1].split()[0] if len(parts) > 1 else "Unknown"
            return "Firefox", ver
        elif "edg/" in ua_lower:
            parts = ua.split("Edg/")
            ver = parts[1].split()[0] if len(parts) > 1 else "Unknown"
            return "Edge", ver
        elif "chrome/" in ua_lower:
            parts = ua.split("Chrome/")
            ver = parts[1].split()[0] if len(parts) > 1 else "Unknown"
            return "Chrome", ver
        elif "safari/" in ua_lower and "version/" in ua_lower:
            parts = ua.split("Version/")
            ver = parts[1].split()[0] if len(parts) > 1 else "Unknown"
            return "Safari", ver
        return "Unknown", "Unknown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "userAgent": self.user_agent,
            "browser": self.browser,
            "browserVersion": self.browser_version,
            "platform": self.platform,
            "screenResolution": self.screen_resolution,
            "devicePixelRatio": self.device_pixel_ratio,
            "cpuCores": self.cpu_cores,
            "language": self.language,
            "timezone": self.timezone,
            "timezoneOffset": self.timezone_offset,
            "viewportSize": self.viewport_size,
            "colorDepth": self.color_depth,
            "touchSupport": self.touch_capability,
            "onlineStatus": self.online_status,
            "deviceType": self.device_type,
        }
