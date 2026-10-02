# IP Geolocation Intelligence Specification

This document details how network IP geolocation data is retrieved, processed, and displayed in LOCLX.

---

## Technical Overview

IP geolocation is a network-based lookup mechanism that maps an IP address to geographic metadata using BGP routing tables, ASN registries, and ISP location databases.

> **CRITICAL RULE:** IP location is strictly approximate. IP location is **NOT** GPS, and IP coordinates are **NEVER** used as a fallback for missing browser GPS data.

---

## Data Providers & Resilience

LOCLX uses a dual-provider architecture in `src/loclx/ipinfo.py`:

1. **Primary Provider: `ipwho.is`**
   - Query format: `https://ipwho.is/<IP>`
   - Endpoint data: IP, ASN, ISP, organization, country, region, city, postal code, latitude, longitude, timezone.

2. **Fallback Provider: `ipapi.co`**
   - Query format: `https://ipapi.co/<IP>/json/`
   - Invoked automatically if the primary provider is unreachable or returns an HTTP error.

---

## Extracted Metrics

- **Network Metadata:** Outbound IP address, Internet Service Provider (ISP), Autonomous System Number (ASN), Organization.
- **Geographic Data:** Country name, country code, region/state, city, postal code.
- **Approximate Coordinates:** Latitude and Longitude estimated for the ISP POP (Point of Presence) or routing hub.
- **Timezone:** Timezone ID and UTC offset.

---

## Accuracy & Scope

- **Resolution:** Typically city or regional level ($\pm 10\text{ km}$ to $\pm 50\text{ km}$).
- **VPN / Proxy Impact:** If the participant routes traffic through a VPN, Tor, or proxy server, IP geolocation reflects the proxy exit node rather than the participant's physical device.
- **Labeling:** In all terminal reports, CLI output, and dashboard maps, IP data is explicitly labeled `APPROXIMATE NETWORK IP LOCATION`.
