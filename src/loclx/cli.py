"""Terminal-first session-centric CLI for LOCLX v2.1.2."""

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
from loclx.server import BIND_ADDR, DEFAULT_PORT, get_active_session, get_session_manager, shutdown_server, start_server_background
from loclx.utils import Ansi, configure_stdio, emit, format_distance, format_uptime, use_color


def print_banner(c: Ansi) -> None:
    banner = r"""
╔══════════════════════════════════════════════════════════╗
║                         LOCLX                            ║
║     LIVE LOCATION & INFORMATION eXTRACTOR                ║
║                         v2.1.2                           ║
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
    emit(f"   {c.green('[9]')} Location Comparison")
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
    emit(c.bold(c.green("\n[+] SESSION CREATED")))
    emit(c.dim("──────────────────────────────────────────────"))
    emit(f"Session ID:\n  {session.sid}\n")
    emit(f"Status:\n  {session.status}\n")
    emit(f"Created:\n  {time.strftime('%H:%M:%S', time.localtime(session.created_at))}\n")
    emit(f"Expires:\n  {time.strftime('%H:%M:%S', time.localtime(session.expires_at))}\n")
    emit(f"Local collection URL:\n  {sess_url}\n")
    emit(c.dim("[*] Open the URL manually in an authorized browser when required.\n"))


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
        emit(f"Altitude   {fix.get('altitude') or 'n/a'}")
        emit(f"Speed      {fix.get('speed') or 0:.1f} m/s")
        emit(f"Heading    {fix.get('heading') or 0:.0f}°")
        emit(f"Timestamp  {fix.get('timestamp') or 'n/a'}\n")
    else:
        emit(c.amber(f"\n[*] Session {session.sid}: Waiting for user browser location permission grant...\n"))


def print_map_visualization(session, server_url: str, c: Ansi) -> None:
    fix = session.current_fix
    ip = session.ip_info
    dash_url = f"{server_url}dashboard/{session.sid}"

    emit(c.bold(c.cyan("\nLOCATION VISUALIZATION")))
    emit(c.dim("──────────────────────────────\n"))

    if fix:
        lat_lon_s = f"{fix['lat']:.9f}, {fix['lon']:.9f}"
        emit(f"GPS:\n  {lat_lon_s}\n")
        emit(f"Accuracy:\n  ±{fix.get('accuracy') or 0:.0f} m\n")
    else:
        lat_lon_s = "0.000000000, 0.000000000"
        emit("GPS:\n  None available yet\n")

    if ip and ip.get("lat") and ip.get("lon"):
        emit(f"IP:\n  {ip['lat']:.6f}, {ip['lon']:.6f}")
        emit("IP precision:\n  APPROXIMATE\n")
    else:
        emit("IP:\n  Lookup pending\n")

    diff = session.calculate_ip_gps_diff()
    if diff is not None:
        emit(f"Distance:\n  {format_distance(diff)}\n")

    emit(c.bold(c.cyan("MAP LINKS:")))
    emit(f"Google Maps:\n  https://www.google.com/maps/search/?api=1&query={lat_lon_s}")
    emit(f"Google Earth:\n  https://earth.google.com/web/search/{lat_lon_s}")
    if fix:
        emit(f"OpenStreetMap:\n  https://www.openstreetmap.org/?mlat={fix['lat']:.6f}&mlon={fix['lon']:.6f}#map=16/{fix['lat']:.6f}/{fix['lon']:.6f}")
    else:
        emit("OpenStreetMap:\n  https://www.openstreetmap.org")

    emit(c.bold(c.cyan(f"\nGlobal Earth Dashboard URL:\n  {dash_url}")))
    emit(c.dim("\n[*] Open manually.\n"))


def parse_args(argv: list[str]) -> tuple[argparse.Namespace, Optional[list[str]]]:
    parser = argparse.ArgumentParser(
        prog="loclx",
        description="LOCLX v2.1.2 — Live Location & Information eXtractor (Terminal-First OSINT Tool).",
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

    for cmd_name in ["target", "gps", "ip", "browser", "history", "map", "earth", "report", "live", "qr"]:
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
            sessions = sm.list_sessions()
            emit(c.bold(c.cyan(f"\n[+] Active Sessions ({len(sessions)}):")))
            for s in sessions:
                emit(f"  - {s.sid} | Created: {time_str(s.created_at)} | Status: {s.status} | Client: {'Connected' if s.connected else 'Waiting'} | GPS Updates: {s.gps_updates}")
            emit("")
        elif choice in ("3", "session info", "info"):
            session = get_active_session()
            emit(f"\n{dash_renderer.render_session_dashboard(session)}\n")
        elif choice in ("4", "session stop", "stop"):
            session = get_active_session()
            sm.stop_session(session.sid)
            emit(c.amber(f"\n[-] Stopped session {session.sid}\n"))
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
        elif choice in ("9", "comparison"):
            session = get_active_session()
            emit(f"\n{dash_renderer.render_session_dashboard(session)}\n")
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


def time_str(t: float) -> str:
    return time.strftime("%H:%M:%S", time.localtime(t))


def main(argv: Optional[list[str]] = None) -> int:
    configure_stdio()
    args, remaining = parse_args(sys.argv[1:] if argv is None else argv)
    c = Ansi(use_color())

    if args.lab:
        run_lab_mode(c)

    # Standalone non-server subcommands
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

    if args.subcommand == "qr":
        emit(c.bold(c.cyan(f"  [+] TERMINAL QR CODE FOR SESSION {session.sid}:")))
        emit(generate_ascii_qr(sess_url))
        emit("")

    if args.subcommand == "report":
        target_sid = getattr(args, "id", None) or session.sid
        target_sess = get_session_manager().get_session(target_sid) or session
        emit(generate_target_report(target_sess, c))
        shutdown_server()
        return 0

    if args.subcommand in ("target", "gps"):
        print_target_gps_info(session, c)
        shutdown_server()
        return 0
    elif args.subcommand in ("map", "earth"):
        print_map_visualization(session, server_url, c)
        shutdown_server()
        return 0

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
