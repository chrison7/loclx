# Operator Security Dashboard Documentation

This document describes the design, features, telemetry panels, and data sources of the LOCLX Operator Security Dashboard (`web/dashboard.html` and `web/dashboard.js`).

---

## Overview

The operator dashboard provides a real-time, interactive security-testing interface for monitoring participant sessions. It is accessed via `http://127.0.0.1:<port>/dashboard/<SESSION_ID>`.

> **Critical Distinction:** The dashboard displays location coordinates reported **exclusively by the participant's browser** for session `LX-XXXXXX`. It does **NOT** query or display the laptop operator's own local Google Maps or host device location.

---

## Dashboard Layout & Features

### 1. Header & Session Status Bar
- **Session ID:** Displays current active session key (`LX-XXXXXX`).
- **Connection Status:** Live indicator showing `WAITING`, `CONNECTED`, or `EXPIRED`.
- **Session Uptime:** Displays session duration formatted in hours, minutes, and seconds.
- **GPS Update Counter:** Shows total count of location fix payloads received.

### 2. Live Map Container (Leaflet.js)
- **Device GPS Fix Marker:** Distinct blue marker with an outer accuracy radius circle indicating browser-reported accuracy ($r$ in meters).
- **Network IP Location Marker:** Distinct orange marker depicting network IP geolocation estimate.
- **Movement Polyline Trail:** Blue path connecting historical GPS fix coordinates in chronological order.
- **Auto-Fit Bounds:** Automatically adjusts map zoom to contain both GPS and IP markers.

### 3. Location Intelligence Panels
- **GPS Data Panel:**
  - Latitude & Longitude (precision to 6 decimal places).
  - Accuracy radius ($r$) formatted in meters/kilometers.
  - Quality classification tier (`HIGH`, `GOOD`, `MODERATE`, `LOW`, `COARSE`).
  - Altitude, speed, and heading (if reported by device).
  - Timestamp of last fix.
- **Best Fix Panel:** Automatically highlights the location fix with the smallest accuracy radius recorded during the session.
- **IP Geolocation Panel:**
  - IP Address.
  - ISP & ASN details.
  - City, Region, Country, and Postal Code.
  - IP-based coordinate estimate.

### 4. Discrepancy & Haversine Distance Analyzer
- **Haversine Distance ($\Delta\text{km}$):** Calculates physical distance between network IP estimate and device GPS coordinates.
- **Interpretation:** Helps identify proxy usage, VPN routing, or regional ISP routing discrepancies.

### 5. Participant Browser Environment Panel
- User-Agent string.
- Operating System & Browser Engine.
- Screen resolution and Device Pixel Ratio (DPR).
- CPU logical core count (`hardwareConcurrency`).
- System language and timezone.

### 6. System & Telemetry Diagnostics Panel
- Loopback binding verification (`127.0.0.1`).
- Active rate limiter status (req/min).
- Session TTL countdown.

---

## Session Isolation & Security

- **Strict Session Scoping:** Dashboard routes (`/dashboard/<SESSION_ID>`) pull data exclusively for `<SESSION_ID>`. Participant telemetry from Session A can never be rendered in Session B.
- **Loopback Route Restriction:** Access to administrative dashboard routes is restricted to local loopback connections.
