# Secure context and geolocation

Browsers do not expose the Geolocation API to arbitrary pages. The API is restricted to a [secure context](https://developer.mozilla.org/en-US/docs/Web/Security/Secure_Contexts): an environment the browser treats as authenticated and isolated enough that granting location is not silently leaked to an unencrypted hop.

In ordinary browsing that means **HTTPS** (or a secure ancestor such as an HTTPS iframe chain). A page served as `http://example.com/…` is not a secure context. `navigator.geolocation` is missing or the calls fail, and there is no useful permission prompt, because the transport itself is not trusted with the result.

## Localhost is an exception

The HTML specification and browser implementations treat **loopback** as potentially trustworthy even without TLS:

- `http://127.0.0.1`
- `http://localhost` (and `*.localhost` in current browsers)

Packets to `127.0.0.1` do not leave the machine. There is no network attacker on that path in the sense the secure-context rules are designed to block. The browser therefore counts these origins as secure contexts. `getCurrentPosition` and `watchPosition` are available, and the native permission prompt can appear.

That is a **local** exception, not a general “HTTP is fine” rule. The same page copied to a LAN IP, a public hostname, or any non-loopback `http://` origin is not a secure context and geolocation will not run.

## Why loclx uses HTTP on 127.0.0.1

Loclx binds only to `127.0.0.1` and serves `http://127.0.0.1:<port>/`. Because that origin is a secure context, the lab does not need certificates, a local CA, or HTTPS. TLS would not change the permission model or the IP-versus-GPS demonstration; it would only add machinery unrelated to the lesson.

If you open the printed URL on the same machine, geolocation is allowed to *ask*. Whether coordinates appear still depends on the permission prompt, not on TLS.

## Verify it yourself

Load the lab from the URL loclx prints (`http://127.0.0.1:<port>/`). Section 2’s GPS buttons can trigger the browser prompt without HTTPS. Section 3’s network log should show IP lookups and a loopback `POST /report` after a fix — still on `127.0.0.1`, not on a remote TLS host. If you instead open the HTML from a non-loopback `http://` origin, the Geolocation API should refuse; that contrast is the secure-context rule, not a loclx setting.
