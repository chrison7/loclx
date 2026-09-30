# Contributing to loclx

loclx is a **localhost-only teaching tool**. It exists to demonstrate one
thing: a web link reveals only an IP-based location estimate, and precise
coordinates require an explicit browser permission grant.

## The one rule

**The server binds to `127.0.0.1`. This is not negotiable.**

`BIND_ADDR` is a module-level constant in `loclx` and there is no flag,
environment variable, or config file that changes it. Pull requests that
add any of the following will be closed without review:

- a `--host` flag, a `HOST` env var, or any way to bind elsewhere
- a tunnel integration (ngrok, cloudflared, localtunnel, serveo, `ssh -R`)
- sessions, session IDs, share links, or QR codes
- persistence (SQLite, JSON state files, log files on disk)
- a map, movement history, or geofencing
- any code path that sends coordinates to a host other than `127.0.0.1`

The reason is simple: the moment a second person can be on the receiving
end of a link, this stops being a lab and becomes a tracking tool. That's
the line the project is drawn around.

## What is welcome

- Documentation improvements, especially clearer explanations of the
  browser permission model
- Additional locally-drawn visualizations of the accuracy radius
- More IP-lookup sources for the side-by-side comparison
- Tests that strengthen the guard in `tests/test_guard.py`

## Running the tests

```bash
python -m unittest discover -s tests -v
```
