# Why IP geolocation is not a person

An IP geolocation lookup answers a different question than GPS. It asks where a *public address block* is believed to live in a commercial or community database, not where a device’s antenna is.

Those databases are built from RIR allocations, ISP announcements, WHOIS, and probe traffic. The smallest unit is almost always a prefix: a range of addresses that share a routing announcement. The location attached to that prefix is typically a city, a region, or an ISP point of presence (a backbone site, a CGNAT pool, a peering hotel). It is not a street address and it is not a person. Several households, phones, and servers can sit behind the same public IP at once.

## Why the estimate is coarse

The public IP is an identifier on the *path*, not a sensor on the *device*. Anything that separates the subscriber from a unique, stable, geographically tight address widens the error.

**Mobile networks.** A handset usually does not own a globally routable address. Traffic leaves through carrier-grade NAT. The address the rest of the internet sees belongs to a pool that may sit in another city from the radio the phone is using. The pool can be reassigned as the device moves or as the operator load-balances.

**VPNs and proxies.** A lookup sees the *exit* of the tunnel. The database will place that IP at the VPN provider’s node. The physical machine can be on another continent. Loclx will still report that exit as “the IP location,” because that is what a page loaded from a link can observe.

**Carrier NAT and shared last miles.** Even on fixed broadband, many operators put customers behind a shared public address. The database entry for that address often points at the operator’s metro PoP, not the street cabinet, and not the building.

Commercial APIs still return a latitude and longitude. Those numbers are a centroid for the prefix (sometimes the city hall, sometimes the PoP). Loclx prints them to three decimal places to make the coarseness visible: that precision is already finer than the data typically supports.

## Why 5–50 km is a typical gap

A GPS fix is a measurement from the device (radio, Wi-Fi assist, or both) after the browser permission prompt. An IP estimate is a guess about a prefix. The haversine distance between those two points is often on the order of **5–50 km**: same metro area, wrong neighborhood, or a PoP one city over. It can be smaller on a well-geolocated residential prefix, and much larger through a VPN or a national mobile pool.

Loclx computes that distance after a fix arrives. The CLI prints it as the line *IP geolocation was off by … from this fix*, using the in-memory `delta_m` value (metres between the IP estimate and the last GPS coordinates). Treat that number as the running example for this file: it is the gap between “a link loaded” and “permission was granted,” not a claim that either figure is a legal or forensic location.

## Verify it yourself

Open the lab page, let section 1 fill from the IP lookup, then grant GPS in section 2. Section 3 (network activity) lists every outbound request from the page. You should see the IP API call(s) and, after a fix, a `POST` to `http://127.0.0.1:<port>/report`. GPS coordinates are not included in the IP lookup. The same `delta_m` shown in the terminal is the distance between those two independent sources.
