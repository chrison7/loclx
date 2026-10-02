# Architecture & Technical Data Flow

This document details the software architecture, component relationships, data pipelines, and individual module responsibilities for LOCLX (v2.4.8).

---

## High-Level System Architecture

```
Participant Browser
        |
        | HTTPS
        v
Reverse Proxy / Cloudflare Tunnel
        |
        v
127.0.0.1:<port>
        |
        v
LOCLX Server (server.py)
        |
        +-- Session Manager (sessions.py)
        +-- Browser Metadata Parser (browser.py)
        +-- GPS Processor (gps.py)
        +-- IP Intelligence Engine (ipinfo.py)
        +-- Ephemeral Storage (storage.py)
        +-- Security Guard (security.py)
        |
        v
Operator Dashboard (dashboard.py) / Terminal CLI (cli.py)
```

---

## End-to-End Data Flow

1. **Session Creation:** Operator executes `loclx start` or creates a session via CLI (`cli.py`). The `SessionManager` (`sessions.py`) generates a unique session ID (`LX-XXXXXX`) and initializes a `Session` record with a default 30-minute TTL.
2. **Participant Page Access:** Participant navigates to `/session/LX-XXXXXX` over HTTPS via Cloudflare Tunnel or reverse proxy. The request hits `server.py` on `127.0.0.1`.
3. **Metadata & IP Ingestion:**
   - `server.py` extracts the participant's IP address (via `security.py`'s `extract_client_ip`).
   - `ipinfo.py` queries IP geolocation services (`ipwho.is` or `ipapi.co`) to obtain approximate location, ISP, ASN, and country data.
   - `browser.py` parses User-Agent headers, screen metrics, timezone, CPU cores, and language.
4. **Consent-Gated Geolocation:** Participant clicks "Continue" on the landing page (`index.html` + `app.js`), triggering native `navigator.geolocation.watchPosition` with high accuracy enabled.
5. **GPS Payload Processing:** `app.js` sends coordinates to `/api/session/LX-XXXXXX/report`.
   - `security.py` validates body size (<= 64KB), rate limits, session ID format, and coordinate ranges.
   - `gps.py` calculates Haversine distance from previous fixes, computes compass bearings, formats accuracy, and assigns quality tiers (`HIGH`, `GOOD`, `MODERATE`, `LOW`, `COARSE`).
   - `storage.py` appends the GPS fix to the session's in-memory history log (up to 500 items) and updates `best_fix`.
6. **Dashboard Visualization:** Operator opens `/dashboard/LX-XXXXXX`. `dashboard.py` and `web/dashboard.js` render Leaflet map markers for GPS and IP locations, draw the movement polyline, and display real-time telemetry.

---

## Production Python Modules (`src/loclx/`)

### `cli.py`
- **Role:** Terminal CLI controller and argument parser.
- **Responsibilities:** Configures argument parsing for all subcommands (`start`, `listen`, `session`, `target`, `gps`, `ip`, `browser`, `history`, `map`, `earth`, `report`, `live`, `qr`, `info`, `export`, `dashboard`, `diagnostics`, `config`). Coordinates server launching, TTY output rendering, and ANSI formatting.

### `server.py`
- **Role:** Core HTTP server and request router.
- **Responsibilities:** Implements `ThreadingHTTPServer` bound to `127.0.0.1`. Routes requests to participant landing pages, static web assets, session APIs, and operator dashboard endpoints. Handles `X-Forwarded-*` header parsing and public URL resolution.

### `sessions.py`
- **Role:** Ephemeral session lifecycle engine.
- **Responsibilities:** Defines `Session` dataclass and `SessionManager`. Handles session creation, lookup, connection tracking, TTL expiration pruning, and active session listing.

### `browser.py`
- **Role:** Browser telemetry and User-Agent parser.
- **Responsibilities:** Extracts OS, browser family, screen resolution, DPR, hardware concurrency, language, and client metadata from headers and JSON payloads.

### `gps.py`
- **Role:** GPS coordinate processor and mathematical engine.
- **Responsibilities:** Validates coordinate bounds, executes Haversine distance calculations (in meters/kilometers), calculates compass bearings, formats accuracy strings, generates map URLs (Google Maps, OpenStreetMap, Google Earth), and classifies GPS quality levels (`HIGH` through `COARSE`).

### `ipinfo.py`
- **Role:** IP geolocation and intelligence provider.
- **Responsibilities:** Queries external IP intelligence APIs (`ipwho.is` primary, `ipapi.co` fallback) to fetch ASN, ISP, country, city, postal code, timezone, and network coordinates.

### `storage.py`
- **Role:** In-memory GPS history and state store.
- **Responsibilities:** Manages bounded circular history storage per session (`LOCLX_MAX_HISTORY`, default: 500). Tracks and updates `best_fix` based on smallest accuracy radius.

### `security.py`
- **Role:** Security guard, rate limiter, and input sanitizer.
- **Responsibilities:** Enforces 64KB request body limits, 100 req/min rate limits per IP (`RateLimiter`), session ID regex matching (`LX-[A-F0-9]{6}`), coordinate range verification, HTML escaping (`sanitize_input`), and trusted proxy header extraction.

### `dashboard.py`
- **Role:** Operator dashboard backend and telemetry provider.
- **Responsibilities:** Serves `web/dashboard.html` and responds to dashboard API requests for session telemetry, live GPS coordinates, IP locations, movement history, and diagnostic status.

### `diagnostics.py`
- **Role:** System health check runner.
- **Responsibilities:** Executes diagnostic checks across Python version, OS platform, loopback binding, port availability, web asset presence, session manager status, IP provider reachability, browser auto-launch policy, and security safeguards.

### `qrcode.py`
- **Role:** Terminal ASCII QR code generator.
- **Responsibilities:** Generates high-contrast ASCII QR codes directly in TTY for session URLs.

### `tunnel.py`
- **Role:** Cloudflare quick tunnel helper.
- **Responsibilities:** Spawns `cloudflared` background process for `--tunnel` flag, monitors tunnel stdout non-blockingly, extracts public HTTPS URL (`*.trycloudflare.com`), and manages tunnel process cleanup.

### `utils.py`
- **Role:** Output formatting and stream utility helper.
- **Responsibilities:** Configures UTF-8 stdio, handles ANSI color wrapping, thread-safe stdout writing (`emit`), and formats distance and uptime strings.
