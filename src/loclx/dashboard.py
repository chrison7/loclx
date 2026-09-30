"""Live terminal dashboard renderer for LOCLX v2.1.0."""

from __future__ import annotations

import shutil
from typing import Optional

from loclx import VERSION
from loclx.gps import format_accuracy
from loclx.sessions import Session
from loclx.utils import Ansi, format_distance, format_uptime


class TerminalDashboard:
    """Renders formatted terminal dashboard for LOCLX sessions."""

    def __init__(self, ansi: Optional[Ansi] = None) -> None:
        self.c = ansi or Ansi(True)

    def render_banner(self) -> str:
        banner_art = r"""
╔════════════════════════════════════════════════════════════╗
║                         LOCLX                              ║
║          Live Location & Information eXtractor             ║
║                         v2.1.0                             ║
╚════════════════════════════════════════════════════════════╝"""
        return self.c.green(banner_art)

    def render_session_dashboard(self, session: Session) -> str:
        data = session.to_dict()
        c = self.c
        width = min(max(shutil.get_terminal_size().columns - 2, 58), 80)
        inner = width - 4

        def line(text: str = "") -> str:
            val = text[:inner]
            return "║ " + val.ljust(inner) + " ║"

        top_border = "╔" + "═" * (width - 2) + "╗"
        div_border = "╠" + "═" * (width - 2) + "╣"
        bot_border = "╚" + "═" * (width - 2) + "╝"

        lines = [
            c.green(top_border),
            c.bold(c.cyan(line(f"LOCLX LIVE — SESSION {data['id']}"))),
            c.green(div_border),
            line(f"STATUS       {data['status']:<12} CREATED  {data['created']}"),
            line(f"AGE          {format_uptime(data['uptimeSeconds']):<12} UPDATES  {data['gpsUpdates']}"),
            c.green(div_border),
            c.bold(c.green(line("GPS LOCATION"))),
        ]

        fix = data.get("currentFix")
        if fix:
            lat = fix.get("lat")
            lon = fix.get("lon")
            lat_s = f"{lat:.6f}" if lat is not None else "n/a"
            lon_s = f"{lon:.6f}" if lon is not None else "n/a"
            lines.extend([
                line(f"Latitude     {lat_s}"),
                line(f"Longitude    {lon_s}"),
                line(f"Accuracy     {format_accuracy(fix.get('accuracy'))}"),
                line(f"Altitude     {fix.get('altitude') or 'n/a'}"),
                line(f"Last update  {fix.get('timestamp') or 'n/a'}"),
            ])
        else:
            lines.append(c.amber(line("Waiting for browser location permission...")))

        lines.extend([
            c.green(div_border),
            c.bold(c.cyan(line("NETWORK GEOLOCATION — APPROXIMATE"))),
        ])

        ip = data.get("ipInfo")
        if ip:
            lines.extend([
                line(f"Public IP    {ip.get('ip') or '—'}"),
                line(f"Country      {ip.get('country') or '—'}"),
                line(f"Region       {ip.get('region') or '—'}"),
                line(f"City         {ip.get('city') or '—'}"),
                line(f"ISP          {ip.get('isp') or '—'}"),
                line(f"ASN          {ip.get('asn') or '—'}"),
            ])
        else:
            lines.append(c.dim(line("IP intelligence lookup pending...")))

        diff = data.get("diffMeters")
        if diff is not None:
            lines.extend([
                c.green(div_border),
                c.bold(c.amber(line("IP VS GPS DISCREPANCY"))),
                line(f"Distance     {format_distance(diff)}"),
                c.dim(line("(IP location is approximate; GPS requires explicit click)")),
            ])

        lines.extend([
            c.green(div_border),
            c.bold(c.amber(line("BROWSER INFORMATION"))),
        ])

        b = data.get("browserInfo")
        if b:
            lines.extend([
                line(f"Browser      {b.get('browser') or '—'} {b.get('browserVersion') or ''}"),
                line(f"Platform     {b.get('platform') or '—'} ({b.get('deviceType') or 'Desktop'})"),
                line(f"Screen       {b.get('screenResolution') or '—'}"),
                line(f"CPU cores    {b.get('cpuCores') or '—'}"),
                line(f"Timezone     {b.get('timezone') or '—'}"),
            ])
        else:
            lines.append(c.dim(line("Browser information pending...")))

        lines.append(c.green(bot_border))
        return "\n".join(lines)
