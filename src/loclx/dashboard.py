"""Live terminal dashboard renderer and target report generator for LOCLX v2.3.0."""

from __future__ import annotations

import shutil
from typing import Optional

from loclx import VERSION
from loclx.gps import calculate_bearing, format_accuracy, generate_map_urls
from loclx.sessions import Session
from loclx.utils import Ansi, format_distance, format_uptime


class TerminalDashboard:
    """Renders formatted terminal dashboard and target report for LOCLX sessions."""

    def __init__(self, ansi: Optional[Ansi] = None) -> None:
        self.c = ansi or Ansi(True)

    def render_banner(self) -> str:
        banner_art = r"""
╔════════════════════════════════════════════════════════════╗
║                         LOCLX                              ║
║     LIVE LOCATION & INFORMATION eXTRACTOR                  ║
║                         v2.3.0                             ║
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
            lat_s = f"{lat:.9f}" if lat is not None else "n/a"
            lon_s = f"{lon:.9f}" if lon is not None else "n/a"
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

    def render_session_info(self, session: Session) -> str:
        d = session.to_dict()
        c = self.c
        sep = c.dim("────────────────────────────")

        fix = d.get("currentFix") or {}
        ip = d.get("ipInfo") or {}
        b = d.get("browserInfo") or {}

        status_str = d['status']
        if session.status == "ACTIVE" and not session.connected:
            status_str = "WAITING"

        lat_val = f"{fix['lat']:.9f}" if fix.get("lat") is not None else "—"
        lon_val = f"{fix['lon']:.9f}" if fix.get("lon") is not None else "—"
        acc_val = format_accuracy(fix.get("accuracy")) if fix.get("accuracy") is not None else "—"
        alt_val = str(fix.get("altitude")) if fix.get("altitude") is not None else "—"
        spd_val = f"{fix['speed']:.1f} m/s" if fix.get("speed") is not None else "—"
        hdg_val = f"{fix['heading']:.0f}°" if fix.get("heading") is not None else "—"

        lines = [
            c.bold(c.cyan("SESSION")),
            sep,
            f"{'ID':<12}: {d['id']}",
            f"{'STATUS':<12}: {status_str}",
            f"{'CREATED':<12}: {d['created']}",
            f"{'EXPIRES':<12}: {time_str_from_ts(d['expires_at'])}",
            f"{'FIRST SEEN':<12}: {d.get('first_seen') or '—'}",
            f"{'LAST SEEN':<12}: {d.get('last_seen') or '—'}",
            f"{'CLIENT IP':<12}: {d.get('client_ip') or '—'}",
            f"{'CONNECTED':<12}: {'YES' if d.get('connected') else 'NO'}",
            f"{'GPS UPDATES':<12}: {d['gpsUpdates']}",
            "",
            c.bold(c.cyan("GPS")),
            sep,
            f"{'Latitude':<12}: {lat_val}",
            f"{'Longitude':<12}: {lon_val}",
            f"{'Accuracy':<12}: {acc_val}",
            f"{'Altitude':<12}: {alt_val}",
            f"{'Speed':<12}: {spd_val}",
            f"{'Heading':<12}: {hdg_val}",
            "",
            c.bold(c.cyan("NETWORK")),
            sep,
            f"{'Public IP':<12}: {ip.get('ip') or '—'}",
            f"{'Country':<12}: {ip.get('country') or '—'}",
            f"{'Region':<12}: {ip.get('region') or '—'}",
            f"{'City':<12}: {ip.get('city') or '—'}",
            f"{'ISP':<12}: {ip.get('isp') or '—'}",
            f"{'ASN':<12}: {ip.get('asn') or '—'}",
            "",
            c.bold(c.cyan("BROWSER")),
            sep,
            f"{'Browser':<12}: {b.get('browser') or '—'}",
            f"{'Version':<12}: {b.get('browserVersion') or '—'}",
            f"{'Platform':<12}: {b.get('platform') or '—'}",
            f"{'Screen':<12}: {b.get('screenResolution') or '—'}",
            f"{'CPU':<12}: {b.get('cpuCores') or '—'}",
            f"{'Timezone':<12}: {b.get('timezone') or '—'}",
            f"{'Language':<12}: {b.get('language') or '—'}",
        ]
        return "\n".join(lines)

    def render_live_session(self, session: Session) -> str:
        d = session.to_dict()
        c = self.c
        width = 54
        inner = width - 4

        def line(text: str = "") -> str:
            val = text[:inner]
            return "║ " + val.ljust(inner) + " ║"

        status_label = "● ACTIVE" if session.connected else "○ WAITING"
        if session.status == "STOPPED":
            status_label = "■ STOPPED"
        elif session.is_expired():
            status_label = "× EXPIRED"

        top_border = "╔" + "═" * (width - 2) + "╗"
        div_border = "╠" + "═" * (width - 2) + "╣"
        bot_border = "╚" + "═" * (width - 2) + "╝"

        fix = d.get("currentFix") or {}
        ip = d.get("ipInfo") or {}

        lat_s = f"{fix.get('lat'):.9f}" if fix.get("lat") is not None else "—"
        lon_s = f"{fix.get('lon'):.9f}" if fix.get("lon") is not None else "—"
        acc_s = f"±{fix.get('accuracy'):.0f} m" if fix.get("accuracy") is not None else "—"

        lines = [
            c.green(top_border),
            c.bold(c.cyan(line("LOCLX LIVE SESSION"))),
            c.green(div_border),
            line(f"Session    {d['id']:<16} {status_label}"),
            line(f"Age        {format_uptime(d['uptimeSeconds'])}"),
            c.green(div_border),
            c.bold(c.green(line("GPS"))),
            line(f"Latitude   {lat_s}"),
            line(f"Longitude  {lon_s}"),
            line(f"Accuracy   {acc_s}"),
            line(f"Updates    {d['gpsUpdates']}"),
            c.green(div_border),
            c.bold(c.cyan(line("NETWORK — APPROXIMATE"))),
            line(f"IP         {ip.get('ip') or '—'}"),
            line(f"City       {ip.get('city') or '—'}"),
            line(f"ISP        {ip.get('isp') or '—'}"),
            line(f"ASN        {ip.get('asn') or '—'}"),
            c.green(bot_border),
        ]
        return "\n".join(lines)


def time_str_from_ts(ts: float) -> str:
    import time
    return time.strftime("%H:%M:%S", time.localtime(ts))



def generate_target_report(session: Session, c: Optional[Ansi] = None) -> str:
    """Generate a comprehensive Hound-style target intelligence report."""
    ansi = c or Ansi(True)
    d = session.to_dict()

    sep = ansi.dim("──────────────────────────────────────────────")
    header_sep = ansi.green("══════════════════════════════════════════════")

    lines = [
        ansi.bold(ansi.cyan("LOCLX — TARGET INFORMATION")),
        header_sep,
        "",
        ansi.bold(ansi.cyan("SESSION")),
        sep,
        f"{'ID':<16}: {d['id']}",
        f"{'STATUS':<16}: {d['status']}",
        f"{'FIRST SEEN':<16}: {d.get('first_seen') or '—'}",
        f"{'LAST SEEN':<16}: {d.get('last_seen') or '—'}",
        f"{'UPDATES':<16}: {d['gpsUpdates']}",
        "",
        ansi.bold(ansi.cyan("DEVICE / BROWSER")),
        sep,
    ]

    b = d.get("browserInfo") or {}
    lines.extend([
        f"{'Browser':<16}: {b.get('browser') or '—'}",
        f"{'Browser Version':<16}: {b.get('browserVersion') or '—'}",
        f"{'Platform':<16}: {b.get('platform') or '—'}",
        f"{'User Agent':<16}: {b.get('userAgent') or '—'}",
        f"{'Language':<16}: {b.get('language') or '—'}",
        f"{'Timezone':<16}: {b.get('timezone') or '—'}",
        f"{'Screen':<16}: {b.get('screenResolution') or '—'}",
        f"{'Viewport':<16}: {b.get('viewportSize') or '—'}",
        f"{'CPU Cores':<16}: {b.get('cpuCores') or '—'}",
        f"{'DPR':<16}: {b.get('devicePixelRatio') or '1'}",
        f"{'Touch':<16}: {b.get('touchSupport') or '—'}",
        f"{'Device Type':<16}: {b.get('deviceType') or 'Desktop'}",
        "",
        ansi.bold(ansi.cyan("NETWORK")),
        sep,
    ])

    ip = d.get("ipInfo") or {}
    lines.extend([
        f"{'Public IP':<16}: {ip.get('ip') or '—'}",
        f"{'Country':<16}: {ip.get('country') or '—'}",
        f"{'Region':<16}: {ip.get('region') or '—'}",
        f"{'City':<16}: {ip.get('city') or '—'}",
        f"{'ISP':<16}: {ip.get('isp') or '—'}",
        f"{'Organization':<16}: {ip.get('org') or '—'}",
        f"{'ASN':<16}: {ip.get('asn') or '—'}",
        f"{'Reverse DNS':<16}: {ip.get('hostname') or '—'}",
        "",
        ansi.bold(ansi.cyan("IP LOCATION")),
        sep,
        f"{'Latitude':<16}: {ip.get('lat') if ip.get('lat') is not None else '—'}",
        f"{'Longitude':<16}: {ip.get('lon') if ip.get('lon') is not None else '—'}",
        f"{'Precision':<16}: APPROXIMATE",
        "",
        ansi.bold(ansi.green("GPS LOCATION")),
        sep,
    ])

    best_fix = d.get("bestFix") or d.get("best_fix") or d.get("currentFix") or {}
    if best_fix:
        lines.extend([
            f"{'Source':<16}: Browser Geolocation",
            f"{'Latitude':<16}: {best_fix.get('lat'):.9f}",
            f"{'Longitude':<16}: {best_fix.get('lon'):.9f}",
            f"{'Accuracy':<16}: {format_accuracy(best_fix.get('accuracy'))}",
            f"{'Altitude':<16}: {best_fix.get('altitude') or 'n/a'}",
            f"{'Speed':<16}: {best_fix.get('speed') or 0:.1f} m/s",
            f"{'Heading':<16}: {best_fix.get('heading') or 0:.0f}°",
            f"{'Timestamp':<16}: {best_fix.get('timestamp') or '—'}",
        ])
    else:
        lines.append(ansi.amber("Waiting for location permission grant..."))

    lines.extend([
        "",
        ansi.bold(ansi.cyan("MAP LINKS")),
        sep,
    ])

    if best_fix and "lat" in best_fix and "lon" in best_fix:
        lat = best_fix["lat"]
        lon = best_fix["lon"]
        urls = generate_map_urls(lat, lon)
        lines.extend([
            f"{'Google Maps':<16}: {urls['google_maps']}",
            f"{'Google Earth':<16}: {urls['google_earth']}",
            f"{'OpenStreetMap':<16}: {urls['openstreetmap']}",
            f"{'GeoURI':<16}: {urls['geouri']}",
        ])
    else:
        lines.append("GPS Fix: None available yet.")


    lines.extend([
        "",
        ansi.bold(ansi.amber("ANALYSIS")),
        sep,
    ])

    diff = d.get("diffMeters")
    if diff is not None:
        bearing_str = ""
        if ip and "lat" in ip and "lon" in ip and best_fix and "lat" in best_fix and "lon" in best_fix:
            deg, cardinal = calculate_bearing(float(ip["lat"]), float(ip["lon"]), float(best_fix["lat"]), float(best_fix["lon"]))

            bearing_str = f" (Bearing: {deg:.0f}° {cardinal})"
        lines.append(f"{'GPS → IP':<16}: {format_distance(diff)}{bearing_str}")
    else:
        lines.append(f"{'GPS → IP':<16}: —")
    lines.append(f"{'GPS precision':<16}: BROWSER REPORTED")
    lines.append(f"{'IP precision':<16}: APPROXIMATE")
    lines.append(header_sep)

    return "\n".join(lines)


def generate_compact_information_report(session: Session, c: Optional[Ansi] = None) -> str:
    """Generate compact Hound-style LOCLX Information Report."""
    ansi = c or Ansi(True)
    d = session.to_dict()

    sep = ansi.dim("----------------------------------------")
    header_sep = ansi.cyan("========================================================")

    b = d.get("browserInfo") or {}
    ip = d.get("ipInfo") or {}
    fix = d.get("bestFix") or d.get("currentFix") or {}

    lat_s = f"{fix.get('lat'):.9f}" if fix.get("lat") is not None else "—"
    lon_s = f"{fix.get('lon'):.9f}" if fix.get("lon") is not None else "—"
    acc_s = format_accuracy(fix.get("accuracy")) if fix.get("accuracy") is not None else "—"
    alt_s = str(fix.get("altitude")) if fix.get("altitude") is not None else "n/a"
    spd_s = f"{fix['speed']:.1f} m/s" if fix.get("speed") is not None else "n/a"
    hdg_s = f"{fix['heading']:.0f}°" if fix.get("heading") is not None else "n/a"

    lines = [
        header_sep,
        ansi.bold(ansi.cyan("              LOCLX INFORMATION REPORT")),
        header_sep,
        "",
        ansi.bold(ansi.cyan("DEVICE INFORMATION")),
        sep,
        f"{'User Agent':<20}: {b.get('userAgent') or '—'}",
        f"{'Platform':<20}: {b.get('platform') or '—'}",
        f"{'Browser':<20}: {b.get('browser') or '—'}",
        f"{'Browser Version':<20}: {b.get('browserVersion') or '—'}",
        f"{'Language':<20}: {b.get('language') or '—'}",
        f"{'Timezone':<20}: {b.get('timezone') or '—'}",
        f"{'Screen':<20}: {b.get('screenResolution') or '—'}",
        f"{'Viewport':<20}: {b.get('viewportSize') or '—'}",
        f"{'CPU Cores':<20}: {b.get('cpuCores') or '—'}",
        f"{'Device Pixel Ratio':<20}: {b.get('devicePixelRatio') or '1'}",
        f"{'Touch Support':<20}: {b.get('touchSupport') or '—'}",
        "",
        ansi.bold(ansi.green("GPS LOCATION")),
        sep,
        f"{'Latitude':<20}: {lat_s}",
        f"{'Longitude':<20}: {lon_s}",
        f"{'Accuracy':<20}: {acc_s}",
        f"{'Altitude':<20}: {alt_s}",
        f"{'Speed':<20}: {spd_s}",
        f"{'Heading':<20}: {hdg_s}",
        f"{'Timestamp':<20}: {fix.get('timestamp') or '—'}",
        "",
        ansi.bold(ansi.cyan("TARGET NETWORK")),
        sep,
        f"{'IP':<20}: {ip.get('ip') or d.get('client_ip') or '—'}",
        "",
        ansi.bold(ansi.cyan("IP LOCATION")),
        sep,
        f"{'Country':<20}: {ip.get('country') or '—'}",
        f"{'Region':<20}: {ip.get('region') or '—'}",
        f"{'City':<20}: {ip.get('city') or '—'}",
        f"{'Latitude':<20}: {ip.get('lat') if ip.get('lat') is not None else '—'}",
        f"{'Longitude':<20}: {ip.get('lon') if ip.get('lon') is not None else '—'}",
        f"{'Precision':<20}: APPROXIMATE",
        "",
        ansi.bold(ansi.amber("LOCATION ANALYSIS")),
        sep,
    ]

    diff = d.get("diffMeters")
    if diff is not None:
        lines.append(f"{'GPS → IP Distance':<20}: {format_distance(diff)}")
    else:
        lines.append(f"{'GPS → IP Distance':<20}: —")
    lines.append(f"{'GPS Precision':<20}: BROWSER REPORTED")
    lines.append(f"{'IP Precision':<20}: APPROXIMATE")

    lines.extend([
        "",
        ansi.bold(ansi.cyan("MAP LINKS")),
        sep,
    ])

    if fix and "lat" in fix and "lon" in fix:
        lat = fix["lat"]
        lon = fix["lon"]
        lat_lon_9 = f"{lat:.9f},{lon:.9f}"
        lat_6 = f"{lat:.6f}"
        lon_6 = f"{lon:.6f}"
        lines.extend([
            f"{'Google Maps':<20}: https://www.google.com/maps?q={lat_lon_9}",
            f"{'Google Earth':<20}: https://earth.google.com/web/search/{lat_lon_9}",
            f"{'OpenStreetMap':<20}: https://www.openstreetmap.org/?mlat={lat_6}&mlon={lon_6}",
        ])
    else:
        lines.append("GPS Fix: None available yet.")

    lines.append(header_sep)
    return "\n".join(lines)

