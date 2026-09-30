# Changelog


## v2.4.4

Major UI upgrade replacing the centered participant card with a mobile-first, responsive chat/messaging interface.

### Added / Changed
- **Mobile-First Chat Interface**: Redesigned participant landing page into a clean, modern messaging interface (`Browser Information`) complete with header avatar, online indicator, and message bubbles.
- **Sequential Information Disclosures**: Formatted disclosures as clean message bubbles detailing demo scope and optional consent-based location access.
- **Action-Driven Flow**: Added prominent `[ Continue ]` button that transitions to checking browser capabilities before requesting location permission.
- **Dynamic Outcome Bubbles**: Renders result bubbles (`"Location information was received."`, `"Location access was not granted."`, or `"Location information is currently unavailable."`).
- **Mobile Responsive Design**: 100% viewport height, responsive breakpoints (360px–1366px), safe-area padding for mobile browsers, and centered desktop card wrapper.

## v2.4.3


Major release adding public Nginx reverse proxy support, public capture URL configuration, proxy header handling, public/admin route separation, improved GPS accuracy acquisition & best-fix strategy, and clean participant UI.

### Fixed / Added
- **Public Nginx Reverse Proxy Support**: Added configuration support (`LOCLX_PUBLIC_URL` / `--public-url` / `--tunnel`) for running LOCLX behind operator-controlled Nginx proxies while keeping local bind fixed at `127.0.0.1:8765`.
- **Public URL Validation**: Strict URL scheme (`https://` required for remote hosts, `http://localhost` allowed for dev) and trailing slash normalization.
- **Trusted Proxy Forwarded IP Extraction**: Extracts client real IP from `X-Real-IP` and `X-Forwarded-For` when request comes from local loopback proxy (`127.0.0.1` / `::1`), preventing IP spoofing.
- **Public & Admin Route Separation**: Restricts reverse-proxied traffic strictly to participant routes (`/`, `/index.html`, `/app.js`, `/style.css`, `/session/<sid>`, `/report`, `/api/session/<sid>/location`), blocking administrative/dashboard endpoints with HTTP 403 Forbidden.
- **Robust GPS Acquisition Strategy**: Uses `getCurrentPosition` and `watchPosition` with `{ enableHighAccuracy: true, timeout: 30000, maximumAge: 0 }`.
- **Best-Fix Tracking & Improvement Deltas**: Selects lowest accuracy value (`best_fix`), logs improvement deltas (`Accuracy: ±25000 m → ±850 m`), and synchronizes all map links (`Google Maps`, `Google Earth`, `OpenStreetMap`) exclusively to `session.best_fix`.
- **Honest Accuracy Labeling & Coarse Fix Policy**: Classifies fixes into `HIGH` (<= 25m), `GOOD` (<= 100m), `MODERATE` (<= 1000m), `LOW` (<= 10000m), and `COARSE` (> 10000m). Labels coarse fixes accurately without claiming exactness or false reverse-geocoding.
- **Clean Participant Landing UI**: Neutral participant status messaging (`"Processing..."`, `"Location information received."`, `"Location access was not granted."`) removing yellow warnings and persistent status text.
- **Terminal Startup Differentiation**: Clearly distinguishes `[+] Internal address:` (`127.0.0.1:<port>`) and `[+] Public Capture URL:` or `[+] Local Capture URL:`.

## v2.4.2


Maintenance and feature release introducing best GPS fix accuracy tracking, BrokenPipe handling, and explicit root capture URL display.

