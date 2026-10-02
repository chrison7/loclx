# Technical Security Controls & Implementation Guide

This document details the technical security mechanisms, input validation pipelines, session safeguards, and network controls implemented in `src/loclx/security.py`, `src/loclx/server.py`, and `src/loclx/sessions.py`.

---

## 1. Loopback Bind Address Invariant

- **Implementation:** `src/loclx/server.py` (`BIND_ADDR = "127.0.0.1"`)
- **Control:** The HTTP server listener is hardcoded to bind strictly to the loopback interface (`127.0.0.1`).
- **Rationale:** Prevents unauthorized direct network access to the Python web server on local network interfaces (all-interface binds or LAN IPs).

---

## 2. Session ID Format & Validation

- **Implementation:** `src/loclx/security.py` (`validate_sid_format`, `SESS_ID_PATTERN`)
- **Pattern:** `^LX-[A-F0-9]{6}$` (e.g. `LX-A1B2C3`)
- **Control:** All endpoints receiving a session ID parameter enforce regex pattern validation.
- **Protection:** Prevents path traversal attacks (`../`), arbitrary string injection, and invalid session key queries. Malformed session IDs are immediately rejected with HTTP 400.

---

## 3. GPS Payload Validation

- **Implementation:** `src/loclx/security.py` (`validate_gps_payload`)
- **Checks Performed:**
  - `lat`: Must be a finite number between $-90.0$ and $+90.0$.
  - `lon`: Must be a finite number between $-180.0$ and $+180.0$.
  - `accuracy`: Optional, must be non-negative and finite ($\ge 0.0$).
  - `altitude`: Optional, must be a finite number.
  - `speed`: Optional, must be non-negative and finite ($\ge 0.0$).
  - `heading`: Optional, must be a finite number between $0.0^\circ$ and $360.0^\circ$.
- **Protection:** Rejects `NaN`, `Infinity`, non-numeric types, boolean values masquerading as numbers, and out-of-bounds geographic coordinates.

---

## 4. Request Size Capping

- **Implementation:** `src/loclx/security.py` (`MAX_REQUEST_BODY = 64 * 1024`)
- **Control:** POST requests to `/api/session/<sid>/report` enforce a maximum body size limit of 64 KB (65,536 bytes).
- **Protection:** Mitigates memory exhaustion and Denial of Service (DoS) attacks attempting to post oversized JSON payloads.

---

## 5. Token-Bucket Rate Limiting

- **Implementation:** `src/loclx/security.py` (`RateLimiter`)
- **Parameters:** Capped at 100 requests per 60-second window per client IP address.
- **Control:** Tracks request timestamps per client IP. Requests exceeding 100 req/min return HTTP `429 Too Many Requests`.
- **Protection:** Prevents payload flooding and endpoint brute-forcing.

---

## 6. Input Sanitization & XSS Mitigation

- **Implementation:** `src/loclx/security.py` (`sanitize_input`)
- **Control:** Uses `html.escape()` to sanitize string inputs (such as User-Agent headers and client browser metadata).
- **Protection:** Prevents Cross-Site Scripting (XSS) when rendering browser metadata in HTML dashboard views or terminal outputs.

---

## 7. Proxy Handling & Client IP Extraction

- **Implementation:** `src/loclx/security.py` (`extract_client_ip`, `TRUSTED_PROXIES`)
- **Trusted Proxies:** `{"127.0.0.1", "::1", "localhost"}`
- **Control:** When an incoming connection originates from a trusted local proxy, client IP resolution inspects:
  1. `X-Real-IP` header
  2. First IP in `X-Forwarded-For` header list
- **Protection:** Prevents IP spoofing from direct untrusted remote connections while properly identifying client IPs behind Nginx or Cloudflare tunnels.

---

## 8. Public Base URL Validation

- **Implementation:** `src/loclx/security.py` (`validate_public_url`)
- **Rules:**
  - Remote public URLs must use the `https://` scheme.
  - `http://` scheme is permitted exclusively for `localhost` or `127.0.0.1` development.
  - Trailing slashes are stripped. Malformed URLs or unsupported schemes raise `ValueError`.

---

## 9. Ephemeral Memory Storage & Lifecycle

- **Implementation:** `src/loclx/sessions.py`, `src/loclx/storage.py`
- **Control:**
  - Sessions are maintained strictly in Python dictionary data structures in volatile memory.
  - TTL enforced (`LOCLX_SESSION_TTL`, default: 1800s / 30 mins). Expired sessions are automatically pruned.
  - In-memory GPS history capped per session (`LOCLX_MAX_HISTORY`, default: 500 fixes).
- **Protection:** Zero disk persistence ensures target telemetry is permanently lost upon process termination or TTL expiration.
