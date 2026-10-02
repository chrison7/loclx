# LOCLX

Live Location & Information eXtractor — Authorized Browser Geolocation & OSINT Laboratory (v2.4.8).

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows%20%7C%20Termux-lightgrey.svg)]()

---

## Overview

LOCLX is an authorized browser-geolocation and OSINT testing laboratory designed for security researchers, penetration testers, educators, and privacy analysts. It provides terminal-driven control, real-time participant connection tracking, ephemeral session management, and interactive dashboard visualizers.

**Core Principles:**
- **Permission-Gated GPS:** Browser GPS collection requires an explicit browser permission grant (`navigator.geolocation`) on the participant landing page.
- **Approximate IP Geolocation:** IP-derived location data is strictly approximate and network-based. IP data is never substituted for GPS or labeled as exact coordinates.
- **Strict Data Separation:** Device-supplied GPS coordinates and network-derived IP estimates are tracked, stored, and displayed completely separately.
- **Zero Fabrication:** LOCLX never fabricates, spoofs, or modifies location coordinates.
- **Loopback Binding Invariant:** The application HTTP listener remains permanently bound to `127.0.0.1` and cannot be configured to listen on external public interfaces.
- **Operator-Controlled Public Proxy:** Remote public access is enabled exclusively through operator-configured reverse proxies or secure tunnels (such as Cloudflare Quick Tunnels or Nginx).

---

## Features

- **Terminal-First Operator Console:** Control sessions, view real-time target connections, render ASCII QR codes, and monitor live GPS streams directly from TTY.
- **Consent-Gated Participant Portal:** Mobile-first participant page with explicit consent flow and browser Geolocation API prompts.
- **Dual-Mode Location Processing:**
  - *Browser GPS:* High-accuracy device position (`enableHighAccuracy: true`, `maximumAge: 0`, `timeout: 60000`).
  - *IP Intelligence:* Network ASN, ISP, country, city, postal code, timezone, and reverse DNS via pluggable providers (`ipwho.is` / `ipapi.co`).
- **Interactive Security Dashboard:** Responsive Leaflet.js visualizer featuring real-time position updates, accuracy radius circle, movement polyline trail, and session telemetry.
- **Haversine Distance Analysis:** Real-time calculation of distance discrepancy (`delta_km`) between IP geolocation estimates and device GPS fixes.
- **Ephemeral Session Engine:** Fully in-memory session store (`LX-XXXXXX`) with configurable TTL (default: 30 minutes) and automatic expiration.
- **Integrated Tunneling & Reverse Proxy:** Built-in Cloudflare tunnel helper (`--tunnel`) and public base URL override (`--public-url`).
- **Comprehensive CLI Diagnostics:** Built-in health checker (`loclx diagnostics`) and effective config viewer (`loclx config`).

---

## Architecture

```
Participant Browser
        |
        | HTTPS
        v
Nginx / Cloudflare Tunnel
        |
        v
127.0.0.1:<port>
        |
        v
LOCLX Server
        |
        +-- Session Manager
        +-- Browser Metadata
        +-- Browser GPS
        +-- IP Intelligence
        +-- In-Memory History
        |
        v
Operator Dashboard / CLI
```

---

## Location Model

LOCLX distinguishes clearly between two distinct location data sources:

### 1. Browser Geolocation (GPS / Radio Triangulation)
- **Permission-Based:** Gated by native browser security prompts. Must be explicitly granted by the user.
- **Device-Supplied:** Derived directly from the target device's GPS hardware, Wi-Fi networks, or cell towers.
- **Precision Metadata:** Includes latitude, longitude, browser-reported accuracy radius in meters, altitude, heading, speed, and timestamp.

### 2. IP Geolocation (Network Intelligence)
- **Approximate & Database-Derived:** Querying ASN and BGP routing databases associated with the participant's outbound IP address.
- **Coarse Resolution:** City or regional accuracy level (typically $\pm 10\text{ km}$ to $\pm 50\text{ km}$).
- **Non-Replacement:** Never used as a fallback for missing GPS coordinates or presented as precise physical position.

---

## Requirements

- **Python:** Version 3.9 or higher (Python 3.9, 3.10, 3.11, 3.12, 3.13, 3.14+).
- **Dependencies:** Standard library only (no external PyPI requirements).
- **Optional External Tools:** `cloudflared` (if using `--tunnel` to launch Cloudflare quick tunnels).

---

## Installation

Install LOCLX directly from the project directory:

```bash
# Clone repository
git clone https://github.com/chrison7/loclx.git
cd loclx

# Install in editable mode
pip install -e .
```

