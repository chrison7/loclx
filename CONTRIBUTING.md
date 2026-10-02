# Contributing to LOCLX

Thank you for your interest in contributing to LOCLX. This document provides guidelines, security invariants, and coding standards for developing and maintaining the LOCLX codebase.

---

## Project Purpose

LOCLX is an authorized browser-geolocation and OSINT security laboratory tool. Its goal is to provide security researchers, educators, and penetration testers with a clean, terminal-first environment for analyzing location intelligence and browser telemetry.

---

## Core Security Invariants & Boundaries

LOCLX enforces strict security and architectural invariants. Pull requests must adhere strictly to these security boundaries:

### Allowed & Supported Architecture
- **Loopback Listener:** The HTTP application server remains strictly bound to `127.0.0.1`.
- **Authorized Tunnel & Proxy Support:** Operators may expose the local listener over HTTPS using an operator-controlled reverse proxy (e.g. Nginx) or secure tunnel (`--tunnel`, `--public-url`, `LOCLX_PUBLIC_URL`).
- **Consent-Gated Geolocation:** Geolocation requests must be explicitly initiated by user interaction ("Continue" button) and approved via native browser permission prompts.

### Forbidden Practices (PRs will be rejected)
- **NO Permission Bypasses:** Attempts to bypass, manipulate, or hide native browser permission dialogs.
- **NO Stealth Tracking:** Background or silent geolocation triggers on page load.
- **NO Credential or Secret Theft:** Collection of passwords, session cookies, auth tokens, or private local files.
- **NO Session Isolation Bypasses:** Cross-session data leakage or unauthorized access to other sessions.
- **NO External Listener Binds:** Modifying the Python HTTP listener to bind to `0.0.0.0` or external public interfaces.
- **NO Arbitrary Public Admin Access:** Allowing public requests to perform session creation, deletion, or administrative actions.
- **NO Unauthorized Persistence:** Writing target coordinates, IPs, or session logs to persistent disk files without explicit operator commands.

---

## Development Setup

1. **Repository Setup:**
   ```bash
   git clone https://github.com/chrison7/loclx.git
   cd loclx
   ```

2. **Virtual Environment & Dependencies:**
   LOCLX uses only the Python standard library for core runtime execution. No external pip packages are required.
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
   ```

3. **Running LOCLX Locally:**
   ```bash
   loclx start --debug
   ```

---

## Code Organization

- `src/loclx/`: Production Python package modules.
  - `cli.py`: Command-line interface and argument parsing.
  - `server.py`: HTTP server, routing, and request dispatching.
  - `sessions.py`: Ephemeral session storage and lifecycle.
  - `security.py`: Rate limiting, header validation, and security guard checks.
  - `gps.py`: Coordinate validation, Haversine calculations, and quality classification.
  - `ipinfo.py`: IP geolocation intelligence lookup.
  - `dashboard.py`: Operator dashboard routing and telemetry.
  - `tunnel.py`: Cloudflare quick tunnel launcher.
- `web/`: Web assets (HTML, JS, CSS) served to participants and operators.
- `tests/`: Automated unit and integration test suite.
- `docs/`: Technical documentation and architecture specifications.

---

## Coding Standards

### Python Standards
- **Compatibility:** Must support Python 3.9 through Python 3.14+.
- **Standard Library Only:** Avoid adding external third-party package dependencies to `pyproject.toml`.
- **Type Annotations:** Use type hints (`from __future__ import annotations`, `Optional`, `List`, `Dict`, `Tuple`).
- **Formatting & Linting:** Clean readability, descriptive variable names, and clear docstrings.

### JavaScript & Web Standards
- **Vanilla JS:** Standard ES6+ JavaScript without external frontend frameworks (React, Vue, etc.).
- **Responsive UI:** CSS layout must render cleanly on mobile phones, tablets, and desktop browsers.
- **Explicit Consent:** Frontend scripts (`app.js`) must trigger location requests only in response to explicit user interaction.

---

## Testing Requirements

Every change or bug fix must be accompanied by automated unit or integration tests.

Run the test suite:
```bash
python -m unittest discover -s tests -v
```

Verify compilation across all modules:
```bash
python -m compileall src
```

Verify git formatting:
```bash
git diff --check
```

---

## Documentation Requirements

- Keep documentation synchronized with source code changes.
- Update relevant documents in `docs/` whenever modifying CLI parameters, API endpoints, or environment variables.
- Ensure `README.md`, `SECURITY.md`, and `docs/` reflect current v2.4.8 behavior.

---

## Commit Message Convention

Follow concise, descriptive commit messages:

- `feat: add new CLI command for export formatting`
- `fix: resolve race condition in session expiration cleanup`
- `docs: update CLI reference for v2.4.8 options`
- `test: add unit test coverage for IP fallback provider`

---

## Pull Request Requirements

Before submitting a pull request:

1. Ensure all tests pass (`python -m unittest discover -s tests -v`).
2. Ensure `python -m compileall src` completes cleanly with no errors.
3. Confirm `git diff --check` returns zero formatting errors.
4. Verify that no security invariants or boundaries have been violated.
