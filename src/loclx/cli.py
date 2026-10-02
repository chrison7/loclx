"""Terminal-first Hound-style CLI for LOCLX."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import time
from typing import Any, Optional

from loclx import VERSION
from loclx.dashboard import TerminalDashboard, generate_compact_information_report, generate_target_report
from loclx.diagnostics import DiagnosticRunner
from loclx.ipinfo import IPManager
from loclx.qrcode import generate_ascii_qr
from loclx.security import validate_public_url, validate_sid_format
from loclx.server import BIND_ADDR, DEFAULT_PORT, get_active_session, get_session_manager, shutdown_server, start_server_background
from loclx.tunnel import stop_cloudflare_tunnel
from loclx.utils import Ansi, configure_stdio, emit, format_distance, format_uptime, use_color


def build_session_url(public_base: str, sid: str) -> str:
    """Construct a clean, normalized public session capture URL."""
    if not validate_sid_format(sid):
        raise ValueError(f"Invalid session ID format: {sid}")
    validated_base = validate_public_url(public_base)
    return f"{validated_base}/session/{sid}"


def print_banner(c: Ansi) -> None:
    banner = f"""
========================================================
                     LOCLX
              Location Intelligence
                      v{VERSION}
========================================================

LOCLX - Authorized Security Testing Tool"""
    emit(c.bold(c.cyan(banner)))


def run_lab_mode(c: Ansi) -> None:
    emit(c.bold(c.cyan("\n[★] LOCLX SECURITY LAB MODE")))
    emit("  1. IP Geolocation is based on network routing databases and provides an APPROXIMATE estimate.")
    emit("  2. Precise GPS coordinates are retrieved ONLY via the browser Geolocation API after EXPLICIT permission.")
    emit("  3. All coordinates and session data remain on localhost (127.0.0.1) and are held in memory.")
    emit("  4. Outbound network activity is logged live on the lab page for inspection.\n")


def run_diagnostics_cmd(c: Ansi, port: int = DEFAULT_PORT) -> None:
    runner = DiagnosticRunner(port=port)
    results = runner.run_all()

    emit(c.bold(c.cyan("\nLOCLX DIAGNOSTICS")))
    emit(c.dim("────────────────────────────────────────────────────────────"))

    for cat, item, status, details in results:
        if status == "OK":
            badge = c.green("[OK]  ")
        elif status == "WARN":
            badge = c.amber("[WARN]")
        else:
            badge = c.red("[FAIL]")
        emit(f" {badge} {item:<24} : {details}")
    emit(c.dim("────────────────────────────────────────────────────────────\n"))


def run_config_cmd(c: Ansi, port: int = DEFAULT_PORT) -> None:
    sm = get_session_manager()
    emit(c.bold(c.cyan("\nLOCLX EFFECTIVE CONFIGURATION")))
    emit(c.dim("────────────────────────────────────────────────────────────"))
    emit(f"  LOCLX_VERSION         : {VERSION}")
    emit(f"  BIND_ADDR             : {BIND_ADDR} (fixed loopback invariant)")
    emit(f"  LOCLX_PORT            : {port}")
    emit(f"  LOCLX_SESSION_TTL     : {sm.default_timeout:.0f}s (30 mins)")
    emit(f"  LOCLX_MAX_HISTORY     : 500 (in-memory history limit)")
    emit(f"  LOCLX_IP_PROVIDER     : ipwho.is (fallback: ipapi.co)")
    emit(f"  LOCLX_DEBUG           : {'Enabled' if os.environ.get('LOCLX_DEBUG') else 'Disabled'}")
    emit(f"  BROWSER_AUTO_LAUNCH   : DISABLED (permanently disabled)")
    emit(c.dim("────────────────────────────────────────────────────────────\n"))


def print_session_creation(session: Any, server_url: str, c: Ansi, public_url: Optional[str] = None) -> None:
    if public_url:
        sess_url = build_session_url(public_url, session.sid)
    else:
        sess_url = f"{server_url.rstrip('/')}/session/{session.sid}"
    dash_url = f"{server_url.rstrip('/')}/dashboard/{session.sid}"
    box_art = r"""
========================================================
                     LOCLX SESSION
