# Command Line Interface (CLI) Reference

This document is the complete CLI reference for LOCLX (v2.4.8).

---

## Global Usage & Options

```
loclx [-h] [--version] [--port INT] [--public-url PUBLIC_URL] [--tunnel-url TUNNEL_URL] [--tunnel] [--debug] [--lab] COMMAND
```

| Flag | Description |
| :--- | :--- |
| `-h, --help` | Show CLI help message and exit. |
| `--version` | Display LOCLX version (`2.4.8`). |
| `--port INT` | Set preferred HTTP listener port on `127.0.0.1` (default: `8765`). |
| `--public-url PUBLIC_URL` | Set public HTTPS reverse proxy capture URL (e.g. `https://custom-domain.example.com`). |
| `--tunnel-url TUNNEL_URL` | Set manually configured public tunnel capture URL. |
| `--tunnel` | Boolean flag to launch automated Cloudflare quick tunnel (`loclx start --tunnel` or `loclx --tunnel start`). |
| `--debug` | Enable verbose debug logging. |
| `--lab` | Run self-contained local educational demonstration mode. |

---

## Subcommands Reference

### Server Commands

- `loclx start`
  - Starts the HTTP server listener on `127.0.0.1:<port>` and creates an initial active session (`LX-XXXXXX`).
  - Supports `--tunnel`, `--public-url`, and `--tunnel-url` flags.
- `loclx start --tunnel`
  - Starts the HTTP server listener and automatically launches a Cloudflare quick tunnel to obtain a public HTTPS URL (`https://*.trycloudflare.com`).
- `loclx start --public-url https://example.com`
  - Starts the HTTP server listener with a pre-configured public HTTPS reverse proxy URL.

- `loclx listen`
  - Starts the HTTP server listener without creating an initial session. Sessions can be created on-demand via CLI.

---

### Session Management

- `loclx session`
  - Manage in-memory sessions.
  - Subcommands:
    - `loclx session create`: Create a new session.
    - `loclx session list`: List active/in-memory sessions.
    - `loclx session info [ID]`: Display detailed information for a specific session.
    - `loclx session stop [ID]`: Stop a specific session.

---

### Session Information & Target Intelligence

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

- `loclx map [ID]`
  - Generate mapping URLs (Google Maps, OpenStreetMap, GeoURI) for the session's best GPS fix.

- `loclx earth [ID]`
  - Generate Google Earth 3D location URL for the session's best GPS fix.

- `loclx report [ID]`
  - Print a complete intelligence report aggregating session overview, target connection metrics, browser environment data, network IP geolocation, GPS location data, map deep links, and distance discrepancy analysis.

- `loclx live [ID]`
  - Attach to live location update stream in terminal TTY.

- `loclx qr [ID]`
  - Render high-contrast ASCII QR code in TTY for the session capture URL.

- `loclx info [ID]`
  - Display session summary.

---

### Export, Dashboard & Utility Commands

- `loclx export [ID] [--format {json,csv}]`
  - Export session GPS history and telemetry data to JSON or CSV format.

- `loclx dashboard [ID]`
  - Print live dashboard URL (`http://127.0.0.1:<port>/dashboard/<SESSION_ID>`).

- `loclx diagnostics`
  - Run automated system health, network, asset, and security policy checks.

- `loclx config`
  - Display effective runtime configuration parameters and environment variables.