Or run directly without installation using Python module execution:

```bash
python -m loclx.cli --help
```

---

## Usage

LOCLX provides a full set of CLI subcommands and flags:

```
loclx [-h] [--version] [--port INT] [--public-url PUBLIC_URL] [--tunnel [TUNNEL]] [--debug] [--lab] COMMAND
```

### Core Subcommands

- `loclx start`: Start the HTTP listener and immediately create a new session.
- `loclx listen`: Start the HTTP listener without creating an initial session.
- `loclx session [list|create|delete|info]`: Manage active in-memory sessions.
- `loclx target [ID]`: Display connected target details and browser metadata.
- `loclx gps [ID]`: Display current and best GPS fixes for a session.
- `loclx ip [ID]`: Display network IP geolocation intelligence.
- `loclx browser [ID]`: Display detailed browser environment metrics (User-Agent, platform, language, cores, screen).
- `loclx history [ID]`: Print historical GPS fixes for a session.
- `loclx map [ID]`: Generate Google Maps and OpenStreetMap URLs for session coordinates.
- `loclx earth [ID]`: Generate Google Earth Web deep links.
- `loclx report [ID]`: Print a complete intelligence report aggregating all session data.
- `loclx live [ID]`: Monitor live incoming location updates for a session.
- `loclx qr [ID]`: Display an ASCII QR code for the session URL.
- `loclx info [ID]`: Summary view of session status.
- `loclx export [ID]`: Export session history to JSON or CSV.
- `loclx dashboard [ID]`: Display the live dashboard URL (`/dashboard/<SESSION_ID>`).
- `loclx diagnostics`: Run environment, network, and security health checks.
- `loclx config`: Print effective runtime settings and environment variables.

---

## HTTPS / Public Deployment

Modern browsers strictly require a **Secure Context** (`https://` or `http://127.0.0.1`) to enable `navigator.geolocation`. For remote testing over the internet, an operator-controlled reverse proxy or tunnel is required.

```
Internet
  |
 HTTPS
  |
 Nginx / Cloudflare
  |
 127.0.0.1
  |
 LOCLX
```

### Quick Cloudflare Tunnel Integration

Launch an automated Cloudflare quick tunnel directly via CLI:

```bash
loclx start --tunnel
```

Or specify a custom public HTTPS reverse proxy URL:

```bash
loclx start --public-url https://custom-domain.example.com
```

Alternatively set environment variables:

```bash
export LOCLX_PUBLIC_URL="https://custom-domain.example.com"
loclx start
```

> **Security Invariant:** The LOCLX Python application listener remains strictly bound to `127.0.0.1`. Public exposure is handled safely at the reverse proxy / tunnel layer.

---

## GPS Accuracy

LOCLX classifies browser-reported accuracy radii into standardized quality tiers:

| Quality Tier | Accuracy Radius ($r$) | Description |
| :--- | :--- | :--- |
| **HIGH** | $r \le 25\text{ m}$ | Precise hardware GPS or multi-point Wi-Fi fix. |
| **GOOD** | $25\text{ m} < r \le 100\text{ m}$ | Wi-Fi / cell tower triangulation fix. |
| **MODERATE** | $100\text{ m} < r \le 1,000\text{ m}$ | Approximate cell or network-assisted fix. |
| **LOW** | $1,000\text{ m} < r \le 10,000\text{ m}$ | Coarse regional location. |
| **COARSE** | $r > 10,000\text{ m}$ | Low-precision IP/cellular fallback fix. |

*Note:* Laptops, desktop PCs, and virtual machines without dedicated GPS hardware or Wi-Fi scanning capabilities frequently return `COARSE` or `MODERATE` fixes.

---

## Session Lifecycle

1. **Creation:** A session ID (`LX-XXXXXX`) is generated with a 30-minute default TTL (configurable via `LOCLX_SESSION_TTL`).
2. **Connection:** When a participant opens `/session/LX-XXXXXX`, browser metadata and IP geolocation are recorded.
3. **GPS Updates:** When the participant clicks "Continue" and allows browser location, coordinates are posted to `/api/session/LX-XXXXXX/report`.
4. **Best Fix Tracking:** LOCLX automatically identifies and tracks the fix with the smallest accuracy radius as `best_fix`.
5. **History:** Up to 500 GPS updates per session are maintained in ephemeral memory (`LOCLX_MAX_HISTORY`).
6. **Expiration:** Sessions expire automatically after TTL inactivity or when explicitly deleted via `loclx session delete`.

---

## Dashboard

Access the real-time Leaflet dashboard at `http://127.0.0.1:8765/dashboard/<SESSION_ID>`.

