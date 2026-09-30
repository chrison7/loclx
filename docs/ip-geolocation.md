# IP Geolocation Intelligence

LOCLX extracts network IP intelligence using pluggable provider abstractions.

## IPProvider Interface

```python
class IPProvider(ABC):
    @abstractmethod
    def fetch(self, ip: Optional[str] = None) -> Optional[dict[str, Any]]:
        pass
```

### Implementations

- **`IPWhoIsProvider`**: Queries `ipwho.is` API for public IP details (ISP, ASN, City, Region, Country, Lat/Lon).
- **`IPApiProvider`**: Secondary fallback provider using `ip-api.com`.

## Accuracy Disclaimer

IP geolocation resolves to ISP routing hubs, regional data centers, or city centroids. **It does NOT pinpoint physical user locations.** LOCLX explicitly labels all IP-derived coordinates as **APPROXIMATE**.
