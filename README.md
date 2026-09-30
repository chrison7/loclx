# loclx

LOCLX is a local teaching tool: a Linux CLI that serves a single lab page on your own machine so you can see, side by side, what a plain web page can infer from an IP address versus what the browser will only reveal after you grant the Geolocation permission. It is meant to be run on the same computer you use to click through the demo. It is not a way to collect location from anyone else.

## What this demonstrates

A link by itself never sees GPS. When the lab page loads, it asks a public IP geolocation API where *this machine's public IP* appears to sit. That answer is an estimate: typically city or region scale, tied to the ISP and routing, shown to three decimal places.

Precise coordinates are a different channel. They come from the browser Geolocation API (`getCurrentPosition` / `watchPosition`) and only after an explicit permission prompt. Until you click a button and accept, the GPS panel stays empty. After a fix, the page and the terminal show the haversine gap between the IP estimate and the GPS reading — the practical difference between “a link loaded” and “permission was granted.”

## Install / run

Python 3.9+ from the operating system is enough. There is nothing to pip-install.

```bash
git clone https://github.com/chrison7/loclx.git
cd loclx
chmod +x loclx
./loclx
```

Optional flags:

```bash
./loclx --port 8765
./loclx --no-browser
```

The server listens on `http://127.0.0.1:<port>/`. If the preferred port is busy it tries the next two ports, then an OS-assigned port, and prints the URL it actually bound.

## Secure context

The Geolocation API requires a [secure context](https://developer.mozilla.org/en-US/docs/Web/Security/Secure_Contexts). `http://127.0.0.1` (and `localhost`) count as secure, so this lab works without HTTPS when you open the printed loopback URL in a browser on the same machine.

## What this is not

This is not remote tracking. There is no tunnel, no session, no share link, and no persistence. Coordinates and IP fields live in process memory and disappear when the process exits. Nothing is written to disk. The bind address is the module-level constant `127.0.0.1`; there is no flag, environment variable, or config value to change it.

## Verifying the claims

Section 3 of the lab page is a live log of outbound requests from that page. You should see the IP lookups and a `POST` to `http://127.0.0.1:<port>/report` after a GPS fix — and you should not see coordinates sent anywhere else.

Read the source in `loclx`. The geolocation success path uses `fetch()` only to POST the fix to the loopback `/report` endpoint. The IP lookup calls are a separate path and do not include GPS coordinates.

## Further reading

- [Why IP geolocation is not a person](docs/ip-vs-gps.md) — prefix databases, mobile/VPN/CGNAT, and the `delta_m` gap.
- [Secure context and geolocation](docs/https-requirement.md) — why `http://127.0.0.1` is enough and TLS is not required here.
- [The geolocation permission prompt](docs/browser-permission-model.md) — Allow/Block, the Permissions API, and why the prompt cannot be skipped.
