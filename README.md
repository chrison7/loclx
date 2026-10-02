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

## Quick Install

Automated PEP 668-safe installation:

```bash
git clone https://github.com/chrison7/loclx.git
cd loclx
./install.sh
source .venv/bin/activate
loclx --version
```

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
- **Integrated Tunneling & Reverse Proxy:** Built-in Cloudflare tunnel helper (`loclx start --tunnel`) and public base URL override (`--public-url`).
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
- **Optional External Tools:** `cloudflared` (required if using `loclx start --tunnel` to launch Cloudflare quick tunnels). Install on Debian/Parrot OS via `sudo apt install cloudflared`.

---

## Installation Methods

### METHOD A — Recommended Development / Source Installation (Script)

Use the provided executable installer to create a isolated virtual environment and install LOCLX in editable mode:

```bash
git clone https://github.com/chrison7/loclx.git
cd loclx
./install.sh
source .venv/bin/activate
loclx --version
```

### METHOD B — Manual Virtual Environment Installation

If installing manually on Parrot OS, Debian, Ubuntu, or macOS, always install inside a virtual environment to adhere to PEP 668:

```bash
git clone https://github.com/chrison7/loclx.git
cd loclx
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
loclx --version
```

> **Note:** If `python3 -m venv` is missing on Debian/Parrot OS, install it using:
> ```bash
> sudo apt update && sudo apt install python3-venv
> ```

### METHOD C — Optional `pipx` Installation

`pipx` installs python packages into isolated application environments:

```bash
sudo apt install pipx
pipx install .
```

---

## Usage

LOCLX provides a clean, terminal-first CLI interface:

```
loclx [-h] [--version] [--port INT] [--public-url PUBLIC_URL] [--tunnel-url TUNNEL_URL] [--tunnel] [--debug] [--lab] COMMAND
```

### Global Options

- `-h, --help` — Show CLI help message and exit.
- `--version` — Display version number (`2.4.8`) and exit.
- `--port INT` — Set preferred HTTP listener port on `127.0.0.1` (default: `8765`).
- `--public-url URL` — Set public HTTPS reverse proxy capture URL (e.g. `https://custom-domain.example.com`).
- `--tunnel-url URL` — Set manually configured public tunnel capture URL.
- `--tunnel` — Boolean flag to automatically launch a Cloudflare quick tunnel.
- `--debug` — Enable verbose debug logging.
- `--lab` — Run self-contained local educational demonstration mode.

---

## CLI Command Reference

### Server Commands

- `loclx start` — Start the local listener and create an initial session.
- `loclx start --tunnel` — Start local listener and automatically create a Cloudflare quick tunnel.
- `loclx start --public-url https://example.com` — Start local listener with custom public HTTPS capture URL.
- `loclx listen` — Start the HTTP listener without creating an initial session.

### Session Management

- `loclx session create` — Create a new session.
- `loclx session list` — List active/in-memory sessions.
- `loclx session info [ID]` — Display session information.
- `loclx session stop [ID]` — Stop a specific session.

### Session Intelligence Commands

- `loclx target [ID]` — Display connected target details and GPS fix status.
- `loclx gps [ID]` — Display current GPS fix data for the session.
- `loclx ip [ID]` — Display network IP geolocation intelligence.
- `loclx browser [ID]` — Display detailed browser & device metrics.
- `loclx history [ID]` — Display historical GPS fix updates.
- `loclx map [ID]` — Display Google Maps, OpenStreetMap, and GeoURI URLs.
- `loclx earth [ID]` — Display Google Earth 3D location URL.
- `loclx report [ID]` — Print complete target intelligence report.
- `loclx live [ID]` — Attach to live location update stream.
- `loclx qr [ID]` — Display an ASCII QR code for the session capture URL.
- `loclx info [ID]` — Display session summary.

### Export, Dashboard & Diagnostics

- `loclx export [ID] [--format {json,csv}]` — Export session location history.
- `loclx dashboard [ID]` — Print the live dashboard URL.
- `loclx diagnostics` — Run system health diagnostics.
- `loclx config` — Display effective configuration.

---

## Cloudflare Quick Tunnel Requirement

The `--tunnel` flag automates Cloudflare quick tunnels targeting `http://127.0.0.1:<port>`.

`cloudflared` must be installed on your system PATH.

Install `cloudflared` on Debian / Parrot OS:
```bash
sudo apt update && sudo apt install cloudflared
```

If `cloudflared` is not installed when running `loclx start --tunnel`, LOCLX outputs:
```
Cloudflare quick tunnel requires cloudflared.
[*] Installation options:
    Debian/Parrot: sudo apt install cloudflared
    Linux:         sudo apt install cloudflared
    macOS:         brew install cloudflared
    Windows:       winget install Cloudflare.cloudflared
```

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

---

## Ephemeral Session Lifecycle

1. **Creation:** A session ID (`LX-XXXXXX`) is generated with a 30-minute default TTL (configurable via `LOCLX_SESSION_TTL`).
2. **Connection:** When a participant opens `/session/LX-XXXXXX`, browser metadata and IP geolocation are recorded.
3. **GPS Updates:** When the participant clicks "Continue" and allows browser location, coordinates are posted to `/api/session/LX-XXXXXX/report`.
4. **Best Fix Tracking:** LOCLX automatically identifies and tracks the fix with the smallest accuracy radius as `best_fix`.
5. **History:** Up to 500 GPS updates per session are maintained in ephemeral memory (`LOCLX_MAX_HISTORY`).
6. **Expiration:** Sessions expire automatically after TTL inactivity or when explicitly stopped via `loclx session stop`.

---

## Diagnostics

Verify system readiness and troubleshoot configuration issues:

```bash
loclx diagnostics
```

---

## Development & Verification

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

## License

This project is licensed under the [MIT License](LICENSE).