========================================================"""
    emit(c.green(box_art))
    emit(c.bold(c.green("\n[+] Session Created\n")))
    emit("ID:")
    emit(f"{session.sid}\n")
    emit("Status:")
    emit(f"{session.status}\n")
    emit("Created:")
    emit(f"{time.strftime('%H:%M:%S', time.localtime(session.created_at))}\n")
    emit("Expires:")
    emit(f"{time.strftime('%H:%M:%S', time.localtime(session.expires_at))}\n")
    emit("Collection URL:")
    emit(f"{sess_url}\n")
    emit("Dashboard (Local):")
    emit(f"{dash_url}\n")
    emit("QR:")
    emit("Use:")
    emit(f"loclx qr {session.sid}\n")
    emit(c.dim("[*] Browser auto-launch: DISABLED\n"))


def print_session_list(c: Ansi) -> None:
    sm = get_session_manager()
    sessions = list(sm.sessions.values())
    emit(c.bold(c.cyan("\nLOCLX SESSIONS")))
    emit(c.dim("────────────────────────────────────────────────────────\n"))
    emit(c.bold(f"{'ID':<12} {'STATUS':<11} {'AGE':<9} {'CONNECTED':<12} {'GPS'}"))

    for s in sessions:
        if s.is_expired():
            status_str = "EXPIRED"
            age_str = "--"
        elif s.status == "STOPPED":
            status_str = "STOPPED"
            age_str = format_uptime(time.time() - s.created_at)
        elif s.connected:
            status_str = "ACTIVE"
            age_str = format_uptime(time.time() - s.created_at)
        else:
            status_str = "WAITING"
            age_str = format_uptime(time.time() - s.created_at)

        conn_str = "YES" if s.connected else "NO"
        gps_str = "YES" if s.current_fix else "NO"

        emit(f"{s.sid:<12} {status_str:<11} {age_str:<9} {conn_str:<12} {gps_str}")
    emit("")


def print_target_gps_info(session: Any, c: Ansi) -> None:
    fix = session.current_fix
    if fix:
        emit(c.bold(c.green("\nTARGET CONNECTED")))
        emit(c.dim("────────────────────────────────────────"))
        emit(f"Session: {session.sid}\n")
        emit(c.bold("GPS:"))
        emit(f"Latitude   {fix['lat']:.9f}")
        emit(f"Longitude  {fix['lon']:.9f}")
        emit(f"Accuracy   ±{fix.get('accuracy') or 0:.0f} m")
        emit(f"Altitude   {fix.get('altitude') if fix.get('altitude') is not None else 'n/a'}")
        emit(f"Speed      {fix.get('speed') if fix.get('speed') is not None else 0:.1f} m/s")
        emit(f"Heading    {fix.get('heading') if fix.get('heading') is not None else 0:.0f}°")
        emit(f"Timestamp  {fix.get('timestamp') or 'n/a'}\n")
    else:
        emit(c.amber(f"\n[*] Session {session.sid}: Waiting for user browser location permission grant...\n"))


def print_ip_info(session: Any, c: Ansi) -> None:
    ip = session.ip_info
    emit(c.bold(c.cyan("\nNETWORK / IP INTELLIGENCE")))
    emit(c.dim("────────────────────────────────────────"))
    emit(f"Session: {session.sid}\n")
    if ip:
        emit(f"Public IP   : {ip.get('ip') or '—'}")
        emit(f"Country     : {ip.get('country') or '—'}")
        emit(f"Region      : {ip.get('region') or '—'}")
        emit(f"City        : {ip.get('city') or '—'}")
        emit(f"ISP         : {ip.get('isp') or '—'}")
        emit(f"Org         : {ip.get('org') or '—'}")
        emit(f"ASN         : {ip.get('asn') or '—'}")
        emit(f"Hostname    : {ip.get('hostname') or '—'}")
        emit(f"Coordinates : {ip.get('lat') if ip.get('lat') is not None else '—'}, {ip.get('lon') if ip.get('lon') is not None else '—'} (APPROXIMATE)\n")
    else:
        emit(c.amber("[*] Network IP intelligence lookup pending...\n"))


def print_browser_info(session: Any, c: Ansi) -> None:
    b = session.browser_info
    emit(c.bold(c.cyan("\nBROWSER / DEVICE INTELLIGENCE")))
    emit(c.dim("────────────────────────────────────────"))
    emit(f"Session: {session.sid}\n")
    if b:
        emit(f"User Agent  : {b.user_agent}")
        emit(f"Browser     : {b.browser} {b.browser_version}")
        emit(f"Platform    : {b.platform} ({b.device_type})")
        emit(f"Screen      : {b.screen_resolution}")
        emit(f"Viewport    : {b.viewport_size}")
        emit(f"CPU Cores   : {b.cpu_cores}")
        emit(f"Timezone    : {b.timezone}")
        emit(f"Language    : {b.language}")
        emit(f"Touch       : {b.touch_capability}\n")
    else:
        emit(c.amber("[*] Browser information pending...\n"))


def print_history_info(session: Any, c: Ansi) -> None:
    history = session.storage.get_history()
    emit(c.bold(c.cyan("\nLOCATION HISTORY")))
    emit(c.dim("────────────────────────────────────────"))
    emit(f"Session: {session.sid} ({len(history)} records)\n")
    if history:
        emit(c.bold(f"{'TIME':<10} {'LATITUDE':<14} {'LONGITUDE':<14} {'ACCURACY':<10} {'SOURCE'}"))
        for r in history:
            lat_s = f"{r['lat']:.9f}" if r.get('lat') is not None else "—"
            lon_s = f"{r['lon']:.9f}" if r.get('lon') is not None else "—"
            acc_s = f"±{r['accuracy']:.0f} m" if r.get('accuracy') is not None else "—"
            emit(f"{r.get('timestamp',''):<10} {lat_s:<14} {lon_s:<14} {acc_s:<10} {r.get('source','Browser Geolocation')}")
        emit("")
    else:
        emit(c.amber("[*] No GPS history records stored for this session.\n"))


def print_map_visualization(session: Any, server_url: str, c: Ansi) -> None:
    fix = session.current_fix
    ip = session.ip_info

    if fix:
        lat = fix['lat']
        lon = fix['lon']
        lat_lon_s = f"{lat:.9f},{lon:.9f}"
        osm_lat_lon = f"mlat={lat:.6f}&mlon={lon:.6f}"
        emit("GPS:")
        emit(f"{lat_lon_s}\n")
    else:
        lat_lon_s = "0.000000000,76.000000000"
        osm_lat_lon = ""
        emit("GPS:")
        emit("None available yet\n")

    emit("Google Maps:")
    emit(f"https://www.google.com/maps?q={lat_lon_s}\n")
    emit("Google Earth:")
    emit(f"https://earth.google.com/web/search/{lat_lon_s}\n")
    emit("OpenStreetMap:")
    if fix:
        emit(f"https://www.openstreetmap.org/?{osm_lat_lon}\n")
    else:
        emit("https://www.openstreetmap.org\n")

    if ip and ip.get("lat") is not None and ip.get("lon") is not None:
        emit("IP LOCATION:")
        emit(f"{ip['lat']:.6f}, {ip['lon']:.6f} (APPROXIMATE)\n")
    else:
        emit("IP LOCATION:")
        emit("Lookup pending\n")

    diff = session.calculate_ip_gps_diff()
    if diff is not None:
        emit("Distance:")
        emit(f"{format_distance(diff)}\n")

    emit(c.dim("[*] Browser auto-launch: DISABLED\n"))


def print_earth_visualization(session: Any, c: Ansi) -> None:
    fix = session.current_fix
    emit(c.bold(c.cyan("\nGOOGLE EARTH 3D LOCATION VIEW")))
    emit(c.dim("────────────────────────────────────────"))
    emit(f"Session: {session.sid}")
    if fix:
        lat_lon = f"{fix['lat']:.9f},{fix['lon']:.9f}"
        emit(f"Target Coordinates: {lat_lon}\n")
        emit("Google Earth URL:")
        emit(f"https://earth.google.com/web/search/{lat_lon}\n")
        emit("GeoURI:")
        emit(f"geo:{fix['lat']:.6f},{fix['lon']:.6f}?z=16\n")
    else:
        emit(c.amber("GPS Fix: None available yet (waiting for location permission grant)\n"))
    emit(c.dim("[*] Browser auto-launch: DISABLED"))
    emit(c.dim("[*] Open the URL manually in your browser or 3D GIS software.\n"))


def resolve_session_arg(target_id: Optional[str], c: Ansi) -> Optional[tuple[Any, str]]:
    sm = get_session_manager()
    if target_id:
        if not validate_sid_format(target_id):
            emit(c.red(f"[-] Invalid session ID format: {target_id}"))
            return None
        session = sm.sessions.get(target_id)
        if not session:
            emit(c.red(f"[-] Session not found or expired: {target_id}"))
            return None
        return session, target_id
    else:
        session = get_active_session()
        return session, session.sid


def parse_args(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        metavar="INT",
        help=f"preferred port on {BIND_ADDR} (default: {DEFAULT_PORT})",
    )
    common_parser.add_argument(
        "--public-url",
        type=str,
        default=None,
        help="public HTTPS reverse proxy capture URL (e.g. https://YOUR_DOMAIN)",
    )
    common_parser.add_argument(
        "--tunnel-url",
        type=str,
        default=None,
        help="manually configured public tunnel URL",
    )
    common_parser.add_argument(
        "--tunnel",
        action="store_true",
        default=False,
        help="start Cloudflare quick tunnel",
    )
    common_parser.add_argument(
        "--no-browser",
        action="store_true",
        help="(deprecated) browser auto-launch is permanently disabled",
    )
    common_parser.add_argument(
        "--debug",
        action="store_true",
        help="enable verbose debug logging",
    )
    common_parser.add_argument(
        "--lab",
        action="store_true",
        help="run self-contained local educational demonstration mode",
    )

    subcommand_common = argparse.ArgumentParser(add_help=False, argument_default=argparse.SUPPRESS)
    subcommand_common.add_argument(
        "--port",
        type=int,
        metavar="INT",
        help=f"preferred port on {BIND_ADDR} (default: {DEFAULT_PORT})",
    )
    subcommand_common.add_argument(
        "--public-url",
        type=str,
        help="public HTTPS reverse proxy capture URL (e.g. https://YOUR_DOMAIN)",
    )
    subcommand_common.add_argument(
        "--tunnel-url",
        type=str,
        help="manually configured public tunnel URL",
    )
    subcommand_common.add_argument(
        "--tunnel",
        action="store_true",
        help="start Cloudflare quick tunnel",
    )
    subcommand_common.add_argument(
        "--no-browser",
        action="store_true",
        help="(deprecated) browser auto-launch is permanently disabled",
    )
    subcommand_common.add_argument(
        "--debug",
        action="store_true",
        help="enable verbose debug logging",
    )
    subcommand_common.add_argument(
        "--lab",
        action="store_true",
        help="run self-contained local educational demonstration mode",
    )

    parser = argparse.ArgumentParser(
        prog="loclx",
        description=f"LOCLX v{VERSION} — Live Location & Information eXtractor (Terminal-First OSINT Tool).",
        epilog=f"The bind address is fixed at {BIND_ADDR} and cannot be changed.",
        parents=[common_parser],
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    subparsers = parser.add_subparsers(dest="subcommand", help="available subcommands")

    subparsers.add_parser("start", help="start server and create session", parents=[subcommand_common])
    subparsers.add_parser("listen", help="start server listener", parents=[subcommand_common])

    sess_p = subparsers.add_parser("session", help="session management", parents=[subcommand_common])
    sess_sub = sess_p.add_subparsers(dest="session_action", help="session action")
    sess_sub.add_parser("create", help="create new session", parents=[subcommand_common])
    sess_sub.add_parser("list", help="list active sessions", parents=[subcommand_common])
    sess_info = sess_sub.add_parser("info", help="display session info", parents=[subcommand_common])
    sess_info.add_argument("id", nargs="?", help="session ID")
    sess_stop = sess_sub.add_parser("stop", help="stop session", parents=[subcommand_common])
    sess_stop.add_argument("id", nargs="?", help="session ID")

    for cmd_name in ["target", "gps", "ip", "browser", "history", "map", "earth", "report", "live", "qr", "info", "dashboard"]:
        sp = subparsers.add_parser(cmd_name, help=f"run {cmd_name} action", parents=[subcommand_common])
        sp.add_argument("id", nargs="?", help="session ID")

    export_p = subparsers.add_parser("export", help="export session history", parents=[subcommand_common])
    export_p.add_argument("id", nargs="?", help="session ID")
    export_p.add_argument("--format", choices=["json", "csv"], default="json", help="export format")

    subparsers.add_parser("diagnostics", help="run system health diagnostics", parents=[subcommand_common])
    subparsers.add_parser("config", help="show effective configuration", parents=[subcommand_common])

    args = parser.parse_args(argv)
    if args.port < 0 or args.port > 65535:
        parser.error("--port must be between 0 and 65535")
    return args, []


def main(argv: Optional[list[str]] = None) -> int:
    configure_stdio()
    args, _ = parse_args(sys.argv[1:] if argv is None else argv)
    c = Ansi(use_color())

    tunnel_proc: Optional[Any] = None
    raw_public_url: Optional[str] = None
    should_start_tunnel: bool = False

    if getattr(args, "public_url", None):
        raw_public_url = args.public_url
    elif getattr(args, "tunnel_url", None):
        raw_public_url = args.tunnel_url
    elif os.environ.get("LOCLX_PUBLIC_URL"):
        raw_public_url = os.environ.get("LOCLX_PUBLIC_URL")
    elif os.environ.get("LOCLX_TUNNEL_URL"):
        raw_public_url = os.environ.get("LOCLX_TUNNEL_URL")

    if getattr(args, "tunnel", False) and not raw_public_url:
        should_start_tunnel = True

    validated_public_url: Optional[str] = None

    if raw_public_url:
        try:
            validated_public_url = validate_public_url(raw_public_url)
        except ValueError as exc:
            emit(c.red(f"[-] Invalid public capture URL: {exc}"))
            return 1

    if args.lab:
        run_lab_mode(c)

    if args.subcommand == "diagnostics":
        run_diagnostics_cmd(c, args.port)
        return 0
    elif args.subcommand == "config":
        run_config_cmd(c, args.port)
        return 0

    if args.subcommand in (None, "start", "listen"):
        if not validated_public_url and not should_start_tunnel:
            print_banner(c)
            emit(c.red("\n========================================================"))
            emit(c.red("[!] Public capture endpoint not configured.\n"))
            emit(c.red("Configure a public capture endpoint using one of the following:\n"))
            emit(c.red("  1. Cloudflare Quick Tunnel:"))
            emit(c.red("     loclx start --tunnel\n"))
            emit(c.red("  2. Manual Public HTTPS URL:"))
            emit(c.red("     loclx start --public-url https://your-domain.example\n"))
            emit(c.red("  3. Environment Variable:"))
            emit(c.red("     export LOCLX_PUBLIC_URL=https://your-domain.example"))
            emit(c.red("========================================================\n"))
            return 1

    print_banner(c)

    try:
        httpd, server_url = start_server_background(args.port)
        bound_port = httpd.server_address[1]
    except OSError as exc:
        emit(c.red(f"[-] Could not bind {BIND_ADDR}: {exc}"))
        return 1

    if should_start_tunnel and not validated_public_url:
        try:
            from loclx.tunnel import start_cloudflare_tunnel
            emit(c.amber("\n[*] Starting Cloudflare quick tunnel..."))
            tunnel_proc, validated_public_url = start_cloudflare_tunnel(bound_port)
        except RuntimeError as exc:
            emit(c.red(f"\n{exc}\n"))
            shutdown_server()
            return 1

    sm = get_session_manager()
    dash_renderer = TerminalDashboard(c)

    # Subcommand execution handling
    if args.subcommand == "session":
        act = getattr(args, "session_action", None)
        if act == "create":
            session = sm.create_session()
            print_session_creation(session, server_url, c, public_url=validated_public_url)
            shutdown_server()
            return 0
        elif act == "list":
            print_session_list(c)
            shutdown_server()
            return 0
        elif act == "info":
            res = resolve_session_arg(getattr(args, "id", None), c)
            if not res:
                shutdown_server()
                return 1
            session, _ = res
            emit(dash_renderer.render_session_info(session))
            shutdown_server()
            return 0
        elif act == "stop":
            res = resolve_session_arg(getattr(args, "id", None), c)
            if not res:
                shutdown_server()
                return 1
            session, sid = res
            sm.stop_session(sid)
            emit(c.amber(f"\n[+] Session stopped:\n    {sid}\n"))
            shutdown_server()
            return 0

    if args.subcommand == "live":
        res = resolve_session_arg(getattr(args, "id", None), c)
        if not res:
            shutdown_server()
            return 1
        session, _ = res
        emit(dash_renderer.render_live_session(session))
        shutdown_server()
        return 0

    if args.subcommand == "info":
        res = resolve_session_arg(getattr(args, "id", None), c)
        if not res:
            shutdown_server()
            return 1
        session, _ = res
        emit(dash_renderer.render_session_info(session))
        shutdown_server()
        return 0

    if args.subcommand == "report":
        res = resolve_session_arg(getattr(args, "id", None), c)
        if not res:
            shutdown_server()
            return 1
        session, _ = res
        emit(generate_target_report(session, c))
        shutdown_server()
        return 0

    if args.subcommand in ("target", "gps"):
        res = resolve_session_arg(getattr(args, "id", None), c)
        if not res:
            shutdown_server()
            return 1
        session, _ = res
        print_target_gps_info(session, c)
        shutdown_server()
        return 0

    if args.subcommand == "ip":
        res = resolve_session_arg(getattr(args, "id", None), c)
        if not res:
            shutdown_server()
            return 1
        session, _ = res
        print_ip_info(session, c)
        shutdown_server()
        return 0

    if args.subcommand == "browser":
        res = resolve_session_arg(getattr(args, "id", None), c)
        if not res:
            shutdown_server()
            return 1
        session, _ = res
        print_browser_info(session, c)
        shutdown_server()
        return 0

    if args.subcommand == "history":
        res = resolve_session_arg(getattr(args, "id", None), c)
        if not res:
            shutdown_server()
            return 1
        session, _ = res
        print_history_info(session, c)
        shutdown_server()
        return 0

    if args.subcommand == "export":
        res = resolve_session_arg(getattr(args, "id", None), c)
        if not res:
            shutdown_server()
            return 1
        session, _ = res
        fmt = getattr(args, "format", "json")
        if fmt == "csv":
            emit(session.storage.export_csv())
        else:
            emit(session.storage.export_json())
        shutdown_server()
        return 0

    if args.subcommand == "dashboard":
        res = resolve_session_arg(getattr(args, "id", None), c)
        if not res:
            shutdown_server()
            return 1
        session, sid = res
        dash_url = f"{server_url.rstrip('/')}/dashboard/{sid}"
        emit(c.bold(c.cyan("\nLOCLX DASHBOARD URL")))
        emit(c.dim("────────────────────────────────────────"))
        emit(f"Session: {sid}")
        emit(f"URL    : {dash_url}\n")
        shutdown_server()
        return 0

    if args.subcommand == "map":
        res = resolve_session_arg(getattr(args, "id", None), c)
        if not res:
            shutdown_server()
            return 1
        session, _ = res
        print_map_visualization(session, server_url, c)
        shutdown_server()
        return 0

    if args.subcommand == "earth":
        res = resolve_session_arg(getattr(args, "id", None), c)
        if not res:
            shutdown_server()
            return 1
        session, _ = res
        print_earth_visualization(session, c)
        shutdown_server()
        return 0

    if args.subcommand == "qr":
        res = resolve_session_arg(getattr(args, "id", None), c)
        if not res:
            shutdown_server()
            return 1
        session, sid = res
        if not validated_public_url:
            emit(c.red("[-] Public capture endpoint not configured. QR code requires a public HTTPS URL."))
            shutdown_server()
            return 1
        sess_url = build_session_url(validated_public_url, sid)
        emit(c.bold(c.cyan(f"  [+] TERMINAL QR CODE FOR SESSION {sid}:")))
        emit(generate_ascii_qr(sess_url))
        emit("")
        shutdown_server()
        return 0

    # Default capture workflow
    session = get_active_session()
    capture_url = build_session_url(validated_public_url, session.sid)

    emit(c.green(f"\n[+] Listener started"))
    emit(c.green(f"[+] Internal listener:\n    {BIND_ADDR}:{bound_port}\n"))
    emit(c.bold(c.cyan(f"[+] Public Capture URL:\n    {capture_url}\n")))
    emit(c.amber("[*] Waiting for connection..."))
    emit(c.dim("[*] Press Ctrl+C to stop.\n"))

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        emit(c.dim("\n[*] Shutting down LOCLX server..."))
    finally:
        if tunnel_proc:
            stop_cloudflare_tunnel(tunnel_proc)
        shutdown_server()

    return 0


if __name__ == "__main__":
    sys.exit(main())
