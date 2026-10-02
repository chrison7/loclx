# HTTPS & Secure Context Requirements

This document explains why HTTPS is strictly required for remote browser geolocation and details how LOCLX operates behind reverse proxies and secure tunnels.

---

## The W3C Secure Context Requirement

Modern web browsers enforce strict security policies regarding sensitive web APIs:

- **Secure Context Gating:** `navigator.geolocation` is designated as a Powerful Feature by the W3C specification. Browsers restrict access to `navigator.geolocation` strictly to **Secure Contexts**.
- **`window.isSecureContext` Check:** `web/app.js` inspects `window.isSecureContext` prior to requesting location permissions.
- **Allowed Schemes:**
  - `https://` (all domain names and remote public URLs)
  - `http://127.0.0.1` or `http://localhost` (loopback exception for local development)
- **Blocked Schemes:** Plain unencrypted `http://` over remote IP addresses or domain names. Accessing `http://<PUBLIC_IP>:8765` causes the browser to disable `navigator.geolocation` entirely (`navigator.geolocation` evaluates to `undefined` or rejects calls).

---

## Secure Architecture: Reverse Proxy & Tunnels

To collect consent-gated browser coordinates over the internet, the participant landing page must be served over HTTPS. The local LOCLX HTTP server remains bound to `127.0.0.1`, while an external reverse proxy or tunnel terminates TLS.

```
PUBLIC HTTPS
      ↓
proxy / tunnel
      ↓
127.0.0.1
      ↓
LOCLX Server
```

---

## Deployment Options

### Option A: Cloudflare Quick Tunnel (`--tunnel`)

LOCLX includes automated Cloudflare tunnel integration:

```bash
loclx start --tunnel
```

1. LOCLX spawns `cloudflared` in the background targeting `http://127.0.0.1:<port>`.
2. Cloudflare provisions a temporary, free HTTPS URL (`https://<subdomain>.trycloudflare.com`).
3. LOCLX automatically detects and displays the public HTTPS session URL.

### Option B: Custom Reverse Proxy / Domain (`--public-url`)

If you manage your own domain and reverse proxy (such as Nginx, Caddy, or Apache):

```bash
loclx start --public-url https://custom-domain.example.com
```

Or set the environment variable:

```bash
export LOCLX_PUBLIC_URL="https://custom-domain.example.com"
loclx start
```

### Nginx Reverse Proxy Configuration Example

```nginx
server {
    listen 443 ssl http2;
    server_name custom-domain.example.com;

    ssl_certificate /etc/letsencrypt/live/custom-domain.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/custom-domain.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8765;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

> **Security Note:** The Python LOCLX listener remains securely bound to `127.0.0.1`. Public HTTPS exposure is handled safely at the reverse proxy / tunnel layer.
