# Changelog

## v1.0.0

First release.

loclx is a single-file Python CLI that serves a web page on `127.0.0.1`
and demonstrates the gap between IP-based geolocation and browser-granted
GPS. Open the page, watch the IP panel fill in immediately, then click
**Request GPS** and accept the browser prompt to see the actual fix
appear — alongside the distance between the two.

### What it does

- Serves one page on `127.0.0.1` (bind address is a hardcoded constant)
- Looks up your public IP via ipwho.is, falling back to ipapi.co
- Waits for the browser's native location prompt before obtaining GPS
- Prints a boxed fix readout and the IP-vs-GPS distance to your terminal
- Draws the reported accuracy as an inline SVG circle (no map tiles)
- Logs every outbound request on the page so claims are checkable

### What it does not do

- No tunnel, no remote sessions, no share links
- No phone-number lookup (that capability doesn't exist for civilians)
- No persistence — coordinates live in memory and vanish on exit
- No dependencies beyond the Python standard library

### Requirements

Python 3.9+ on Linux, macOS, or Windows. No `pip install` needed.

### Run

```bash
chmod +x loclx
./loclx
```
