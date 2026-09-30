# Changelog

## v2.0.0

Major architecture upgrade transforming LOCLX into an advanced consent-based Linux security & OSINT laboratory tool.

### Added
- **Modular Package Structure**: Split single-file demo into clean Python package under `src/loclx/` (`cli`, `server`, `sessions`, `gps`, `ipinfo`, `browser`, `storage`, `security`, `dashboard`, `utils`).
- **Interactive TTY Terminal Interface**: Banner box, numeric menu (0-10), ANSI colorized status, live session tracking.
- **Session Management System**: Non-predictable `LX-XXXXXX` session identifiers, configurable timeouts, auto-expiration, session list/show/stop/delete operations.
- **Pluggable IP Provider Framework**: Abstract `IPProvider` class with `IPWhoIsProvider` and `IPApiProvider` fallbacks.
- **Security & Rate Limiting**: In-memory token bucket rate limiter, input sanitization, 64KB max request body protection.
- **Dark Security Dashboard & Live Map**: Responsive web security dashboard with Leaflet map tracking, movement trail, and session history management.
- **Data Export**: Support for JSON and CSV history exports.
- **CLI Options**: Added `--port`, `--no-browser`, `--debug`, `--lab`, `--version`, `--help`.
- **Educational Lab Mode (`--lab`)**: Self-contained demonstration explaining IP vs GPS boundaries.
- **Comprehensive Unit & Guard Tests**: 27 unit tests verifying sessions, GPS math, IP info, rate limiting, HTTP endpoints, and security guard conditions.

## v1.0.1

Documentation and security policy release.

- Added `CONTRIBUTING.md` guidelines outlining single-machine teaching scope and non-negotiable localhost rules.
- Added `SECURITY.md` defining vulnerability report boundaries and security policy.
- Added architectural screenshot and asset references.

## v1.0.0

First release of LOCLX localhost demonstration.
