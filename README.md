# LOCLX — Live Location & Information eXtractor

```
========================================================
                     LOCLX
              Location Intelligence
                      v2.4.6
========================================================

LOCLX - Authorized Security Testing Tool

[+] Listener started
[+] Internal address:
    127.0.0.1:8765

[+] Public Capture URL:
    https://YOUR_DOMAIN/

[*] Waiting for connection...
[*] Press Ctrl+C to stop.
```

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Parrot%20OS%20%7C%20Kali%20Linux%20%7C%20macOS%20%7C%20WSL-lightgrey.svg)]()

LOCLX (Live Location & Information eXtractor) v2.4.6 is a professional Linux security and OSINT laboratory tool featuring a dual-interface architecture:
1. **Operator Terminal**: Primary intelligence controller displaying listener status, real-time target connection events, device metadata, consent-based GPS fixes, map links, and live location streams.
2. **Browser Participant Landing Page**: Modern, responsive, mobile-first chat/messaging interface ("Browser Information Demo") that presents information disclosures as message bubbles and requests location permission exclusively via standard browser Geolocation API prompts.

Designed for security researchers, privacy advocates, educators, and penetration testing laboratories operating on Kali Linux, Parrot OS, Ubuntu, Debian, Termux, WSL, and macOS.

---

## Architecture & Workflow

```
OPERATOR TERMINAL                  PARTICIPANT CHAT WEBPAGE
-----------------                  ------------------------

./loclx
   │
Listener Started                   Browser Information Chat
   │                                           │
Waiting for connection                     [ Continue ]
   │                                           │
Target Connected ─────────────── Native Browser Permission Prompt
   │                                           │
Browser Metadata                               │
   │                                     Allow / Deny
Location Received ◄───────────────────────────┘
   │
Map & Earth Links
```


---

## Key Features

- **Terminal-First Execution**: Zero automatic browser launching. Local server URLs (`http://127.0.0.1:8765/session/<SESSION_ID>`) are printed for manual access.
- **Session-Centric Routing**: Dedicated collection routes per session (`/session/<SESSION_ID>`, `/dashboard/<SESSION_ID>`, `/api/session/<SESSION_ID>/report`).
- **Target Connection Events**: Real-time console notifications when a browser client connects to a session URL.
- **Hound-Style Intelligence Reports**: Comprehensive terminal report generator (`loclx report <ID>`) aggregating Session, Device/Browser, Network, IP Location, GPS Location, Map Links, and Discrepancy Analysis.
- **Consent-Based High-Accuracy GPS**: Browser Geolocation API (`enableHighAccuracy: true`) requesting explicit user permission grant before capturing coordinates, altitude, speed, and heading.
- **IP Intelligence Engine**: Pluggable provider architecture (`IPWhoIs`, `IPApi`) extracting ASN, ISP, country, region, city, postal code, timezone, and reverse DNS.
- **Haversine Distance Analysis**: Real-time discrepancy calculation between network IP estimates and browser GPS fixes (`delta_km`).
- **Interactive Security Dashboard**: Real-time dark UI dashboard featuring live position tracking, accuracy radius indicator, movement trail, location discrepancy interpretation, and session history management.
- **Terminal CLI & ANSI Dashboard**: High-fidelity TTY interface with grouped menu structure, terminal width detection, ASCII QR code rendering, and live update logs.
- **Diagnostics & Config Utility**: Integrated `loclx diagnostics` environment runner and `loclx config` viewer.
- **Security & Privacy Safeguards**: Fixed local bind (`127.0.0.1`), security HTTP headers (CSP, X-Content-Type-Options), rate limiting, request size limits, zero credential theft, and bounded ephemeral session memory.

---

## Architecture & Location Data Integrity

LOCLX processes location data exclusively through standard browser permission APIs:

```
LOCLX SERVER (127.0.0.1:8765)
     ▲
     │ receives actual browser GPS payload
REMOTE BROWSER
     ▲
     │ requests explicit user permission via Geolocation API
REMOTE DEVICE'S LOCATION PROVIDER (GPS / Wi-Fi / Cell)
```

### Strict Location Principles
1. **Zero Fabrication**: LOCLX strictly displays the coordinates reported by the client browser. Coordinates are never altered, mathematically "corrected", or inferred from IP geolocation.
2. **GPS vs. Network Separation**: Browser GPS data (`gps.latitude`, `gps.longitude`, `gps.accuracy`) and Network IP geolocation data (`ip_location.latitude`, `ip_location.longitude`, `ip_location.accuracy`) are stored and rendered completely separately. Map links are generated exclusively from `session.best_fix`.
3. **Honest Quality Labeling**: Accuracy is classified into `HIGH` ($\le 25\text{ m}$), `GOOD` ($\le 100\text{ m}$), `MODERATE` ($\le 1000\text{ m}$), `LOW` ($\le 10000\text{ m}$), or `COARSE` ($> 10000\text{ m}$). Coarse fixes are explicitly labeled `COARSE BROWSER FIX` and are never misrepresented as exact.

---

## Parrot OS & Virtual Machine Testing Note

> When testing LOCLX inside a virtual machine (such as Parrot OS VM or Kali Linux VM), the VM browser may not have access to physical GPS hardware or host OS location services.

In a VM environment, browsers typically fall back to network-based positioning, returning coarse accuracy (e.g., $\pm 25\text{ km}$). This is an expected environment constraint of virtualized hardware, not a software defect or coordinate error. To test high-accuracy GPS ($\le 25\text{ m}$), run the participant browser on a physical mobile device or hardware with native location services enabled.

---

## Public Deployment & Nginx Reverse Proxy

LOCLX binds strictly to local loopback (`127.0.0.1:8765`) by design. Public exposure must happen through an operator-controlled reverse proxy or secure tunnel.

