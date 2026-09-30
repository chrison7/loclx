# Security & Safeguards Policy

LOCLX is an authorized educational laboratory tool built with strict security controls.

## Hard Security Boundaries

1. **Fixed Bind Address (`127.0.0.1`)**: The server cannot bind to external non-loopback interfaces or expose remote flags.
2. **No Tunneling Integration**: LOCLX does not integrate with third-party reverse proxies or SSH reverse tunnels.
3. **Cryptographic Tokens**: Session IDs are non-sequential hexadecimal tokens (`LX-XXXXXX`).
4. **Request Rate Limiting**: In-memory token bucket rate limiter caps incoming requests per client IP.
5. **Request Payload Limits**: Request bodies exceeding 64KB are rejected with HTTP 413.
6. **Input Sanitization**: All incoming data is sanitized against XSS injection before rendering.
7. **No Data Retention**: History storage is ephemeral and retained in-memory only until session expiration.
