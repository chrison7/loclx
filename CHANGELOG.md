# Changelog

## v2.2.0

Major release hardening session security, session isolation, multi-session workflow, and terminal target handling.

### Added
- **Strict Session Routing**: `/session/<SESSION_ID>`, `/dashboard/<SESSION_ID>`, and `/api/session/<SESSION_ID>/*` strictly serve only the exact requested session. Invalid or expired sessions return HTTP 404/410 with "Session not found or expired" and never fall back to another active session.
- **Session Isolation & Validation**: Enforced strict `LX-[A-F0-9]{6}` session ID regex validation preventing path traversal and malformed inputs. Isolated GPS, browser metrics, network intelligence, and history buffers per session.
- **GPS Telemetry Validation**: Enforced strict boundary checks (`-90 <= lat <= 90`, `-180 <= lon <= 180`, `accuracy >= 0`, finite altitude/speed/heading) to reject malformed or non-finite client payloads.
- **Multi-Session Terminal Dashboard & Commands**: Added `loclx live <SESSION_ID>` live single-session dashboard, `loclx session list` table, `loclx session info <SESSION_ID>`, `loclx session stop <SESSION_ID>`, `loclx report <SESSION_ID>`, `loclx map <SESSION_ID>`, `loclx earth <SESSION_ID>`, and `loclx qr <SESSION_ID>`.
- **Target Connection Handling**: Live console event notifications (`[+] SESSION CONNECTED`) when a client opens a session URL.
- **Comprehensive Security Test Suite**: Added dedicated isolation, routing, stopped/expired session, and traversal vulnerability tests.

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