```
Internet ──> HTTPS (https://example.com) ──> Nginx ──> 127.0.0.1:8765 ──> LOCLX
```

### 1. Nginx Reverse Proxy Configuration
Create `/etc/nginx/sites-available/loclx`:
```nginx
server {
    listen 443 ssl;
    server_name example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8765;

        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_read_timeout 60s;
        proxy_send_timeout 60s;
    }
}
```

### 2. Launching LOCLX with Public Capture URL
```bash
export LOCLX_PUBLIC_URL=https://example.com
./loclx
# Or via CLI flag:
./loclx --public-url https://example.com
```

### 3. Public Networking Requirements
> Simply installing Nginx on a local machine does **NOT** make `127.0.0.1` Internet-accessible by itself.

To make the Nginx reverse proxy publicly reachable over the Internet, one of the following network configurations is required:
- **Public IP + DNS**: A public IP address with DNS records pointing to your domain and port 443 forwarded in your router/firewall.
- **Public VPS Proxy**: A public Cloud/VPS server running Nginx with a secure tunnel back to your local LOCLX service.
### 4. Cloudflare Quick Tunnel Mode
```bash
./loclx --tunnel
```
When `./loclx --tunnel` is executed:
1. Verifies `cloudflared` is installed locally.
2. Binds LOCLX internally to `127.0.0.1:8765`.
3. Starts an authorized Cloudflare quick tunnel pointing to `http://127.0.0.1:8765`.
4. Parses and displays the generated HTTPS capture URL (e.g. `https://xxxx.trycloudflare.com/`).



## Startup Output Example

```
╔════════════════════════════════════════════════════════════╗
║                         LOCLX                              ║
║     LIVE LOCATION & INFORMATION eXTRACTOR                  ║
║                         v2.3.0                             ║
╚════════════════════════════════════════════════════════════╝

[+] LISTENER
    127.0.0.1:8765

[+] STATUS
    WAITING FOR SESSION (LX-83A91F)

[*] Local collection URL : http://127.0.0.1:8765/session/LX-83A91F
[*] Dashboard URL        : http://127.0.0.1:8765/dashboard/LX-83A91F
[*] Browser auto-launch   : DISABLED (Terminal-First)
```

---

## Interactive Menu & Terminal UI

```
  LOCLX MAIN MENU
  ──────────────────────────────────────────────

  SESSION
   [1] Create Session
   [2] List Sessions
   [3] Session Information
   [4] Stop Session

  INFORMATION
   [5] Target Information
   [6] GPS Information
   [7] IP Intelligence
   [8] Browser Information

  ANALYSIS
   [9] Location Comparison
   [10] Location History
   [11] Map / Earth Links

  TOOLS
   [12] Generate Report
   [13] Export Session
   [14] QR Code
   [15] Diagnostics

   [0] Exit
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
loclx listen                          # Start server listener
loclx session create                  # Create a new session LX-XXXXXX
loclx session list                    # List active sessions
loclx session info LX-XXXXXX          # Display session details
loclx session stop LX-XXXXXX          # Stop specified session
loclx target LX-XXXXXX                 # Display target GPS fix details
loclx gps LX-XXXXXX                    # Display high-accuracy GPS fix info
loclx ip LX-XXXXXX                     # Display network IP intelligence
loclx browser LX-XXXXXX                # Display browser metrics
loclx history LX-XXXXXX                # View location history log
loclx map LX-XXXXXX                    # Display external map & Earth URLs
loclx report LX-XXXXXX                 # Generate Hound-style target intelligence report
loclx export LX-XXXXXX --format csv   # Export history to CSV or JSON
loclx diagnostics                     # Run environment health checks
loclx config                          # Display effective configuration
loclx qr LX-XXXXXX                     # Render ASCII QR code for session URL
loclx --lab                           # Educational lab mode
loclx --version                       # Display version information
loclx --help                          # Display command help
```

---

## Target Information Report Example (`loclx report`)

```
LOCLX — TARGET INFORMATION
══════════════════════════════════════════════

SESSION
──────────────────────────────────────────────
ID              LX-83A91F
STATUS          ACTIVE
FIRST SEEN      08:15:22
LAST SEEN       08:18:41
UPDATES         18

DEVICE / BROWSER
──────────────────────────────────────────────
Browser         Firefox
Browser Version 124.0
Platform        Linux
User Agent      Mozilla/5.0...
Language        en-US
Timezone        Asia/Kolkata
Screen          1920x1080
Viewport        1920x947
CPU Cores       8
DPR             1
Touch           Supported
Device Type     Desktop

NETWORK
──────────────────────────────────────────────
Public IP       xxx.xxx.xxx.xxx
Country         India
Region          Kerala
City            Ernakulam
ISP             BSNL
Organization    BSNL
ASN             AS9829
Reverse DNS     —

IP LOCATION
──────────────────────────────────────────────
Latitude        10.120000
Longitude       76.100000
Precision       APPROXIMATE

GPS LOCATION
──────────────────────────────────────────────
Latitude        10.123456789
Longitude       76.123456789
Accuracy        ±7 m
Altitude        32 m
Speed           0.2 m/s
Heading         181°
Timestamp       08:18:41

MAP LINKS
──────────────────────────────────────────────
Google Maps     https://www.google.com/maps/search/?api=1&query=10.123456789,76.123456789
Google Earth    https://earth.google.com/web/search/10.123456789,76.123456789
OpenStreetMap   https://www.openstreetmap.org/?mlat=10.123457&mlon=76.123457#map=16/10.123457/76.123457

ANALYSIS
──────────────────────────────────────────────
GPS → IP        12.4 km
GPS precision   BROWSER REPORTED
IP precision    APPROXIMATE
══════════════════════════════════════════════
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
