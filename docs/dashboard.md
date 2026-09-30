# LOCLX Web Dashboard Guide

The LOCLX Security & OSINT Dashboard provides real-time visualization of active session telemetry.

## Dashboard Components

```
+-------------------------------------------------------------+
|                      Session Overview                       |
|   Session ID | Status | Uptime | Fixes | Discrepancy        |
+-------------------------------------------------------------+
|              Location Discrepancy & Analysis                |
|   Approximate IP Location  vs  Exact GPS Fix                |
+-------------------------------------------------------------+
|                 Live Map & Movement Trail                   |
|   Leaflet Map | Accuracy Circle | Previous Positions        |
+-------------------------------------------------------------+
|             Session History & Data Export                   |
|   JSON Export | CSV Export | Clear Ephemeral History        |
+-------------------------------------------------------------+
```

## Features

1. **Session Overview Card**: Displays real-time uptime, update counts, and discrepancy metrics.
2. **Location Discrepancy Analysis**: Displays side-by-side comparison of approximate network IP estimates versus exact browser GPS coordinates.
3. **Interactive Map**: Centered Leaflet map rendering accuracy circles, current fix markers, and movement polyline trails.
4. **Data Export Controls**: Direct downloads of JSON and CSV history buffers.
