# Changelog

## v2.1.0

Major release transforming LOCLX into a professional Linux security & OSINT laboratory tool.

### Added
- **Redesigned Grouped CLI Menu**: Categorized into SESSION, ANALYSIS, TOOLS, Exit sections with auto terminal width detection.
- **CLI Subcommands**: Full command-line interface supporting `start`, `session list`, `session info`, `session stop`, `dashboard`, `gps`, `ip`, `browser`, `history`, `export`, `diagnostics`, `config`, and `qr`.
- **ASCII QR Code Generator**: Pure-Python standard library QR code renderer for terminal loopback URLs (`loclx qr`).
- **Integrated System Diagnostics**: Automated environment runner (`loclx diagnostics`) verifying Python 3.9+, OS, 127.0.0.1 loopback bind, port availability, web assets, session engine, IP APIs.
- **Effective Configuration Viewer**: Environment settings inspector (`loclx config`) displaying `LOCLX_PORT`, `LOCLX_SESSION_TTL`, `LOCLX_MAX_HISTORY`, `LOCLX_DEBUG`, `LOCLX_IP_PROVIDER`.
- **Enhanced Session Engine**: Configurable TTL (default 30 mins), bounded history limits (default 500 records), unpredictable `LX-XXXXXX` session identifiers.
- **Security HTTP Response Headers**: `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Cache-Control`.
- **Web Dashboard Location Discrepancy Panel**: Side-by-side location comparison card with Haversine distance interpretation.
- **Documentation Suite**: Added `docs/cli.md`, `docs/dashboard.md`, `docs/configuration.md`, `docs/troubleshooting.md`.

## v2.0.0

Major architecture upgrade transforming LOCLX into an advanced consent-based Linux security & OSINT laboratory tool.

## v1.0.1

Documentation and security policy release.

## v1.0.0

First release of LOCLX localhost demonstration.
