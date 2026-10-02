# Comprehensive Troubleshooting Guide

This guide provides step-by-step diagnostic and remediation procedures for common operational issues encountered when running LOCLX (v2.4.8).

---

## Quick Diagnostic Command

Run the automated system diagnostic runner at any time:

```bash
loclx diagnostics
```

---

## Issue Resolution Matrix

### 1. HTTPS / Secure Context Failure
- **Symptom:** Browser console error `navigator.geolocation is undefined` or geolocation prompt does not appear.
- **Root Cause:** Participant page accessed over unencrypted `http://` on a remote domain or IP address.
- **Solution:** Remote deployments require HTTPS. Use Cloudflare Quick Tunnel (`loclx start --tunnel`) or configure an Nginx reverse proxy with TLS certificates.

---

### 2. Geolocation Permission Denied
- **Symptom:** Terminal status or dashboard displays `PERMISSION_DENIED`.
- **Root Cause:** User clicked "Block" or site permissions are blocked in browser site settings.
- **Solution:** Reset site location permissions in browser site settings (lock icon in address bar) and reload page.

---

### 3. Position Unavailable
- **Symptom:** Error code 2 (`POSITION_UNAVAILABLE`).
- **Root Cause:** Device cannot establish location fix (e.g. indoors, OS location services toggled off, or missing GPS/Wi-Fi radios).
- **Solution:** Ensure OS-level location services are turned ON. On Windows/macOS/Android, verify Location permissions are allowed for the browser application.

---

### 4. Geolocation Acquisition Timeout
- **Symptom:** Error code 3 (`TIMEOUT`).
- **Root Cause:** Device location provider took longer than 60 seconds (`timeout: 60000`) to return a fix.
- **Solution:** Move closer to windows or outdoors for satellite visibility. Refresh participant page to trigger fresh fix request.

---

### 5. Coarse Laptop Location
- **Symptom:** Accuracy radius reported is $1,000\text{ m}$ to $50,000\text{ m}$ (`COARSE`).
- **Root Cause:** Laptop or desktop PC lacks dedicated GPS receiver or Wi-Fi scanning hardware, falling back to IP/cellular tower positioning.
- **Solution:** This is normal hardware behavior. Mobile smartphones produce significantly tighter (`HIGH` / `GOOD`) accuracy radii.

---

### 6. Virtual Machine (VM) Location Limitations
- **Symptom:** Testing inside VMware, VirtualBox, or WSL returns timeout or coarse location.
- **Root Cause:** Hypervisors do not pass physical Wi-Fi or Bluetooth radios through to guest OS.
- **Solution:** Test participant landing pages using a physical mobile browser or host OS browser.

---

### 7. Stale Browser Assets
- **Symptom:** Dashboard or participant landing page UI does not update after upgrading LOCLX.
- **Root Cause:** Browser cached old static assets (`app.js`, `dashboard.js`, `style.css`).
- **Solution:** Perform a hard refresh (`Ctrl + F5` or `Cmd + Shift + R`) or clear browser cache.

---

### 8. Invalid or Wrong Session ID
- **Symptom:** HTTP 400 or HTTP 404 response on `/session/<ID>` or `/dashboard/<ID>`.
- **Root Cause:** Session ID key format is invalid or session does not exist in memory.
- **Solution:** Verify active sessions via CLI: `loclx session list`. Ensure session IDs follow `LX-XXXXXX` format.

---

### 9. Dashboard Not Updating
- **Symptom:** Participant allowed location, but dashboard map marker does not move.
- **Root Cause:** Dashboard opened for wrong session ID or local loopback connection interrupted.
- **Solution:** Verify dashboard URL matches participant session ID (`http://127.0.0.1:8765/dashboard/LX-XXXXXX`).

---

### 10. Public URL Configuration Issues
- **Symptom:** Participant link generated with `http://127.0.0.1` instead of public domain.
- **Root Cause:** Public URL flag or environment variable not provided.
- **Solution:** Pass `--public-url https://custom-domain.example.com` or export `LOCLX_PUBLIC_URL="https://custom-domain.example.com"`.

---

### 11. Cloudflare Tunnel Failures
- **Symptom:** `loclx start --tunnel` hangs or fails to generate URL.
- **Root Cause:** `cloudflared` binary not installed or network blocks outbound tunnel connections.
- **Solution:** Verify `cloudflared` is installed (`cloudflared --version`). Check firewall rules allowing outbound HTTPS connections.

---

### 12. Nginx Reverse Proxy Problems
- **Symptom:** Client IP appears as `127.0.0.1` or reverse proxy loops.
- **Root Cause:** Missing `X-Forwarded-For` or `X-Real-IP` headers in Nginx configuration.
- **Solution:** Ensure Nginx includes `proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;` and `proxy_set_header X-Forwarded-Proto $scheme;`.

---

### 13. IP / GPS Location Mismatch
- **Symptom:** IP marker is in a different city or country than GPS marker ($\Delta\text{km} > 100\text{ km}$).
- **Root Cause:** Participant is connected through a VPN, Tor, or cellular carrier roaming gateway.
- **Solution:** This is expected behavior. The dashboard distance analyzer highlights this discrepancy as potential proxy/VPN usage.

---

### 14. Session Expiration
- **Symptom:** Session disappears after 30 minutes of inactivity.
- **Root Cause:** Default session TTL (`LOCLX_SESSION_TTL = 1800`) expired.
- **Solution:** Create a new session (`loclx start` or `loclx session create`) or increase TTL via environment variable (`export LOCLX_SESSION_TTL=3600`).
