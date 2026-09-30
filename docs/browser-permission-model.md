# The geolocation permission prompt

Precise coordinates in a browser are gated by a **permission**, not by the presence of a map library or a `<script>` tag. The Geolocation API (`navigator.geolocation.getCurrentPosition` and `watchPosition`) is the only standard way a page requests them. Loclx does not call that API until you click a button in section 2. Until then the GPS panel stays empty even if the IP panel is already filled.

## What triggers the prompt

The native dialog is browser chrome. JavaScript cannot draw it or style it. It appears when:

1. The page is in a **secure context** (see [https-requirement.md](https-requirement.md)).
2. The site’s geolocation permission is in the **prompt** state (neither previously granted nor blocked for that origin).
3. The page actually calls `getCurrentPosition` or `watchPosition`.

A page load, an IP lookup, or a `fetch` to `/report` does not trigger it. Loclx’s “Request GPS — one shot” and “Start live watch” buttons are the calls that do.

If permission is already **granted** for `http://127.0.0.1:<port>`, a later call may return a fix without showing the dialog again. If it is **denied**, the call fails immediately with error code 1 (`PERMISSION_DENIED`) and no coordinates.

## Allow versus Block

**Allow** (or the equivalent “while visiting this site”) stores a grant for that origin. The success callback receives a `GeolocationPosition`: latitude, longitude, accuracy, optional altitude, and a timestamp. Loclx then POSTs that object to its own loopback `/report` handler and prints a boxed readout in the terminal.

**Block** stores a deny. The error callback runs. Loclx maps code 1 to *PERMISSION_DENIED — you declined, no coordinates available*. Codes 2 and 3 are not permission: they mean no fix (indoor / no radio) or a timeout. Blocking is origin-scoped. Reloading the page does not bypass it; you change it in the browser’s site settings.

The prompt is per **origin** (`http://127.0.0.1:8765` is not the same origin as another port). There is no loclx flag that grants access.

## Checking state with the Permissions API

Independent of requesting a fix, a page may query `navigator.permissions.query({ name: "geolocation" })`. The result’s `state` is `"granted"`, `"denied"`, or `"prompt"`. `"prompt"` means a call to Geolocation may show the dialog. `"denied"` means a call will fail without coordinates. `"granted"` means a call may obtain a fix without another dialog.

This query does **not** produce coordinates and does **not** skip the prompt. It only reads the browser’s stored decision. Loclx does not need this query to function; it is the documented way a site can *inspect* state, not a back door.

## Why a page cannot skip the prompt

The permission check lives in the browser process, outside the page. Script cannot set `granted`, forge a `GeolocationPosition`, or replace the dialog. Hiding the UI, using an iframe, or posting to your own server does not create a fix. Without a successful Geolocation callback (or an equivalent OS-level grant the browser already recorded), there are no coordinates to send.

That is why loclx’s GPS rows stay blank until you click and accept, and why IP geolocation in section 1 is a separate, coarser channel.

## Verify it yourself

On the lab page, leave GPS untouched and watch section 3: you should see IP lookups only. Click **Request GPS**. If you Allow, the GPS rows fill and the log gains a `POST` to `http://127.0.0.1:<port>/report`. If you Block, the status line shows `PERMISSION_DENIED` and that POST does not happen, because there is no fix to send. Nothing in the network log is a substitute for the native prompt.
