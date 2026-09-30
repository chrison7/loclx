# LOCLX Troubleshooting Guide

## Common Issues & Solutions

### 1. Browser Denies Location Permission
- **Symptom**: `gps status` shows `PERMISSION_DENIED`.
- **Cause**: User clicked "Block" on the browser geolocation prompt or site location permissions are blocked in site settings.
- **Solution**: Reset browser site permissions for `http://127.0.0.1:8765` and press **[ Request Location Permission ]** again.

### 2. Location Fix Unavailable / Timeout
- **Symptom**: `POSITION_UNAVAILABLE` or `TIMEOUT`.
- **Cause**: Device lacks hardware GPS sensors, Wi-Fi location services are disabled, or indoors without satellite line-of-sight.
- **Solution**: Ensure Wi-Fi or location services are enabled on the host OS.

### 3. Preferred Port in Use
- **Symptom**: Console displays warning that port 8765 is occupied.
- **Solution**: LOCLX automatically falls back to ports 8766, 8767, or an OS-assigned port. Alternatively, specify `loclx --port 9000`.

### 4. IP Geolocation Lookup Fails
- **Symptom**: `IP intelligence unavailable`.
- **Cause**: Outbound Internet connectivity is offline or primary IP API is rate-limited.
- **Solution**: LOCLX automatically switches to secondary fallback providers (`ipapi.co`). Verify outbound Internet connectivity.

### 5. Running Diagnostics
To inspect all components at once, run:
```bash
loclx diagnostics
```
