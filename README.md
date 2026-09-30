# LOCLX — Live Location & Information eXtractor

```
╔════════════════════════════════════════════════════════════╗
║                         LOCLX                              ║
║       Live Location & Information eXtractor                ║
║                         v2.1.1                             ║
╚════════════════════════════════════════════════════════════╝
```

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Parrot%20OS%20%7C%20Kali%20Linux%20%7C%20macOS%20%7C%20WSL-lightgrey.svg)]()

LOCLX (Live Location & Information eXtractor) v2.1.1 is a terminal-first, consent-based Linux security and OSINT laboratory tool. It demonstrates the technical boundary between approximate IP-derived network intelligence and precise, user-permissioned browser GPS coordinates.

Designed for security researchers, privacy advocates, educators, and penetration testing laboratories operating on Kali Linux, Parrot OS, Ubuntu, Debian, Termux, WSL, and macOS.

---

## Terminal-First Architecture

LOCLX is **100% terminal-first**. Running `./loclx` or executing any subcommand **NEVER** automatically launches a web browser. The local HTTP server starts, prints the server and dashboard loopback URLs, and remains listening in the terminal while you manually navigate to the URL when desired.

---

## Key Features

- **Terminal-First Execution**: Zero automatic browser launching. Server URLs are printed to console for manual access.
- **Consent-Based GPS Laboratory**: Implements `navigator.geolocation.getCurrentPosition()` and `navigator.geolocation.watchPosition()` requiring explicit user click interaction.
- **Session Engine System**: Non-predictable `LX-XXXXXX` session tokens, 30-minute auto-expiration (`LOCLX_SESSION_TTL`), and full session lifecycle control (`start`, `listen`, `session list`, `session info`, `session stop`).
- **IP Intelligence Engine**: Pluggable provider architecture (`IPWhoIs`, `IPApi`) extracting ASN, ISP, country, region, city, postal code, timezone, and approximate coordinates.
- **Haversine Distance Analysis**: Real-time discrepancy calculation between network IP estimates and browser GPS fixes (`delta_km`).
- **Browser Metrics Inspection**: Captures standard client capabilities (User-Agent, Platform, Screen resolution, Viewport, DPR, CPU cores, timezone, language, color depth, touch support, online status, device type).
- **Interactive Security Dashboard**: Real-time dark UI dashboard featuring live position tracking, accuracy radius indicator, movement trail, location discrepancy interpretation, and session history management.
- **Terminal CLI & ANSI Dashboard**: High-fidelity TTY interface with grouped menu structure, terminal width detection, ASCII QR code rendering, and live update logs.
- **Diagnostics & Config Utility**: Integrated `loclx diagnostics` environment runner and `loclx config` viewer.
- **Security & Privacy Safeguards**: Fixed local bind (`127.0.0.1`), security HTTP headers (CSP, X-Content-Type-Options), rate limiting, request size limits, zero credential theft, and bounded ephemeral session memory.

---

## Startup Output Example

```
╔════════════════════════════════════════════════════════════╗
║                         LOCLX                              ║
║       Live Location & Information eXtractor                ║
║                         v2.1.1                             ║
╚════════════════════════════════════════════════════════════╝

[+] LOCLX SERVER
    Bind      : 127.0.0.1
    Port      : 8765
    Status    : LISTENING

[+] Local URL:
    http://127.0.0.1:8765/

[+] Dashboard:
    http://127.0.0.1:8765/dashboard

[*] Browser auto-launch: DISABLED
[*] Open the URL manually when required.

LOCLX >
```

---

## Interactive Menu & Terminal UI

```
╔════════════════════════════════════════════════════════════╗
║                         LOCLX                              ║
║          Live Location & Information eXtractor             ║
║                         v2.1.1                             ║
╚════════════════════════════════════════════════════════════╝

  SESSION
  ──────────────────────────────────────────────────────────
  [1]  Start New Session
  [2]  Active Sessions
  [3]  Session Information
  [4]  Stop Session

  ANALYSIS
  ──────────────────────────────────────────────────────────
  [5]  Live Dashboard URL
  [6]  GPS / Target Fix
  [7]  IP Intelligence
  [8]  Browser Information
  [9]  Location History

  TOOLS
  ──────────────────────────────────────────────────────────
  [10] Export Session
  [11] QR Code
  [12] External Map Links
  [13] Diagnostics
  [14] Configuration

  [0]  Exit
```

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

## Usage & Subcommands

LOCLX supports both an interactive terminal menu and standard CLI subcommands:

```bash
# Interactive TTY menu
loclx

# Subcommands
loclx start                           # Start server and create session
loclx listen                          # Start server and listen for incoming GPS updates
loclx session list                    # List active sessions
loclx session info LX-XXXXXX          # Display session details
loclx session stop LX-XXXXXX          # Stop specified session
loclx dashboard                       # Print live dashboard URL
loclx target                          # Show target GPS fix details
loclx gps                             # Display GPS fix info
loclx ip                              # Display network IP intelligence
loclx browser                         # Display browser metrics
loclx history                         # View location history log
loclx map                             # Print external map URLs
loclx export LX-XXXXXX --format csv   # Export history to CSV or JSON
loclx diagnostics                     # Run environment health checks
loclx config                          # Display effective configuration
loclx qr                              # Render terminal ASCII QR code
loclx --lab                           # Educational lab mode
loclx --version                       # Display version information
loclx --help                          # Display command help
```

---

## Documentation

- [CLI Reference](docs/cli.md)
- [Dashboard Guide](docs/dashboard.md)
- [Configuration Reference](docs/configuration.md)
- [Troubleshooting Guide](docs/troubleshooting.md)
- [Architecture Overview](docs/architecture.md)
- [GPS & Mathematics](docs/gps.md)
- [IP Geolocation Intelligence](docs/ip-geolocation.md)
- [Browser Permissions Model](docs/browser-permissions.md)
- [Security Safeguards](docs/security.md)

---

## Testing

Run the full automated test suite:

```bash
python -m unittest discover -s tests -v
```

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
