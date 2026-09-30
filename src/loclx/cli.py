"""Terminal-first session-centric CLI for LOCLX v2.3.0."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import time
from typing import Optional

from loclx import VERSION
from loclx.dashboard import TerminalDashboard, generate_target_report
from loclx.diagnostics import DiagnosticRunner
from loclx.ipinfo import IPManager
from loclx.qrcode import generate_ascii_qr
from loclx.security import validate_sid_format
from loclx.server import BIND_ADDR, DEFAULT_PORT, get_active_session, get_session_manager, shutdown_server, start_server_background
from loclx.utils import Ansi, configure_stdio, emit, format_distance, format_uptime, use_color


def print_banner(c: Ansi) -> None:
    banner = r"""
╔══════════════════════════════════════════════════════════╗
║                         LOCLX                            ║
║     LIVE LOCATION & INFORMATION eXTRACTOR                ║
║                         v2.3.0                           ║
╚══════════════════════════════════════════════════════════╝"""
    emit(c.green(banner))


def print_grouped_menu(c: Ansi) -> None:
    width = min(max(shutil.get_terminal_size().columns - 2, 52), 60)
    sep = c.dim("─" * width)

    emit(c.bold(c.cyan("  LOCLX MAIN MENU")))
    emit(sep)

    emit(c.bold(c.cyan("\n  SESSION")))
    emit(f"   {c.green('[1]')} Create Session")
    emit(f"   {c.green('[2]')} List Sessions")
    emit(f"   {c.green('[3]')} Session Information")
    emit(f"   {c.green('[4]')} Stop Session")

    emit(c.bold(c.cyan("\n  INFORMATION")))
    emit(f"   {c.green('[5]')} Target Information")
    emit(f"   {c.green('[6]')} GPS Information")
    emit(f"   {c.green('[7]')} IP Intelligence")
    emit(f"   {c.green('[8]')} Browser Information")

    emit(c.bold(c.cyan("\n  ANALYSIS")))
    emit(f"   {c.green('[9]')} Live Dashboard")
    emit(f"   {c.green('[10]')} Location History")
    emit(f"   {c.green('[11]')} Map / Earth Links")

    emit(c.bold(c.cyan("\n  TOOLS")))
    emit(f"   {c.green('[12]')} Generate Report")
    emit(f"   {c.green('[13]')} Export Session")
    emit(f"   {c.green('[14]')} QR Code")
    emit(f"   {c.green('[15]')} Diagnostics\n")

    emit(f"   {c.red('[0]')} Exit\n")


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


def print_session_creation(session, server_url: str, c: Ansi) -> None:
    sess_url = f"{server_url}session/{session.sid}"
    dash_url = f"{server_url}dashboard/{session.sid}"
    box_art = r"""
