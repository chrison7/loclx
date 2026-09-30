# Changelog

## v2.1.1

Important bugfix release establishing a strict **terminal-first** architecture.

### Fixed
- **Browser Auto-Launch Removal**: Completely removed `webbrowser` import and all automatic browser opening calls across startup, `loclx dashboard`, and menu options.
- **Terminal Startup Output**: Updated startup banner and loop output to clearly communicate that browser auto-launching is disabled and server URLs must be opened manually.
- **`--no-browser` Flag**: Deprecated `--no-browser` flag in CLI parser, making zero browser auto-launching the permanent default.
- **Subcommand Updates**: `loclx dashboard`, `loclx map`, and `loclx earth` now print URLs directly to terminal for manual user navigation.
- **Regression Unit Tests**: Added regression tests in `tests/test_cli.py` ensuring `cli.py` contains no `webbrowser` import and does not trigger browser opening.

## v2.1.0

Major release transforming LOCLX into a professional Linux security & OSINT laboratory tool.

## v2.0.0

Major architecture upgrade transforming LOCLX into an advanced consent-based Linux security & OSINT laboratory tool.

## v1.0.1

Documentation and security policy release.

## v1.0.0

First release of LOCLX localhost demonstration.
