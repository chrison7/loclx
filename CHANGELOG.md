# Changelog

## v2.4.0

Major release transforming the default user experience into a streamlined, Hound-style terminal capture workflow while maintaining internal session isolation and token security.

### Added / Changed
- **Hound-Style Stream Workflow**: Default execution (`./loclx`) removes the interactive main menu and directly starts the listener, outputs local/tunnel URLs, enters live target waiting state, and streams connection events and GPS fixes directly.
- **Optional Tunnel Integration**: Added `--tunnel` option to easily configure public lab domains while keeping tunnel auth credentials isolated.
- **Direct Target Connection & Report Streaming**: Automatically renders Target Information, Device/Browser parameters, Permission-granted GPS fixes, Map links, and Compact Information Reports upon target connection.
- **Live GPS Watch Updates**: Continuous position tracking with `watchPosition()` rendering live update lines directly to console.
- **Direct Dashboard Links**: Dashboard printed per capture link (`/dashboard/<TOKEN>`) featuring map controls, IP marker, and IP-to-GPS connection line.

Major release introducing Advanced Location Intelligence, 3D Google Earth Visualization, GeoURI mapping integration, directional bearing calculation, and enhanced location analysis.

### Added
- **Advanced Map & Earth Intelligence**: Expanded mapping capabilities with dedicated `loclx map <SESSION_ID>` and `loclx earth <SESSION_ID>` subcommands for high-precision GPS and IP coordinates.
- **GeoURI Integration**: Generates standardized `geo:lat,lon?z=16` URIs for native Linux GIS applications and mobile mapping.
- **Directional Bearing & Heading Analysis**: Calculates compass bearing (0-360°) and cardinal direction (e.g., `45° NE`) between IP estimate and browser GPS fix.
- **Google Earth 3D Visualization**: Dedicated 3D location view generator (`loclx earth <SESSION_ID>`) providing direct search URLs for Google Earth Web and desktop GIS software.
- **Enhanced Target Intelligence Reports**: Integrated GeoURI and compass bearing metrics into `loclx report <SESSION_ID>` target intelligence summaries.

## v2.2.0

Major release hardening session security, session isolation, multi-session workflow, and terminal target handling.

## v2.1.2

Session-centric terminal OSINT workflow release inspired by information-gathering tools.

## v2.1.1

Important bugfix release establishing a strict **terminal-first** architecture.

## v2.1.0

Major release transforming LOCLX into a professional Linux security & OSINT laboratory tool.

## v2.0.0

Major architecture upgrade transforming LOCLX into an advanced consent-based Linux security & OSINT laboratory tool.

## v1.0.1

Documentation and security policy release.

## v1.0.0

First release of LOCLX localhost demonstration.
