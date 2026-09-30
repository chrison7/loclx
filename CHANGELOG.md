# Changelog

## v2.4.8

Hardening release introducing dynamic CORS `Origin` reflection for public HTTPS reverse proxy/Cloudflare deployment models, structured geolocation error diagnostics (`PERMISSION_DENIED`, `POSITION_UNAVAILABLE`, `TIMEOUT`), and regression test suite expansion.

### Fixed / Added
- **Public HTTPS CORS Correctness**: Dynamically reflects request `Origin` header when present, enabling public HTTPS session pages to POST location data without CORS policy blocks.
- **Enhanced Location Error Diagnostics**: Distinguishes `PERMISSION_DENIED` (user/browser denied), `POSITION_UNAVAILABLE` (provider unable to fix), and `TIMEOUT` (request timed out) with operator-side diagnostic explanation.
- **Client Geolocation Standards Alignment**: Verified standards-compliant Geolocation API usage (`getCurrentPosition` & `watchPosition`, `enableHighAccuracy: true`, `timeout: 30000`, `maximumAge: 0`).
- **Public Endpoint Security**: Preserved administrative/dashboard route separation (HTTP 403 Forbidden when proxied) and strict session scoping.

## v2.4.7

Major release enforcing mandatory public capture endpoints (configured public Nginx URL or Cloudflare quick tunnel), complete removal of local capture fallback mode, session capture URL formatting (`/session/LX-XXXXXX`), and explicit startup failure when no public endpoint is supplied.

### Fixed / Added
- **Mandatory Public Capture Endpoint**: Default capture mode (`./loclx` or `loclx start`) requires `--public-url`, `LOCLX_PUBLIC_URL`, or `--tunnel`. If unconfigured, startup fails cleanly with exit code 1 and configuration instructions.
- **Removal of Localhost Fallback**: Removed `[+] Local Capture URL:` output in capture mode.
- **Session-Based Public Capture URL**: Generated public capture URL includes the active session route (e.g., `https://example.com/session/LX-ABC123` or `https://XXXX.trycloudflare.com/session/LX-ABC123`).
- **Dynamic Port Forwarding**: Tunnel and reverse proxy forward to actual bound port (`127.0.0.1:<actual-port>`).
- **Nginx Architecture Updates**: Updated `README.md` diagram and documentation reflecting multi-tier Nginx proxying.

## v2.4.6

Release enforcing exact browser GPS preservation, LOCATION DIAGNOSTICS output formatting, best-fix map links, coarse fix notices (>10 km), public Nginx capture URL display workflow, and Parrot OS VM hardware testing notes.

### Fixed / Added
- **Browser GPS Source & Exact Preservation**: All GPS coordinates come strictly from `navigator.geolocation` (`getCurrentPosition` followed by `watchPosition` with high accuracy options). Coordinates are preserved without math transformation, IP substitution, or operator location override.
- **Location Diagnostics Terminal Output**: Added `LOCATION DIAGNOSTICS` section displaying Source (`Browser Geolocation API`), Latitude, Longitude, Accuracy, Quality, Updates count, and Best fix indicator (`YES`).
- **Coarse Fix Notice**: Renders `NOTICE: Browser supplied a coarse location. No coordinate correction was applied.` when accuracy exceeds 10 km.
- **Best-Fix Map Links**: Generated Google Maps, Google Earth, and OpenStreetMap URLs exclusively use `session.best_fix`.
- **Public Capture URL Startup Display**: When `--public-url` or `LOCLX_PUBLIC_URL` is set, CLI startup output displays `[+] Public Capture URL:` ONLY and suppresses `[+] Local Capture URL:`.
- **Nginx Example & Virtual Machine Guidance**: Complete documented Nginx reverse proxy configuration in `README.md` and explanation of browser location limitations inside Parrot/Kali virtual machines.

## v2.4.5

Maintenance and documentation release enforcing strict GPS vs. IP location separation, honest accuracy labeling, map link generation using best fix only, and Nginx deployment architecture.

### Fixed / Added
- **Strict GPS vs. Network Separation**: Explicitly separates browser GPS coordinates (`gps.latitude`, `gps.longitude`, `gps.accuracy`) from IP geolocation estimates (`ip_location.latitude`, `ip_location.longitude`, `ip_location.accuracy`).
- **Coarse Fix Handling & Status**: Coarse fixes ($> 10000\text{ m}$) are explicitly labeled `COARSE BROWSER FIX` without claiming exactness or performing reverse-geocoding.
- **Best-Fix Map Link Generation**: All map links (Google Maps, Google Earth, OpenStreetMap) are generated exclusively from `session.best_fix`.
- **Zero Coordinate Fabrication**: LOCLX strictly reports browser-provided coordinates without modification or substitution.
- **Nginx Architecture & Public Networking Documentation**: Added documentation covering reverse proxy configuration, secure context (`https://`), trusted proxy header extraction (`X-Real-IP`, `X-Forwarded-For`), and networking prerequisites for public exposure.
- **Parrot OS / VM Testing Guidance**: Documented virtual machine location limitations when host location hardware is unavailable.

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