### Fixed / Added
- **Explicit Capture URL Display**: Immediately displays `[+] Capture URL:` (e.g. `http://127.0.0.1:<bound_port>/`) derived dynamically from actual bound socket port upon server startup.
- **BrokenPipe & Disconnect Safety**: Added exception handlers wrapping socket writes to safely absorb `BrokenPipeError` and `ConnectionResetError` without emitting Python tracebacks.
- **Favicon & Static Asset Handling**: Explicitly handles `/favicon.ico` returning `204 No Content` and guarantees `200 OK` for static assets (`/`, `/index.html`, `/app.js`, `/style.css`).
- **Best GPS Fix Selection**: Tracks and selects the highest-accuracy GPS fix (`best_fix`), logging `[+] BETTER GPS FIX` when accuracy improves (e.g. `±25000 m → ±18 m`).
- **Map Links Synchronization**: Generated Google Maps, Google Earth, and OpenStreetMap URLs always synchronize with the best available GPS fix coordinates.
- **GPS Quality Classification**: Categorizes GPS accuracy into `HIGH` (<= 25m), `GOOD` (<= 100m), `MODERATE` (<= 1000m), `LOW` (<= 10000m), or `COARSE` (> 10000m).

Major architecture update separating the Operator Terminal and Participant Browser Page into clean, distinct interfaces.

### Added / Changed
- **Redesigned Participant Landing Page**: Replaced terminal-style participant page with a clean, professional, mobile-first neutral web page ("Browser Information Demo") with transparent disclosure and `[ Start Demo ]` button.
- **Operator Terminal Refinement**: Removed dashboard links and local session URL clutter from default startup output; primary focus on listener state and target intelligence stream.
- **Internal Session Architecture**: Preserved session isolation, random session tokens (`LX-XXXXXX`), request validation, rate limiting, and expiration while hiding session complexity from participants.
- **Clean Geolocation Error Handling**: Handled `PERMISSION_DENIED`, `POSITION_UNAVAILABLE`, and `TIMEOUT` with clear, non-repetitive participant feedback.

Major release transforming the default user experience into a streamlined, Hound-style terminal capture workflow while maintaining internal session isolation and token security.

### Added / Changed
- **Hound-Style Stream Workflow**: Default execution (`./loclx`) removes the interactive main menu and directly starts the listener, outputs local/tunnel URLs, enters live target waiting state, and streams connection events and GPS fixes directly.
- **Optional Tunnel Integration**: Added `--tunnel` option to easily configure public lab domains while keeping tunnel auth credentials isolated.
- **Direct Target Connection & Report Streaming**: Automatically renders Target Information, Device/Browser parameters, Permission-granted GPS fixes, Map links, and Compact Information Reports upon target connection.
- **Live GPS Watch Updates**: Continuous position tracking with `watchPosition()` rendering live update lines directly to console.
- **Direct Dashboard Links**: Dashboard printed per capture link (`/dashboard/<TOKEN>`) featuring map controls, IP marker, and IP-to-GPS connection line.

Major release introducing Advanced Location Intelligence, 3D Google Earth Visualization, GeoURI mapping integration, directional bearing calculation, and enhanced location analysis.

### Added
- **Advanced Map & Earth Intelligence**: Expanded mapping capabilities with dedicated `loclx map <SESSION_ID>` and `loclx earth <SESSION_ID>` subcommands for high-precision GPS and IP coordinates.
- **GeoURI Integration**: Generates standardized `geo:lat,lon?z=16` URIs for native Linux GIS applications and mobile mapping.
- **Directional Bearing & Heading Analysis**: Calculates compass bearing (0-360°) and cardinal direction (e.g., `45° NE`) between IP estimate and browser GPS fix.
- **Google Earth 3D Visualization**: Dedicated 3D location view generator (`loclx earth <SESSION_ID>`) providing direct search URLs for Google Earth Web and desktop GIS software.
- **Enhanced Target Intelligence Reports**: Integrated GeoURI and compass bearing metrics into `loclx report <SESSION_ID>` target intelligence summaries.

## v2.2.0

Major release hardening session security, session isolation, multi-session workflow, and terminal target handling.

## v2.1.2

Session-centric terminal OSINT workflow release inspired by information-gathering tools.

## v2.1.1

Important bugfix release establishing a strict **terminal-first** architecture.

## v2.1.0

Major release transforming LOCLX into a professional Linux security & OSINT laboratory tool.

## v2.0.0

Major architecture upgrade transforming LOCLX into an advanced consent-based Linux security & OSINT laboratory tool.

## v1.0.1

Documentation and security policy release.

## v1.0.0

First release of LOCLX localhost demonstration.
