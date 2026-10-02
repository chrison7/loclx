# Configuration Reference

This document describes all environment variables, runtime constants, and CLI configuration flags used in LOCLX (v2.4.8).

---

## Security Invariant (Unchangeable Setting)

### `BIND_ADDR`
- **Default:** `127.0.0.1`
- **Description:** Fixed loopback IP address for the HTTP server listener in `src/loclx/server.py`.
- **Security Invariant:** This value is hardcoded and cannot be changed via environment variables or CLI flags. LOCLX will always bind strictly to `127.0.0.1`. Public exposure must be handled via an operator-controlled reverse proxy or tunnel.

---

## Active Environment Variables

| Variable Name | Default Value | Description |
| :--- | :--- | :--- |
| **`LOCLX_PORT`** | `8765` | Preferred HTTP listener port on `127.0.0.1`. Can also be set via `--port INT`. |
| **`LOCLX_SESSION_TTL`** | `1800` | In-memory session Time-To-Live in seconds (30 minutes). Sessions inactive past TTL are automatically expired. |
| **`LOCLX_MAX_HISTORY`** | `500` | Maximum number of historical GPS fixes stored in memory per session. |
| **`LOCLX_DEBUG`** | Disabled (unset) | Set to any non-empty value (or pass `--debug`) to enable verbose debug logging to stdout. |
| **`LOCLX_IP_PROVIDER`** | `ipwho.is` | Primary IP geolocation provider (`ipwho.is` or `ipapi.co`). |
| **`LOCLX_PUBLIC_URL`** | Unset | Public HTTPS reverse proxy URL (e.g. `https://custom-domain.example.com`). |
| **`PUBLIC_BASE_URL`** | Unset | Fallback public URL environment variable alias. |
| **`LOCLX_TUNNEL_URL`** | Unset | Fallback Cloudflare tunnel URL environment variable alias. |
| **`NO_COLOR`** | Unset | Standard environment variable to disable ANSI color codes in stdout when set. |

---

## CLI Configuration Inspection

Inspect the effective runtime configuration at any time:

```bash
loclx config
```

Example output:
```
LOCLX EFFECTIVE CONFIGURATION
────────────────────────────────────────────────────────────
  LOCLX_VERSION         : 2.4.8
  BIND_ADDR             : 127.0.0.1 (fixed loopback invariant)
  LOCLX_PORT            : 8765
  LOCLX_SESSION_TTL     : 1800s (30 mins)
  LOCLX_MAX_HISTORY     : 500 (in-memory history limit)
  LOCLX_IP_PROVIDER     : ipwho.is (fallback: ipapi.co)
  LOCLX_DEBUG           : Disabled
  BROWSER_AUTO_LAUNCH   : DISABLED (permanently disabled)
────────────────────────────────────────────────────────────
```
