"""Browser information model and data parsing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class BrowserInfo:
    user_agent: str = "Unknown"
    browser: str = "Unknown"
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
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BrowserInfo:
        if not isinstance(data, dict):
            return cls()
        return cls(
            user_agent=str(data.get("userAgent") or data.get("user_agent") or "Unknown"),
            browser=str(data.get("browser") or "Unknown"),
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
            extra=data,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "userAgent": self.user_agent,
            "browser": self.browser,
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
        }
