# LOCLX Architecture Overview

LOCLX (Live Location & Information eXtractor) v2.0 is designed as a modular, consent-based Linux security and OSINT laboratory tool.

## Component Design

```
+-------------------------------------------------------------+
|                      LOCLX CLI Launcher                     |
|            (Interactive Menu / Command Arguments)           |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                      Session Manager                        |
|   - Unique LX-XXXXXX Session Tokens                         |
|   - Auto-Expiration & Status Tracking                       |
|   - Memory Storage & Export (JSON / CSV)                    |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                      HTTP API Server                        |
|   - Standard Library ThreadingHTTPServer (127.0.0.1)        |
|   - Rate Limiter & Sanitization Middleware                   |
|   - REST Endpoints (/api/session/*, /report, /dashboard)    |
+------------------------------+------------------------------+
                               |
        +----------------------+----------------------+
        |                                             |
        v                                             v
+-------------------------------+   +-------------------------------+
|      IP Intelligence Engine   |   |   Consent Web Laboratory UI   |
|   - Abstract IPProvider       |   |   - Geolocation API           |
|   - IPWhoIs / IPApi Fallback  |   |   - Interactive Consent Box   |
|   - Labelled as APPROXIMATE   |   |   - Dark Security Dashboard   |
+-------------------------------+   +-------------------------------+
```

## Modules Summary

- `loclx.cli`: Argument parsing, TTY ANSI formatting, interactive menu loop, and `--lab` mode execution.
- `loclx.server`: HTTP API endpoints (`/report`, `/api/session/...`, static asset serving). Fixed to `127.0.0.1`.
- `loclx.sessions`: Session object lifecycle, timeout management, data aggregation.
- `loclx.gps`: Geodesic mathematics (Haversine formula), coordinate validation, precision formatting.
- `loclx.ipinfo`: Abstracted IP provider framework (`IPProvider`, `IPWhoIsProvider`, `IPApiProvider`).
- `loclx.browser`: User-agent and browser capability parsing.
- `loclx.storage`: History buffer with JSON and CSV export logic.
- `loclx.security`: Token bucket rate limiting, input sanitization, 64KB request body size limiting.
- `loclx.dashboard`: Real-time ANSI terminal dashboard rendering.
