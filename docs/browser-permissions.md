# Browser Permissions & Privacy Model

LOCLX adheres strictly to standard browser security architectures.

## Browser Geolocation Security

- **Permission Dialog**: Browsers enforce an OS/browser level permission prompt before returning any GPS data.
- **No Bypass**: LOCLX contains zero permission bypass mechanisms, zero exploits, and zero stealth tracking code.
- **Local Host Scoping**: The application binds exclusively to `127.0.0.1`, guaranteeing that data collected during lab execution remains on the local machine.

## Exposed Browser Metrics

LOCLX displays basic metrics exposed via standard web APIs:
- User-Agent string
- Platform & OS metadata
- Screen resolution & Device Pixel Ratio (DPR)
- Logical CPU core count
- Timezone and Language settings
