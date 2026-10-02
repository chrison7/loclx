# Command Line Interface (CLI) Reference

This document is the complete CLI reference for LOCLX (v2.4.8).

---

## Global Options

```
loclx [-h] [--version] [--port INT] [--public-url PUBLIC_URL] [--tunnel [TUNNEL]] [--debug] [--lab] COMMAND
```

| Flag | Description |
| :--- | :--- |
| `-h, --help` | Show CLI help message and exit. |
| `--version` | Display LOCLX version (`2.4.8`). |
| `--port INT` | Set preferred HTTP listener port on `127.0.0.1` (default: `8765`). |
| `--public-url URL` | Set public HTTPS reverse proxy capture URL (e.g. `https://custom-domain.example.com`). |
| `--tunnel [URL]` | Launch automated Cloudflare quick tunnel or specify existing tunnel URL. |
| `--debug` | Enable verbose debug logging. |
| `--lab` | Run self-contained local educational demonstration mode. |

---

## Subcommands Reference

### Server & Session Initialization

- `loclx start`
  - Starts the HTTP server listener on `127.0.0.1:<port>` and immediately creates a new active session (`LX-XXXXXX`).
  - Supports `--tunnel` and `--public-url` flags.

- `loclx listen`
  - Starts the HTTP server listener without creating an initial session. Sessions can be created on-demand via CLI.

---

### Session Management

- `loclx session`
  - Manage in-memory sessions.
  - Options:
    - `loclx session list`: List all active in-memory sessions, creation time, TTL, and status.
    - `loclx session create`: Manually create a new session ID.
    - `loclx session delete <ID>`: Expire and delete a specific session.
    - `loclx session info <ID>`: Show detailed status for a specific session.

---

### Target Intelligence & Location Data

- `loclx target [ID]`
  - Display target connection status, connected IP address, connection timestamp, and User-Agent summary.

- `loclx gps [ID]`
  - Display current and best GPS fixes for the session, including latitude, longitude, accuracy radius, quality classification (`HIGH`..`COARSE`), altitude, speed, heading, and timestamp.

- `loclx ip [ID]`
  - Display network IP geolocation intelligence: IP address, ISP, ASN, country, region, city, postal code, timezone, and reverse DNS.

- `loclx browser [ID]`
  - Display detailed client browser metrics: User-Agent string, OS, browser engine, screen width/height/DPR, CPU logical cores, system language, and timezone.

- `loclx history [ID]`
  - Display chronological list of historical GPS updates received for the session.

- `loclx report [ID]`
  - Print a complete intelligence report aggregating session overview, target connection metrics, browser environment data, network IP geolocation, GPS location data, map deep links, and distance discrepancy analysis.

- `loclx live [ID]`
  - Attach to live location update stream in terminal TTY.

---

### Mapping & QR Codes

- `loclx map [ID]`
  - Generate mapping URLs (Google Maps, OpenStreetMap, GeoURI) for the session's best GPS fix.

- `loclx earth [ID]`
  - Generate Google Earth Web deep link for the session's best GPS fix.

- `loclx qr [ID]`
  - Render high-contrast ASCII QR code in TTY for the session capture URL.

---

### Export & Utility Commands

- `loclx export [ID]`
  - Export session GPS history and telemetry data to JSON or CSV format.

- `loclx dashboard [ID]`
  - Display live dashboard URL (`http://127.0.0.1:<port>/dashboard/<SESSION_ID>`).

- `loclx diagnostics`
  - Run automated system health, network, asset, and security policy checks.

- `loclx config`
  - Display effective runtime configuration parameters and environment variables.