╔══════════════════════════════════════════════════════════╗
║                    LOCLX SESSION                         ║
╚══════════════════════════════════════════════════════════╝"""
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
    emit("Dashboard:")
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


def print_target_gps_info(session, c: Ansi) -> None:
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


def print_map_visualization(session, server_url: str, c: Ansi) -> None:
    fix = session.current_fix
    ip = session.ip_info

    if fix:
        lat = fix['lat']
        lon = fix['lon']
        lat_lon_s = f"{lat:.9f},{lon:.9f}"
        osm_lat_lon = f"mlat={lat:.6f}&mlon={lon:.6f}#map=16/{lat:.6f}/{lon:.6f}"
        emit("GPS:")
        emit(f"{lat_lon_s}\n")
    else:
        lat_lon_s = "0.000000000,76.000000000"
        osm_lat_lon = ""
        emit("GPS:")
        emit("None available yet\n")

    emit("Google Maps:")
    emit(f"https://www.google.com/maps/search/?api=1&query={lat_lon_s}\n")
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


def print_earth_visualization(session, c: Ansi) -> None:
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


def parse_args(argv: list[str]) -> tuple[argparse.Namespace, Optional[list[str]]]:
    parser = argparse.ArgumentParser(
        prog="loclx",
        description="LOCLX v2.3.0 — Live Location & Information eXtractor (Terminal-First OSINT Tool).",
        epilog=f"The bind address is fixed at {BIND_ADDR} and cannot be changed.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        metavar="INT",
        help=f"preferred port on {BIND_ADDR} (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="(deprecated) browser auto-launch is permanently disabled",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="enable verbose debug logging",
    )
    parser.add_argument(
        "--lab",
        action="store_true",
        help="run self-contained local educational demonstration mode",
    )

    subparsers = parser.add_subparsers(dest="subcommand", help="available subcommands")

    subparsers.add_parser("start", help="start server and create session")
    subparsers.add_parser("listen", help="start server listener")

    sess_p = subparsers.add_parser("session", help="session management")
    sess_sub = sess_p.add_subparsers(dest="session_action", help="session action")
    sess_sub.add_parser("create", help="create new session")
    sess_sub.add_parser("list", help="list active sessions")
    sess_info = sess_sub.add_parser("info", help="display session info")
    sess_info.add_argument("id", nargs="?", help="session ID")
    sess_stop = sess_sub.add_parser("stop", help="stop session")
    sess_stop.add_argument("id", nargs="?", help="session ID")

    for cmd_name in ["target", "gps", "ip", "browser", "history", "map", "earth", "report", "live", "qr", "info"]:
        sp = subparsers.add_parser(cmd_name, help=f"run {cmd_name} action")
        sp.add_argument("id", nargs="?", help="session ID")

    export_p = subparsers.add_parser("export", help="export session history")
    export_p.add_argument("id", nargs="?", help="session ID")
    export_p.add_argument("--format", choices=["json", "csv"], default="json", help="export format")

    subparsers.add_parser("dashboard", help="print live dashboard URL")
    subparsers.add_parser("diagnostics", help="run system health diagnostics")
    subparsers.add_parser("config", help="show effective configuration")

    known, remaining = parser.parse_known_args(argv)
    if known.port < 0 or known.port > 65535:
        parser.error("--port must be between 0 and 65535")
    return known, remaining


def interactive_menu_loop(server_url: str, c: Ansi) -> None:
    sm = get_session_manager()
    dash_renderer = TerminalDashboard(c)

    while True:
        print_grouped_menu(c)
        try:
            raw = input(c.green("LOCLX > "))
        except (EOFError, KeyboardInterrupt):
            emit("\n")
            return
        choice = raw.strip().lower()

        if choice in ("1", "session create", "create"):
            session = sm.create_session()
            print_session_creation(session, server_url, c)
        elif choice in ("2", "session list", "list"):
            print_session_list(c)
        elif choice in ("3", "session info", "info"):
            session = get_active_session()
            emit(f"\n{dash_renderer.render_session_info(session)}\n")
        elif choice in ("4", "session stop", "stop"):
            session = get_active_session()
            sm.stop_session(session.sid)
            emit(c.amber(f"\n[+] Session stopped:\n    {session.sid}\n"))
        elif choice in ("5", "target"):
            session = get_active_session()
            print_target_gps_info(session, c)
        elif choice in ("6", "gps"):
            session = get_active_session()
            print_target_gps_info(session, c)
        elif choice in ("7", "ip"):
            ip_mgr = IPManager()
            info = ip_mgr.fetch_ip_info()
            if info:
                emit(c.bold(c.cyan("\n[*] NETWORK GEOLOCATION — APPROXIMATE:")))
                for k, v in info.items():
                    emit(f"  {k:<15}: {v}")
                emit("")
            else:
                emit(c.red("\n[-] IP intelligence lookup unavailable.\n"))
        elif choice in ("8", "browser"):
            session = get_active_session()
            if session.browser_info:
                emit(c.bold(c.cyan("\n[*] BROWSER INFORMATION:")))
                for k, v in session.browser_info.to_dict().items():
                    emit(f"  {k:<20}: {v}")
                emit("")
            else:
                emit(c.amber("\n[*] No browser information received yet.\n"))
        elif choice in ("9", "live", "dashboard"):
            session = get_active_session()
            emit(f"\n{dash_renderer.render_live_session(session)}\n")
        elif choice in ("10", "history"):
            session = get_active_session()
            history = session.storage.get_history()
            emit(c.bold(c.cyan(f"\n[*] Location History for {session.sid} ({len(history)} entries):")))
            emit(c.dim("#   TIME       LAT          LON          ACC"))
            for idx, h in enumerate(history, 1):
                emit(f"{idx:<3} {h['timestamp']:<10} {h['lat']:.6f}   {h['lon']:.6f}   ±{h.get('accuracy') or 0:.0f}m")
            emit("")
        elif choice in ("11", "map", "earth"):
            session = get_active_session()
            print_map_visualization(session, server_url, c)
        elif choice in ("12", "report"):
            session = get_active_session()
            emit(f"\n{generate_target_report(session, c)}\n")
        elif choice in ("13", "export"):
            session = get_active_session()
            emit(c.bold(c.cyan(f"\n[+] Exporting Session {session.sid} (JSON):")))
            emit(session.storage.export_json()[:500] + "\n...")
            emit("")
        elif choice in ("14", "qr"):
            session = get_active_session()
            sess_url = f"{server_url}session/{session.sid}"
            emit(c.bold(c.cyan(f"\n[+] QR CODE FOR SESSION {session.sid} ({sess_url}):")))
            emit(generate_ascii_qr(sess_url))
            emit("")
        elif choice in ("15", "diagnostics"):
            port = int(server_url.split(":")[-1].strip("/"))
            run_diagnostics_cmd(c, port)
        elif choice == "0" or choice in ("exit", "quit"):
            return
        elif choice == "":
            continue
        else:
            emit(c.red("\n[-] Unknown choice. Please enter a valid menu number or command.\n"))


def main(argv: Optional[list[str]] = None) -> int:
    configure_stdio()
    args, remaining = parse_args(sys.argv[1:] if argv is None else argv)
    c = Ansi(use_color())

    if args.lab:
        run_lab_mode(c)

    if args.subcommand == "diagnostics":
        run_diagnostics_cmd(c, args.port)
        return 0
    elif args.subcommand == "config":
        run_config_cmd(c, args.port)
        return 0

    print_banner(c)

    try:
        httpd, server_url = start_server_background(args.port)
        bound_port = httpd.server_address[1]
    except OSError as exc:
        emit(c.red(f"[-] Could not bind {BIND_ADDR}: {exc}"))
        return 1

    sm = get_session_manager()
    dash_renderer = TerminalDashboard(c)

    # Subcommand execution handling
    if args.subcommand == "session":
        act = args.session_action
        if act == "create":
            session = sm.create_session()
            print_session_creation(session, server_url, c)
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
        sess_url = f"{server_url}session/{sid}"
        emit(c.bold(c.cyan(f"  [+] TERMINAL QR CODE FOR SESSION {sid}:")))
        emit(generate_ascii_qr(sess_url))
        emit("")
        shutdown_server()
        return 0

    session = get_active_session()
    sess_url = f"{server_url}session/{session.sid}"
    dash_url = f"{server_url}dashboard/{session.sid}"

    emit(c.green(f"[+] LISTENER"))
    emit(f"    {BIND_ADDR}:{bound_port}\n")

    emit(c.green(f"[+] STATUS"))
    emit(f"    WAITING FOR SESSION ({session.sid})\n")

    emit(c.cyan(f"[*] Local collection URL : {sess_url}"))
    emit(c.cyan(f"[*] Dashboard URL        : {dash_url}"))
    emit(c.dim("[*] Browser auto-launch   : DISABLED (Terminal-First)\n"))

    try:
        interactive_menu_loop(server_url, c)
    except KeyboardInterrupt:
        emit("\n")
    finally:
        emit(c.dim("Shutting down LOCLX server..."))
        shutdown_server()

    return 0


if __name__ == "__main__":
    sys.exit(main())
