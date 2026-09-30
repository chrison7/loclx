"""Live terminal dashboard renderer for LOCLX."""

from __future__ import annotations

import time
from typing import Optional

from loclx.gps import format_accuracy
from loclx.sessions import Session
from loclx.utils import Ansi, format_distance, format_uptime


class TerminalDashboard:
    """Renders formatted terminal dashboard for LOCLX sessions."""

    def __init__(self, ansi: Optional[Ansi] = None) -> None:
        self.c = ansi or Ansi(True)

    def render_banner(self) -> str:
        banner_art = r"""
 ╔══════════════════════════════════════════════╗
 ║                 LOCLX                        ║
 ║      Live Location & Information eXtractor   ║
 ║                 v2.0                         ║
 ╚══════════════════════════════════════════════╝"""
        return self.c.green(banner_art)

    def render_session_dashboard(self, session: Session) -> str:
        data = session.to_dict()
        c = self.c

        lines = [
            c.bold(c.cyan("LOCLX LIVE SESSION")),
            c.dim("─" * 44),
            f"{c.dim('Session'):<14} {c.bold(data['id'])}",
            f"{c.dim('Status'):<14} {c.green(data['status']) if data['status'] == 'ACTIVE' else c.amber(data['status'])}",
            f"{c.dim('Duration'):<14} {format_uptime(data['uptimeSeconds'])}",
            "",
            c.bold(c.green("GPS")),
            c.dim("─" * 44),
        ]

        fix = data.get("currentFix")
        if fix:
            lat = fix.get("lat")
            lon = fix.get("lon")
            lat_s = f"{lat:.6f}" if lat is not None else "n/a"
            lon_s = f"{lon:.6f}" if lon is not None else "n/a"
            lines.extend([
                f"{c.dim('Latitude'):<14} {lat_s}",
                f"{c.dim('Longitude'):<14} {lon_s}",
                f"{c.dim('Accuracy'):<14} {format_accuracy(fix.get('accuracy'))}",
                f"{c.dim('Altitude'):<14} {fix.get('altitude') or 'n/a'}",
                f"{c.dim('Updates'):<14} {data['gpsUpdates']}",
                f"{c.dim('Last update'):<14} {fix.get('timestamp') or 'n/a'}",
            ])
        else:
            lines.append(c.amber("Waiting for location permission & GPS fix..."))

        lines.extend([
            "",
            c.bold(c.cyan("NETWORK (APPROXIMATE)")),
            c.dim("─" * 44),
        ])

        ip = data.get("ipInfo")
        if ip:
            lines.extend([
                f"{c.dim('Public IP'):<14} {ip.get('ip') or '—'}",
                f"{c.dim('Country'):<14} {ip.get('country') or '—'}",
                f"{c.dim('Region'):<14} {ip.get('region') or '—'}",
                f"{c.dim('City'):<14} {ip.get('city') or '—'}",
                f"{c.dim('ISP'):<14} {ip.get('isp') or '—'}",
                f"{c.dim('ASN'):<14} {ip.get('asn') or '—'}",
            ])
        else:
            lines.append(c.dim("IP information pending..."))

        diff = data.get("diffMeters")
        if diff is not None:
            lines.extend([
                "",
                c.bold(c.amber("IP VS GPS DISCREPANCY")),
                c.dim("─" * 44),
                c.amber(f"IP estimate was off by {format_distance(diff)} from browser GPS."),
                c.dim("(IP geolocation is approximate; browser GPS requires explicit permission)"),
            ])

        lines.extend([
            "",
            c.bold(c.amber("BROWSER")),
            c.dim("─" * 44),
        ])

        b = data.get("browserInfo")
        if b:
            lines.extend([
                f"{c.dim('Browser'):<14} {b.get('browser') or '—'}",
                f"{c.dim('Platform'):<14} {b.get('platform') or '—'}",
                f"{c.dim('Screen'):<14} {b.get('screenResolution') or '—'}",
                f"{c.dim('CPU cores'):<14} {b.get('cpuCores') or '—'}",
                f"{c.dim('Timezone'):<14} {b.get('timezone') or '—'}",
            ])
        else:
            lines.append(c.dim("Browser information pending..."))

        return "\n".join(lines)
