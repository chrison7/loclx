# Changelog

## v2.1.2

Session-centric terminal OSINT workflow release inspired by information-gathering tools.

### Added
- **Session-Centric Terminal Workflow**: LOCLX terminal acts as central controller and listener.
- **Session-Specific URLs**: Dedicated collection endpoints (`/session/<SESSION_ID>`, `/dashboard/<SESSION_ID>`, `/api/session/<SESSION_ID>/report`, `/api/session/<SESSION_ID>/qr`).
- **Target Connection Notification**: Real-time console notifications when a browser connects to a session URL (`[+] SESSION CONNECTED`).
- **Hound-Style Intelligence Reports**: Added `loclx report <ID>` command generating formatted terminal reports aggregating Session, Device, Network, IP Location, GPS Location, Map links, and Discrepancy Analysis.
- **High-Accuracy Geolocation Settings**: Configured `enableHighAccuracy: true`, `timeout: 15000`, `maximumAge: 0` for browser GPS capture.
- **Subcommand Expansion**: Added `loclx session create`, `loclx target`, `loclx map`, `loclx earth`, `loclx report`, `loclx live`.
- **Session-Specific QR Code**: ASCII QR code generator encodes `/session/<SESSION_ID>` instead of root URL.
- **Minimal Browser Client**: Streamlined consent landing page focused on clear location permission request.
- **Regression Unit Tests**: Expanded test suite to verify session routing, connection events, report generation, and map link formatting.

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
