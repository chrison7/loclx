"""CLI interface, interactive menu loop, and lab mode for LOCLX."""

from __future__ import annotations

import argparse
import json
import os
import sys
import webbrowser
from typing import Optional

from loclx import VERSION
from loclx.dashboard import TerminalDashboard
from loclx.ipinfo import IPManager
from loclx.server import BIND_ADDR, DEFAULT_PORT, get_active_session, get_session_manager, shutdown_server, start_server_background
from loclx.utils import Ansi, configure_stdio, emit, format_uptime, use_color


def print_banner(c: Ansi) -> None:
    banner = r"""
╔══════════════════════════════════════════════╗
║                 LOCLX                        ║
║      Live Location & Information eXtractor   ║
║                 v2.0                         ║
╚══════════════════════════════════════════════╝"""
    emit(c.green(banner))
    emit(c.cyan("  localhost security & permission laboratory"))
    emit(c.dim(f"  bind address: {BIND_ADDR} (fixed) · standard library core\n"))


def print_menu(c: Ansi) -> None:
    emit(c.bold(c.green("MAIN MENU")))
    emit(f" {c.cyan('[1]')} Start Session")
    emit(f" {c.cyan('[2]')} Start Server")
    emit(f" {c.cyan('[3]')} Open Dashboard")
    emit(f" {c.cyan('[4]')} Active Sessions")
    emit(f" {c.cyan('[5]')} Session Information")
    emit(f" {c.cyan('[6]')} Location History")
    emit(f" {c.cyan('[7]')} Browser Information")
    emit(f" {c.cyan('[8]')} IP Intelligence")
    emit(f" {c.cyan('[9]')} Configuration")
    emit(f" {c.cyan('[10]')} Diagnostics")
    emit(f" {c.cyan('[0]')} Exit\n")


def run_lab_mode(c: Ansi) -> None:
    emit(c.bold(c.cyan("\n--- LOCLX SECURITY LAB MODE ---")))
    emit("1. IP Geolocation is based on network routing databases and provides an APPROXIMATE estimate.")
    emit("2. Precise GPS coordinates are retrieved ONLY via the browser Geolocation API after EXPLICIT permission.")
    emit("3. All coordinates and session data remain on localhost (127.0.0.1) and are held in memory.")
    emit("4. Outbound network activity is logged live on the lab page for inspection.\n")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="loclx",
        description="LOCLX v2.0 — Live Location & Information eXtractor laboratory.",
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
    args = parser.parse_args(argv)
    if args.port < 0 or args.port > 65535:
        parser.error("--port must be between 0 and 65535")
    return args


def interactive_menu_loop(server_url: str, c: Ansi) -> None:
    sm = get_session_manager()
    dash_renderer = TerminalDashboard(c)

    while True:
        print_menu(c)
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
            emit(c.green(f"\n[+] HTTP Server running at {server_url}\n"))
        elif choice == "3":
            dash_url = f"{server_url}dashboard"
            webbrowser.open(dash_url)
            emit(c.dim(f"\nopened {dash_url}\n"))
        elif choice == "4":
            sessions = sm.list_sessions()
            emit(c.bold(c.cyan(f"\nActive Sessions ({len(sessions)}):")))
            for s in sessions:
                emit(f"  - {s.sid} | Created: {time_str(s.created_at)} | Status: {s.status} | GPS Updates: {s.gps_updates}")
            emit("")
        elif choice == "5":
            session = get_active_session()
            emit(f"\n{dash_renderer.render_session_dashboard(session)}\n")
        elif choice == "6":
            session = get_active_session()
            history = session.storage.get_history()
            emit(c.bold(c.cyan(f"\nLocation History for {session.sid} ({len(history)} entries):")))
            for h in history:
                emit(f"  [{h['timestamp']}] Lat: {h['lat']:.6f} | Lon: {h['lon']:.6f} | Acc: ±{h.get('accuracy') or 0:.0f}m")
            emit("")
        elif choice == "7":
            session = get_active_session()
            if session.browser_info:
                emit(c.bold(c.cyan("\nBrowser Information:")))
                for k, v in session.browser_info.to_dict().items():
                    emit(f"  {k:<20}: {v}")
                emit("")
            else:
                emit(c.amber("\nNo browser information received yet.\n"))
        elif choice == "8":
            ip_mgr = IPManager()
            info = ip_mgr.fetch_ip_info()
            if info:
                emit(c.bold(c.cyan("\nIP Intelligence (APPROXIMATE):")))
                for k, v in info.items():
                    emit(f"  {k:<15}: {v}")
                emit("")
            else:
                emit(c.red("\nIP intelligence lookup failed.\n"))
        elif choice == "9":
            emit(c.bold(c.cyan("\nConfiguration:")))
            emit(f"  BIND_ADDR             : {BIND_ADDR} (fixed)")
            emit(f"  DEFAULT_PORT          : {DEFAULT_PORT}")
            emit("  SESSION_TIMEOUT_SEC   : 1800.0")
            emit("  DEFAULT_IP_PROVIDER   : ipwho.is (fallback: ipapi.co)\n")
        elif choice == "10":
            emit(c.bold(c.cyan("\nDiagnostics:")))
            emit(f"  Python Version        : {sys.version.split()[0]}")
            emit(f"  Platform              : {sys.platform}")
            emit(f"  LOCLX Version         : {VERSION}")
            emit("  Server Status         : Running\n")
        elif choice == "0":
            return
        elif choice == "":
            continue
        else:
            emit(c.red("\nUnknown choice. Please enter a valid menu number.\n"))


def time_str(t: float) -> str:
    import time
    return time.strftime("%H:%M:%S", time.localtime(t))


def main(argv: Optional[list[str]] = None) -> int:
    configure_stdio()
    args = parse_args(sys.argv[1:] if argv is None else argv)
    c = Ansi(use_color())

    if args.lab:
        run_lab_mode(c)

    print_banner(c)

    try:
        httpd, server_url = start_server_background(args.port)
    except OSError as exc:
        emit(c.red(f"Could not bind {BIND_ADDR}: {exc}"))
        return 1

    emit(c.green(f"  Lab Page  : {server_url}"))
    emit(c.green(f"  Dashboard : {server_url}dashboard"))
    emit(c.dim("  In-memory session storage · Ctrl-C or [0] to exit\n"))

    if not args.no_browser:
        webbrowser.open(server_url)

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
