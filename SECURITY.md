# LOCLX Security Policy

This document outlines the security architecture, invariants, threat model, and vulnerability reporting procedures for the LOCLX project.

---

## Scope

LOCLX is an authorized browser-geolocation and OSINT security laboratory.

"The LOCLX application server remains bound to 127.0.0.1. Public access, when intentionally configured, occurs through an operator-controlled reverse proxy or tunnel."

---

## Security Architecture

The LOCLX architecture separates local application execution from public transport exposure:

- **Application Layer:** The Python HTTP server (`loclx.server`) binds exclusively to `127.0.0.1:<port>`. It processes session routes, serves participant assets, and receives location payloads.
- **Transport Layer:** Secure remote connections are achieved by placing an operator-controlled reverse proxy (e.g. Nginx, Apache) or encrypted tunnel (`cloudflared`) in front of the local loopback listener.
- **Data Engine:** Session state and GPS coordinates reside strictly in volatile process memory (`loclx.sessions`, `loclx.storage`) with automatic expiration (TTL) and bounded history caps.

---

## Threat Model

LOCLX operates under the following threat assumptions:

1. **Untrusted Participant Inputs:** Data sent by browsers to `/api/session/<sid>/report` (coordinates, User-Agent, headers) is untrusted and must be strictly validated.
2. **Untrusted External Network:** When exposed via reverse proxy/tunnel, external clients can attempt denial-of-service, path traversal, rate-limit flooding, or session enumeration.
3. **Authorized Laboratory Execution:** The operator explicitly deploys LOCLX for authorized testing with full awareness of session creation and listener logs.

---

## Security Invariants

The following security properties are guaranteed by design:

- **Loopback Listener Invariant:** The core HTTP server listener will never bind directly to external network interfaces (`0.0.0.0` or public IPs).
- **Explicit Consent Requirement:** JavaScript runtime scripts (`app.js`) invoke `navigator.geolocation` only upon explicit user button click. No stealth background calls on page load.
- **Zero Coordinate Fabrication:** Coordinates received from browsers are processed and displayed strictly as reported. LOCLX never spoofs or fakes location data.
- **Strict Data Isolation:** Browser GPS data and network IP geolocation data are stored and labeled as separate fields and are never combined or interchanged.

---

## Browser Permission Model

Browser geolocation requires explicit permission:
- **Origin-Scoped Prompt:** Modern browsers gate `navigator.geolocation` behind origin-level user permission dialogs.
- **Secure Context Enforcement:** Browsers reject geolocation requests on unencrypted HTTP connections unless on `127.0.0.1`. Remote deployments must use HTTPS via proxy/tunnel.
- **No Native Bypass:** Modern web browsers prevent JavaScript from programmatically forging or bypassing permission grants.

---

## Session Isolation

- **Token Format:** Session IDs follow the pattern `LX-` followed by 6 hexadecimal characters (`LX-[0-9A-F]{6}`).
- **Route Validation:** Requests to session-specific endpoints (`/session/<sid>`, `/dashboard/<sid>`, `/api/session/<sid>/report`) require a valid active session.
- **Data Scope:** Session A data is strictly isolated from Session B. Cross-session reads or writes are rejected.

---

## Input Validation

All incoming HTTP requests pass through strict input checks in `loclx.security`:
- **Coordinate Bounds:** Latitude must be within $[-90.0, 90.0]$; Longitude must be within $[-180.0, 180.0]$. Non-numeric, finite numeric checks apply.
- **Type Checking:** All numeric parameters (accuracy, altitude, heading, speed) undergo strict float parsing and range verification.
- **Sanitization:** String fields (User-Agent, session IDs) are sanitized against control characters and script injection.

---

## Rate Limiting

- **Per-IP Rate Limiting:** Enforced via `SecurityGuard` in `loclx.security`.
- **Threshold:** Maximum 100 requests per minute per remote IP address.
- **Enforcement:** Exceeding rate limits triggers an HTTP `429 Too Many Requests` response.

---

## Request Size Limits

- **Payload Cap:** HTTP request bodies sent to POST endpoints are strictly capped at 64 KB (65,536 bytes).
- **Enforcement:** Excessively large request bodies are rejected immediately with HTTP `413 Payload Too Large`.

---

## Proxy Trust

- **Forwarded Header Processing:** When deployed behind a reverse proxy or tunnel, LOCLX extracts client IP addresses from `X-Forwarded-For` or `X-Real-IP` headers.
- **Public URL Resolution:** The external base URL is dynamically determined from `LOCLX_PUBLIC_URL`, `PUBLIC_BASE_URL`, `LOCLX_TUNNEL_URL`, `X-Forwarded-Proto`, or `X-Forwarded-Host`.

---

## Public Route Restrictions

- **Participant Routes:** `/session/<sid>` and `/api/session/<sid>/report` are accessible to remote participants via proxy/tunnel.
- **Administrative Routes:** Dashboard (`/dashboard/<sid>`) and administrative session endpoints are strictly restricted to local loopback operators when header checks detect un-forwarded external access.

---

## Data Retention

- **In-Memory Storage:** All session data, target metadata, and GPS history items are kept strictly in ephemeral process memory.
- **Session Expiration:** Sessions expire automatically after their TTL (default: 30 minutes) or upon process shutdown.
- **No Disk Storage:** No target data, coordinates, or IP logs are written to disk.

---

## Sensitive Data Handling

- **No Credential Harvesting:** LOCLX contains no mechanisms for collecting passwords, session cookies, auth tokens, or private device storage.
- **Transparent Disclosure:** The participant landing page clearly discloses information processing ("Browser Information Demo") and requests consent.

---

## Reporting Vulnerabilities

If you discover a security vulnerability or security invariant violation in LOCLX:

1. **Submission:** Open a GitHub security issue or contact the repository maintainer directly via GitHub.
2. **Details:** Include a clear description of the issue, steps to reproduce, and any relevant traceback or payload examples.

---

## Responsible Disclosure

We appreciate security researchers who adhere to responsible disclosure guidelines:
- Allow reasonable time to address reported issues before public disclosure.
- Avoid testing against unauthorized target systems or non-consenting users.
