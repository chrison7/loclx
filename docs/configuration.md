# LOCLX Configuration Reference

LOCLX supports safe configuration via environment variables while strictly preserving hard security invariants.

## Supported Environment Variables

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `LOCLX_PORT` | Integer | `8765` | Preferred HTTP server listening port |
| `LOCLX_SESSION_TTL` | Float | `1800` | Session auto-expiration timeout in seconds (30 mins) |
| `LOCLX_MAX_HISTORY` | Integer | `500` | Maximum number of GPS fixes stored in memory per session |
| `LOCLX_DEBUG` | Boolean | `0` | Enable verbose log emission |
| `LOCLX_IP_PROVIDER` | String | `auto` | Primary IP intelligence provider (`ipwho.is` or `ipapi.co`) |

## Hard Invariants (Non-Configurable)

- **Fixed Bind Address**: `BIND_ADDR` is permanently hardcoded to `"127.0.0.1"`.
- **No Remote Host / Tunnel Flags**: LOCLX rejects flags like `--bind`, `--host`, or `LOCLX_BIND` to prevent remote exposure.
