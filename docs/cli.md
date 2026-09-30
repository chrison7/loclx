# LOCLX CLI Reference Guide (v2.1.0)

LOCLX provides a dual interface: a rich, ANSI-grouped interactive terminal menu and standard CLI subcommands.

## Command Syntax

```bash
loclx [flags] [subcommand] [arguments]
```

## Global Options

| Option | Type | Description |
| :--- | :--- | :--- |
| `--port <int>` | Integer | Preferred HTTP server port on `127.0.0.1` (default: 8765) |
| `--no-browser` | Flag | Disable auto-launching default web browser on startup |
| `--lab` | Flag | Run educational self-contained demonstration mode |
| `--debug` | Flag | Enable verbose debug log output |
| `--version` | Flag | Display LOCLX version and exit |
| `--help` | Flag | Display usage menu and security epilog |

## Subcommands

### 1. `loclx`
Launches the interactive TTY menu loop with auto-detected terminal width formatting.

### 2. `loclx start`
Starts the HTTP server and creates a new active session token.

### 3. `loclx session list`
Lists all non-expired active sessions (`LX-XXXXXX`), creation timestamp, and GPS update counts.

### 4. `loclx session info <id>`
Displays detailed breakdown of session status, duration, latest GPS fix, approximate IP info, and browser capabilities.

### 5. `loclx session stop <id>`
Stops location ingestion for the specified session.

### 6. `loclx dashboard`
Opens the interactive web security dashboard (`http://127.0.0.1:8765/dashboard`).

### 7. `loclx gps`
Outputs the current session's latest GPS fix coordinates, accuracy radius, altitude, and timestamp.

### 8. `loclx ip`
Fetches and displays network IP intelligence, explicitly labeled as **APPROXIMATE**.

### 9. `loclx browser`
Displays client environment properties reported by the web browser.

### 10. `loclx history`
Displays bounded in-memory location history logs for the active session.

### 11. `loclx export <id> [--format json|csv]`
Exports session location history records to JSON or CSV format.

### 12. `loclx diagnostics`
Runs environment health checks (Python 3.9+, OS, 127.0.0.1 loopback bind, port availability, web assets, session engine, IP APIs).

### 13. `loclx config`
Displays effective configuration environment variables and loopback invariants.

### 14. `loclx qr`
Renders a pure-Python ASCII QR code in the terminal encoding the local server URL (`http://127.0.0.1:8765/`).
