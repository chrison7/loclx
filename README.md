# LOCLX — Live Location & Information eXtractor

```
╔══════════════════════════════════════════════╗
║                 LOCLX                        ║
║      Live Location & Information eXtractor   ║
║                 v2.0                         ║
╚══════════════════════════════════════════════╝
```

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20WSL-lightgrey.svg)]()

LOCLX (Live Location & Information eXtractor) v2.0 is an advanced, consent-based Linux security and OSINT laboratory tool. It demonstrates the technical boundary between approximate IP-derived network intelligence and precise, user-permissioned browser GPS coordinates.

Designed for security researchers, privacy advocates, educators, and penetration testing laboratories operating on Kali Linux, Parrot OS, Ubuntu, Debian, Termux, WSL, and macOS.

---

## Key Features

- **Consent-Based GPS Laboratory**: Implements `navigator.geolocation.getCurrentPosition()` and `navigator.geolocation.watchPosition()` requiring explicit user click interaction.
- **Session Management System**: Non-predictable `LX-XXXXXX` session identifiers, automatic expiration timeouts, and full session lifecycle control (`start`, `list`, `show`, `stop`, `delete`).
- **IP Intelligence Engine**: Pluggable provider architecture (`IPWhoIs`, `IPApi`) extracting ASN, ISP, country, region, city, and approximate coordinates.
- **Haversine Distance Analysis**: Real-time discrepancy calculation between network IP estimates and browser GPS fixes (`delta_km`).
- **Browser Metrics Inspection**: Captures standard client capabilities (User-Agent, Platform, Screen resolution, DPR, CPU cores, timezone, language).
- **Interactive Security Dashboard**: Real-time dark UI dashboard featuring live position tracking, accuracy radius indicator, movement trail, and session history management.
- **ANSI Terminal Interface & Dashboard**: High-fidelity TTY interface with colorized status indicators and real-time live update logs.
- **Security & Privacy Safeguards**: Fixed local bind (`127.0.0.1`), rate limiting, request size limits, zero credential theft, and ephemeral session memory.

---

## Architecture

```
LOCLX Architecture
──────────────────────────────────────────────────────────────────
Terminal CLI (loclx) ──► Session Manager ──► HTTP API (127.0.0.1)
                              │                     │
                              ▼                     ▼
                        Session Storage      Web Lab & Dashboard
                       (JSON/CSV Export)     (Leaflet Map & GPS)
```

For detailed architectural specifications, see [docs/architecture.md](docs/architecture.md).

---

## Installation

LOCLX relies strictly on the Python 3.9+ standard library. Zero external Python packages are required.

### Method 1: Direct Execution (Linux / macOS / WSL)
```bash
git clone https://github.com/chrison7/loclx.git
cd loclx
chmod +x loclx
./loclx
```

### Method 2: System-Wide Packaging
```bash
# Install via pipx (recommended)
pipx install .

# Or install via python pip
python -m pip install .
```

---

## Usage & Commands

Run LOCLX to launch the interactive terminal interface:

```bash
loclx
```

### Command Line Options

| Flag | Description |
| :--- | :--- |
| `loclx` | Launch standard TTY menu interface |
| `loclx --port 8765` | Specify custom HTTP server port |
| `loclx --no-browser` | Launch server without automatically opening default browser |
| `loclx --lab` | Launch educational self-contained demonstration mode |
| `loclx --debug` | Enable verbose log output |
| `loclx --version` | Display version information |
| `loclx --help` | Display command line usage and epilog |

---

## GPS Permission Model

The W3C Geolocation API enforces browser and operating system permission boundaries:

1. **No Automatic Prompts**: LOCLX does not request location access upon page load.
2. **User Initiation**: The user must explicitly press `[ Request Location Permission ]`.
3. **Secure Context**: Modern browsers require HTTPS or `localhost` / `127.0.0.1` secure context.

For details, read [docs/browser-permissions.md](docs/browser-permissions.md) and [docs/gps.md](docs/gps.md).

---

## IP Geolocation vs. Exact GPS

IP geolocation maps public IP routing prefixes to ISP hub locations or regional city centroids. It **never** represents exact physical user location.

LOCLX explicitly labels all IP coordinates as **APPROXIMATE** and measures the discrepancy distance against exact GPS coordinates using the Haversine formula:

$$d = 2R \cdot \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)}\right)$$

Read [docs/ip-geolocation.md](docs/ip-geolocation.md) for deeper analysis.

---

## Security & Safeguards Boundary

LOCLX strictly enforces the following security controls:

- **Loopback Only (`127.0.0.1`)**: Fixed local bind address. Cannot be exposed remotely.
- **Zero Stealth Tracking**: No hidden background tracking, covert telemetry, or permission bypasses.
- **No Persistence**: History buffers live strictly in session memory unless manually exported to JSON/CSV.
- **Payload Validation**: Hard limits on request size (64KB) and token-bucket rate limiting.

Read [SECURITY.md](SECURITY.md) and [docs/security.md](docs/security.md).

---

## Testing

Run the full automated test suite (27 unit & guard tests):

```bash
python -m unittest discover -s tests -v
```

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
