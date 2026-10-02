# Browser Geolocation & GPS Processing Guide

This document details how LOCLX acquires, processes, classifies, and stores location data provided via the W3C Geolocation API.

---

## W3C Geolocation API Mechanism

LOCLX interacts with client devices through standard W3C Geolocation API calls in `web/app.js`:

```javascript
navigator.geolocation.watchPosition(successCallback, errorCallback, options);
```

### Core API Methods
- `getCurrentPosition`: Requests a single location fix snapshot.
- `watchPosition`: Registers a continuous location listener that triggers success callbacks whenever device position or accuracy changes.

### Geolocation Options (`GEO_OPTS`)
```javascript
const GEO_OPTS = {
  enableHighAccuracy: true,
  timeout: 60000,
  maximumAge: 0
};
```

1. **`enableHighAccuracy: true`**
   - Instructs the underlying operating system and browser to request the most precise location data available (e.g. physical GPS receiver, multi-ap Wi-Fi positioning, or Bluetooth beacons).
   - Increases acquisition time and power consumption compared to low-accuracy network lookups.

2. **`maximumAge: 0`**
   - Explicitly requests a **fresh position fix** from the underlying location provider rather than accepting a previously cached position. Setting `maximumAge: 0` ensures that historical positions cached by the browser are not returned.

3. **`timeout: 60000`**
   - Specifies the maximum duration (60 seconds) the browser will wait for the location provider to return a valid fix before triggering a `TIMEOUT` error callback.

---

## Physical Hardware & OS Limitations

- **Browser & OS Authority:** JavaScript running in the browser cannot force the device to enable physical GPS hardware if location services are disabled at the OS level.
- **Desktop & Laptop PCs:** Desktop computers and laptops without dedicated GPS chips or Wi-Fi scanning hardware rely on IP-assisted or cellular positioning from the OS, often yielding coarse accuracy.
- **Virtual Machines:** Linux VMs (e.g. Kali, Parrot OS) running inside hypervisors (VMware, VirtualBox, WSL) lack access to host radio hardware and typically return coarse location errors or position unavailable timeouts.

---

## GPS Accuracy Tiers & Quality Classification

LOCLX classifies browser-reported accuracy radii into standardized quality tiers in `src/loclx/gps.py`:

```python
def classify_gps_quality(acc: float) -> str:
    if acc <= 25.0:
        return "HIGH"
    elif acc <= 100.0:
        return "GOOD"
    elif acc <= 1000.0:
        return "MODERATE"
    elif acc <= 10000.0:
        return "LOW"
    else:
        return "COARSE"
```

| Quality Tier | Accuracy Radius ($r$) | Description & Common Provider Source |
| :--- | :--- | :--- |
| **HIGH** | $r \le 25\text{ m}$ | Precise hardware GPS, GNSS, or multi-point Wi-Fi RTT. |
| **GOOD** | $25\text{ m} < r \le 100\text{ m}$ | Wi-Fi network scanning / dense cell tower fix. |
| **MODERATE** | $100\text{ m} < r \le 1,000\text{ m}$ | Single-tower cellular or broad Wi-Fi lookup. |
| **LOW** | $1,000\text{ m} < r \le 10,000\text{ m}$ | Coarse regional cell ID / ISP network lookup. |
| **COARSE** | $r > 10,000\text{ m}$ | Low-precision IP/cellular fallback fix. |

---

## Best Fix Tracking & History Storage

### Best Fix Selection (`best_fix`)
Whenever a new GPS fix payload is received for an active session:
- LOCLX compares the incoming fix's `accuracy` radius against the currently stored `best_fix`.
- If no previous `best_fix` exists, or if the new fix has a smaller (more accurate) accuracy radius, `best_fix` is updated to the new fix.

### Ephemeral History Log (`history`)
- Each session maintains an in-memory chronological list of received GPS updates.
- Storage cap is governed by `LOCLX_MAX_HISTORY` (default: 500 items).
- History items feed the movement polyline trail rendered in the operator dashboard.
