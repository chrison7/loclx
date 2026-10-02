# Comparative Analysis: IP Geolocation vs. Browser GPS

This document details the architectural differences, accuracy characteristics, and security models separating network IP geolocation from W3C browser GPS positioning in LOCLX.

---

## Technical Comparison

| Feature / Metric | Browser Geolocation (GPS / Radio) | IP Geolocation (Network Intelligence) |
| :--- | :--- | :--- |
| **Data Source** | Physical GPS receiver, Wi-Fi BSSID scanning, cell tower RTT | ISP BGP routing databases, ASN registries, MaxMind / WHOIS |
| **User Permission** | **Required** (Native browser security prompt) | **None required** (Extracted from HTTP connection IP) |
| **Accuracy Level** | High to Moderate ($\pm 5\text{ m}$ to $\pm 100\text{ m}$) | Approximate ($\pm 10\text{ km}$ to $\pm 50\text{ km}$) |
| **VPN / Proxy Sensitivity** | Insensitive (reports true device hardware fix) | Highly sensitive (reports VPN exit node IP location) |
| **Secure Context Requirement**| Requires HTTPS or `http://127.0.0.1` | Works over plain HTTP or HTTPS |
| **LOCLX Classification** | `HIGH`, `GOOD`, `MODERATE`, `LOW`, `COARSE` | `APPROXIMATE NETWORK IP LOCATION` |

---

## Architectural Principles in LOCLX

1. **Strict Field Separation:**
   Device GPS data (`latitude`, `longitude`, `accuracy`) and Network IP data (`ip_lat`, `ip_lon`, `ip_city`) are stored in completely separate data structures in `Session`.

2. **No Fallback Substitution:**
   LOCLX never substitutes IP coordinates into GPS data fields when GPS permission is denied or pending. If a participant declines GPS permission, the GPS panel remains empty/unlinked.

3. **Discrepancy Analysis ($\Delta\text{km}$):**
   When both IP location and device GPS coordinates are available, LOCLX computes the Haversine distance between them. Large discrepancies ($\Delta\text{km} > 50\text{ km}$) indicate VPN/proxy routing or regional ISP POP backhaul.
