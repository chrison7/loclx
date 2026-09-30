# GPS Geolocation & Precision in LOCLX

LOCLX uses the standard W3C Geolocation API (`navigator.geolocation`) provided by modern web browsers.

## Principles

1. **Explicit Consent**: GPS coordinate collection cannot start automatically. The user must explicitly press a button to grant location permission.
2. **Standard Methods**:
   - `getCurrentPosition()`: Acquires a single location fix.
   - `watchPosition()`: Establishes a live location stream updating on position changes.
3. **Accuracy & Altitude**:
   - Latitude and longitude are formatted to 6 decimal places (~0.1m precision).
   - Accuracy radius is reported in meters (e.g. `±7 m`).
   - Altitude is captured when reported by device sensors.

## Discrepancy Analysis (Haversine Formula)

The Haversine formula is used to calculate the great-circle distance between the approximate IP-derived coordinates and exact browser GPS coordinates:

\[
a = \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1) \cdot \cos(\phi_2) \cdot \sin^2\left(\frac{\Delta \lambda}{2}\right)
\]
\[
c = 2 \cdot \text{atan2}\left(\sqrt{a}, \sqrt{1-a}\right)
\]
\[
d = R \cdot c \quad (R = 6371 \text{ km})
\]

This measurement clearly illustrates the inaccuracy of IP geolocation compared to true device GPS fixes.
