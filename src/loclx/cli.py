"""CLI subcommands, interactive menu loop, and lab mode for LOCLX v2.1.0."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import time
import webbrowser
from typing import Optional

from loclx import VERSION
from loclx.dashboard import TerminalDashboard
from loclx.diagnostics import DiagnosticRunner
from loclx.ipinfo import IPManager
from loclx.qrcode import generate_ascii_qr
from loclx.server import BIND_ADDR, DEFAULT_PORT, get_active_session, get_session_manager, shutdown_server, start_server_background
from loclx.utils import Ansi, configure_stdio, emit, format_distance, format_uptime, use_color


def print_banner(c: Ansi) -> None:
    banner = r"""
╔════════════════════════════════════════════════════════════╗
║                         LOCLX                              ║
║          Live Location & Information eXtractor             ║
║                         v2.1.0                             ║
╚════════════════════════════════════════════════════════════╝"""
    emit(c.green(banner))
    emit(c.cyan("  localhost security & permission laboratory"))
    emit(c.dim(f"  bind address: {BIND_ADDR} (fixed) · standard library core\n"))


def print_grouped_menu(c: Ansi) -> None:
    width = min(max(shutil.get_terminal_size().columns - 2, 58), 62)
    sep = c.dim("─" * width)

    emit(c.bold(c.cyan("  SESSION")))
    emit(sep)
    emit(f"  {c.green('[1]')}  Start New Session")
    emit(f"  {c.green('[2]')}  Active Sessions")
    emit(f"  {c.green('[3]')}  Session Information")
    emit(f"  {c.green('[4]')}  Stop Session\n")

    emit(c.bold(c.cyan("  ANALYSIS")))
    emit(sep)
    emit(f"  {c.green('[5]')}  Live Dashboard")
    emit(f"  {c.green('[6]')}  GPS Information")
    emit(f"  {c.green('[7]')}  IP Intelligence")
    emit(f"  {c.green('[8]')}  Browser Information")
    emit(f"  {c.green('[9]')}  Location History\n")

    emit(c.bold(c.cyan("  TOOLS")))
    emit(sep)
    emit(f"  {c.green('[10]')} Export Session")
    emit(f"  {c.green('[11]')} QR Code")
    emit(f"  {c.green('[12]')} Diagnostics")
    emit(f"  {c.green('[13]')} Configuration\n")

    emit(f"  {c.red('[0]')}  Exit\n")


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
    emit(c.dim("────────────────────────────────────────────────────────────\n"))


def parse_args(argv: list[str]) -> tuple[argparse.Namespace, Optional[list[str]]]:
    parser = argparse.ArgumentParser(
        prog="loclx",
        description="LOCLX v2.1.0 — Live Location & Information eXtractor laboratory.",
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
        help="do not auto-open the web page at startup",
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

    subparsers.add_parser("start", help="start server and create active session")

    sess_parser = subparsers.add_parser("session", help="session management commands")
    sess_sub = sess_parser.add_subparsers(dest="session_action", help="session action")
    sess_sub.add_parser("list", help="list active sessions")
    sess_info = sess_sub.add_parser("info", help="display session details")
    sess_info.add_argument("id", nargs="?", help="session ID")
    sess_stop = sess_sub.add_parser("stop", help="stop specified session")
    sess_stop.add_argument("id", nargs="?", help="session ID")

    subparsers.add_parser("dashboard", help="open or render live dashboard")
    subparsers.add_parser("gps", help="show GPS fix information")
    subparsers.add_parser("ip", help="show network IP intelligence")
    subparsers.add_parser("browser", help="show browser information")
    subparsers.add_parser("history", help="show session location history")

    export_p = subparsers.add_parser("export", help="export session history to JSON or CSV")
    export_p.add_argument("id", nargs="?", help="session ID")
    export_p.add_argument("--format", choices=["json", "csv"], default="json", help="export format (default: json)")

    subparsers.add_parser("diagnostics", help="run system health diagnostics")
    subparsers.add_parser("config", help="show effective configuration")
    subparsers.add_parser("qr", help="render ASCII QR code for local server URL")

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
        choice = raw.strip()

        if choice == "1":
            session = sm.create_session()
            emit(c.green(f"\n[+] Created new session: {session.sid}\n"))
        elif choice == "2":
            sessions = sm.list_sessions()
            emit(c.bold(c.cyan(f"\n[+] Active Sessions ({len(sessions)}):")))
            for s in sessions:
                emit(f"  - {s.sid} | Created: {time_str(s.created_at)} | Status: {s.status} | GPS Updates: {s.gps_updates}")
            emit("")
        elif choice == "3":
            session = get_active_session()
            emit(f"\n{dash_renderer.render_session_dashboard(session)}\n")
        elif choice == "4":
            session = get_active_session()
            sm.stop_session(session.sid)
            emit(c.amber(f"\n[-] Stopped session {session.sid}\n"))
        elif choice == "5":
            dash_url = f"{server_url}dashboard"
            webbrowser.open(dash_url)
            emit(c.dim(f"\n[+] Opened {dash_url}\n"))
        elif choice == "6":
            session = get_active_session()
            if session.current_fix:
                fix = session.current_fix
                emit(c.bold(c.green("\n[+] GPS FIX (EXPLICIT USER PERMISSION):")))
                emit(f"  Latitude   : {fix['lat']:.6f}")
                emit(f"  Longitude  : {fix['lon']:.6f}")
                emit(f"  Accuracy   : ±{fix.get('accuracy') or 0:.0f} m")
                emit(f"  Altitude   : {fix.get('altitude') or 'n/a'}")
                emit(f"  Last Update: {fix.get('timestamp') or 'n/a'}\n")
            else:
                emit(c.amber("\n[*] Waiting for browser location permission & GPS fix...\n"))
        elif choice == "7":
            ip_mgr = IPManager()
            info = ip_mgr.fetch_ip_info()
            if info:
                emit(c.bold(c.cyan("\n[*] NETWORK GEOLOCATION — APPROXIMATE:")))
                for k, v in info.items():
                    emit(f"  {k:<15}: {v}")
                emit("")
            else:
                emit(c.red("\n[-] IP intelligence lookup unavailable.\n"))
        elif choice == "8":
            session = get_active_session()
            if session.browser_info:
                emit(c.bold(c.cyan("\n[*] BROWSER INFORMATION:")))
                for k, v in session.browser_info.to_dict().items():
                    emit(f"  {k:<20}: {v}")
                emit("")
            else:
                emit(c.amber("\n[*] No browser information received yet.\n"))
        elif choice == "9":
            session = get_active_session()
            history = session.storage.get_history()
            emit(c.bold(c.cyan(f"\n[*] Location History for {session.sid} ({len(history)} entries):")))
            for h in history:
                emit(f"  [{h['timestamp']}] Lat: {h['lat']:.6f} | Lon: {h['lon']:.6f} | Acc: ±{h.get('accuracy') or 0:.0f}m")
            emit("")
        elif choice == "10":
            session = get_active_session()
            emit(c.bold(c.cyan(f"\n[+] Exporting Session {session.sid} (JSON):")))
            emit(session.storage.export_json()[:500] + "\n...")
            emit("")
        elif choice == "11":
            emit(c.bold(c.cyan(f"\n[+] TERMINAL QR CODE FOR LOCAL URL ({server_url}):")))
            emit(generate_ascii_qr(server_url))
            emit("")
        elif choice == "12":
            port = int(server_url.split(":")[-1].strip("/"))
            run_diagnostics_cmd(c, port)
        elif choice == "13":
            port = int(server_url.split(":")[-1].strip("/"))
            run_config_cmd(c, port)
        elif choice == "0":
            return
        elif choice == "":
            continue
        else:
            emit(c.red("\n[-] Unknown choice. Please enter a valid menu number.\n"))


def time_str(t: float) -> str:
    return time.strftime("%H:%M:%S", time.localtime(t))


def main(argv: Optional[list[str]] = None) -> int:
    configure_stdio()
    args, remaining = parse_args(sys.argv[1:] if argv is None else argv)
    c = Ansi(use_color())

    if args.lab:
        run_lab_mode(c)

    # Execute standalone non-server subcommands directly
    if args.subcommand == "diagnostics":
        run_diagnostics_cmd(c, args.port)
        return 0
    elif args.subcommand == "config":
        run_config_cmd(c, args.port)
        return 0

    print_banner(c)

    try:
        httpd, server_url = start_server_background(args.port)
    except OSError as exc:
        emit(c.red(f"[-] Could not bind {BIND_ADDR}: {exc}"))
        return 1

    emit(c.green(f"  Lab Page  : {server_url}"))
    emit(c.green(f"  Dashboard : {server_url}dashboard"))
    emit(c.dim("  In-memory session storage · Ctrl-C or [0] to exit\n"))

    if args.subcommand == "qr":
        emit(c.bold(c.cyan(f"  [+] TERMINAL QR CODE FOR LOCAL URL ({server_url}):")))
        emit(generate_ascii_qr(server_url))
        emit("")

    if not args.no_browser and args.subcommand is None:
        webbrowser.open(server_url)

    if args.subcommand == "dashboard":
        webbrowser.open(f"{server_url}dashboard")
    elif args.subcommand == "gps":
        session = get_active_session()
        dash = TerminalDashboard(c)
        emit(dash.render_session_dashboard(session))
        shutdown_server()
        return 0
    elif args.subcommand == "ip":
        ip_mgr = IPManager()
        info = ip_mgr.fetch_ip_info()
        if info:
            emit(c.bold(c.cyan("\n[*] NETWORK GEOLOCATION — APPROXIMATE:")))
            for k, v in info.items():
                emit(f"  {k:<15}: {v}")
            emit("")
        else:
            emit(c.red("\n[-] IP intelligence lookup unavailable.\n"))
        shutdown_server()
        return 0
    elif args.subcommand == "browser":
        session = get_active_session()
        if session.browser_info:
            emit(c.bold(c.cyan("\n[*] BROWSER INFORMATION:")))
            for k, v in session.browser_info.to_dict().items():
                emit(f"  {k:<20}: {v}")
            emit("")
        else:
            emit(c.amber("\n[*] No browser information received yet.\n"))
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