Features:
- **Session Overview:** Real-time uptime, connected state, permission state, and update counts.
- **Dual Map Markers:** Separate markers for device GPS fix (blue dot with accuracy circle) and approximate IP location (orange marker).
- **Movement Trail:** Live polyline connecting historical GPS fixes.
- **Discrepancy Analyzer:** Real-time distance comparison between IP location and GPS coordinates.
- **Telemetry Panel:** System health status, rate limiting indicators, and active session details.

---

## Diagnostics

Verify system readiness and troubleshoot configuration issues:

```bash
loclx diagnostics
```

Checks performed:
- Python 3.9+ runtime version
- Operating system environment
- Loopback (`127.0.0.1`) interface availability
- Port availability (default 8765)
- Required web asset files (`index.html`, `dashboard.html`, `app.js`, `dashboard.js`, `style.css`)
- In-memory session manager state
- IP geolocation provider reachability (`ipwho.is`)
- Terminal-first browser auto-launch policy
- Security controls (rate limits, request size limits, loopback invariant)

---

## Security

LOCLX is designed with strict security invariants:
- **Loopback Bound:** Fixed `127.0.0.1` binding preventing unauthorized local network exposure.
- **Session Isolation:** Session tokens are strictly validated (`LX-` + 6 hex chars). Administrative endpoints require local loopback requests.
- **Request Safeguards:** Payload sizes capped at 64 KB; endpoint rate limiting enforced at 100 requests per minute per IP.
- **No Persistence:** Ephemeral in-memory storage only; no database, credentials, or sensitive tokens are stored to disk.

For complete details, review [SECURITY.md](SECURITY.md) and [docs/security.md](docs/security.md).

---

## Development

Run unit tests and verification checks:

```bash
# Execute test suite
python -m unittest discover -s tests -v

# Run bytecode compilation check
python -m compileall src

# Check git diff formatting
git diff --check
```

---

## Project Structure

```
loclx/
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI workflow
├── docs/                        # Technical documentation
│   ├── architecture.md          # Architecture & data flow spec
│   ├── browser-permission-model.md # Canonical browser permission guide
│   ├── cli.md                   # CLI command reference
│   ├── configuration.md         # Environment variables & constants
│   ├── dashboard.md             # Dashboard UI documentation
│   ├── gps.md                   # GPS processing & accuracy tiers
│   ├── https-requirement.md     # Secure context & proxy requirement
│   ├── ip-geolocation.md        # IP intelligence specification
│   ├── ip-vs-gps.md             # GPS vs IP comparison guide
│   ├── security.md              # Technical security controls
│   └── troubleshooting.md       # Diagnostic & troubleshooting guide
├── src/
│   └── loclx/                   # Production Python package
│       ├── __init__.py          # Version & package entry
│       ├── browser.py           # Browser metadata parser
│       ├── cli.py               # CLI interface & argument parser
│       ├── dashboard.py         # Dashboard HTML/API handler
│       ├── diagnostics.py       # Diagnostic engine
│       ├── gps.py               # Haversine, bearing & quality tier calculations
│       ├── ipinfo.py            # IP geolocation provider integration
│       ├── qrcode.py            # ASCII QR code generator
│       ├── security.py          # Security guard & rate limiter
│       ├── server.py            # HTTP request handler & router
│       ├── sessions.py          # In-memory session manager
│       ├── storage.py           # In-memory GPS history store
│       ├── tunnel.py            # Cloudflare tunnel helper
│       └── utils.py             # ANSI formatting & stream utilities
├── tests/                       # Automated test suite
│   ├── test_cli.py
│   ├── test_diagnostics.py
│   ├── test_gps.py
│   ├── test_guard.py
│   ├── test_ipinfo.py
│   ├── test_qrcode.py
│   ├── test_security.py
│   ├── test_server.py
│   ├── test_sessions.py
│   └── test_tunnel.py
├── web/                         # Web participant & dashboard assets
│   ├── app.js                   # Participant Geolocation API handler
│   ├── dashboard.html           # Operator dashboard HTML template
│   ├── dashboard.js             # Operator dashboard Leaflet JS logic
│   ├── index.html               # Participant landing page template
│   └── style.css                # CSS styling rules
├── CHANGELOG.md                 # Version history log
├── CONTRIBUTING.md              # Development & contribution guidelines
├── LICENSE                      # MIT License
├── README.md                    # Project README
├── SECURITY.md                  # GitHub security policy
├── loclx                        # Shell launcher script
└── pyproject.toml               # Package build configuration
```

---

## License

This project is licensed under the [MIT License](LICENSE).
