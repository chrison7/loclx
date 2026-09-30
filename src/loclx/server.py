"""HTTP API Server and Static Web Asset Server for LOCLX."""

from __future__ import annotations

import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Optional

from loclx.ipinfo import IPManager
from loclx.security import MAX_REQUEST_BODY, RateLimiter, sanitize_input
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
            self.serve_file("index.html", "text/html; charset=utf-8")
        elif url_path == "/dashboard" or url_path == "/dashboard.html":
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
        elif url_path.startswith("/api/session/"):
            parts = url_path.strip("/").split("/")
            if len(parts) >= 3 and parts[2]:
                sid = parts[2]
                session = _session_manager.get_session(sid)
                if not session:
                    self.send_json(404, {"error": "Session not found"})
                    return
                if len(parts) == 4 and parts[3] == "history":
                    self.send_json(200, session.storage.get_history())
                elif len(parts) == 4 and parts[3] == "export":
                    fmt = self.path.split("format=")[-1] if "format=" in self.path else "json"
                    if fmt == "csv":
                        csv_data = session.storage.export_csv().encode("utf-8")
                        self.send_response(200)
                        self.send_header("Content-Type", "text/csv")
                        self.send_header("Content-Length", str(len(csv_data)))
                        self.end_headers()
                        self.wfile.write(csv_data)
                    else:
                        self.send_json(200, session.storage.get_history())
                else:
                    self.send_json(200, session.to_dict())
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
            self._handle_location_update(session, payload)
            self.send_json(200, {"status": "ok", "sessionId": session.sid})
        elif url_path == "/api/session":
            session = _session_manager.create_session()
            self.send_json(201, session.to_dict())
        elif url_path.startswith("/api/session/"):
            parts = url_path.strip("/").split("/")
            if len(parts) >= 3:
                sid = parts[2]
                session = _session_manager.get_session(sid)
                if not session:
                    self.send_json(404, {"error": "Session not found"})
                    return
                if len(parts) == 4 and parts[3] == "location":
                    self._handle_location_update(session, payload)
                    self.send_json(200, {"status": "ok"})
                elif len(parts) == 4 and parts[3] == "stop":
                    session.stop()
                    self.send_json(200, {"status": "stopped"})
                else:
                    self.send_json(400, {"error": "Invalid endpoint"})
        else:
            self.send_error(404, "Not Found")

    def _handle_location_update(self, session: Session, payload: dict[str, Any]) -> None:
        gps_data = payload.get("gps")
        ip_data = payload.get("ip")
        browser_data = payload.get("browser")

        if isinstance(gps_data, dict) and "lat" in gps_data and "lon" in gps_data:
            session.update_gps(gps_data)

        if isinstance(ip_data, dict):
            session.set_ip_info(ip_data)
        elif session.ip_info is None:
            fetched_ip = _ip_manager.fetch_ip_info()
            if fetched_ip:
                session.set_ip_info(fetched_ip)

        if isinstance(browser_data, dict):
            session.set_browser_info(browser_data)

        # Emit live update notification to terminal console
        c = Ansi(True)
        emit(c.green(f"\n[+] GPS update received for Session {session.sid}"))
        if session.current_fix:
            emit(c.cyan(f"  Latitude : {session.current_fix['lat']:.6f}"))
            emit(c.cyan(f"  Longitude: {session.current_fix['lon']:.6f}"))
            if session.current_fix.get("accuracy"):
                emit(c.cyan(f"  Accuracy : ±{session.current_fix['accuracy']:.0f} m"))

        diff = session.calculate_ip_gps_diff()
        if diff is not None:
            emit(c.amber(f"  IP vs GPS discrepancy: {format_distance(diff)}"))


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
