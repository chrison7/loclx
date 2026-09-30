# Security policy

## Scope

loclx is a localhost-only permission lab. It binds to `127.0.0.1`, holds
coordinates in memory for the life of the process, and writes nothing to
disk. There is no authentication surface, no network service reachable
off-host, and no data at rest.

## What counts as a vulnerability

The most important class of bug for this project is **any way to make
loclx collect location data from a remote person**. Examples:

- a code path that binds to a non-loopback address
- an endpoint that accepts reports from a host other than `127.0.0.1`
- a dependency or integration that tunnels the local server
- persistence that survives the process

If you find one, please open an issue. The `tests/test_guard.py` suite is
the first line of defense, but it is a pattern match — a clever bypass is
exactly the kind of finding we want to know about.

## What does not count

- "The IP lookup calls ipwho.is / ipapi.co" — that's the demonstration
- "The page can't get GPS without permission" — that's the point
- "Coordinates are visible in the terminal" — that's the intended output

## Reporting

Open a GitHub issue. There is no bounty program; this is a teaching tool
maintained in spare time.
