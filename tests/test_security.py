import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from loclx.security import (
    RateLimiter,
    extract_client_ip,
    sanitize_input,
    validate_gps_payload,
    validate_json_payload,
    validate_public_url,
)


class TestSecurity(unittest.TestCase):
    def test_rate_limiter(self):
        limiter = RateLimiter(max_requests=3, window_seconds=10.0)
        self.assertTrue(limiter.is_allowed("127.0.0.1"))
        self.assertTrue(limiter.is_allowed("127.0.0.1"))
        self.assertTrue(limiter.is_allowed("127.0.0.1"))
        self.assertFalse(limiter.is_allowed("127.0.0.1"))

    def test_sanitize_input(self):
        dirty = "<script>alert('xss')</script>"
        clean = sanitize_input(dirty)
        self.assertNotIn("<script>", clean)
        self.assertIn("&lt;script&gt;", clean)

    def test_validate_json_payload(self):
        self.assertTrue(validate_json_payload({"key": "val"}))
        self.assertFalse(validate_json_payload("not a dict"))

    def test_validate_gps_payload(self):
        self.assertTrue(validate_gps_payload({"lat": 10.12, "lon": 76.12, "accuracy": 5.0}))
        # Invalid latitude
        self.assertFalse(validate_gps_payload({"lat": 95.0, "lon": 76.12, "accuracy": 5.0}))
        self.assertFalse(validate_gps_payload({"lat": -95.0, "lon": 76.12, "accuracy": 5.0}))
        # Invalid longitude
        self.assertFalse(validate_gps_payload({"lat": 10.12, "lon": 185.0, "accuracy": 5.0}))
        self.assertFalse(validate_gps_payload({"lat": 10.12, "lon": -185.0, "accuracy": 5.0}))
        # Invalid accuracy
        self.assertFalse(validate_gps_payload({"lat": 10.12, "lon": 76.12, "accuracy": -5.0}))
        # NaN rejection
        self.assertFalse(validate_gps_payload({"lat": float("nan"), "lon": 76.12, "accuracy": 5.0}))
        # Infinity rejection
        self.assertFalse(validate_gps_payload({"lat": 10.12, "lon": float("inf"), "accuracy": 5.0}))
        self.assertFalse(validate_gps_payload({"lat": float("-inf"), "lon": 76.12, "accuracy": 5.0}))

    def test_validate_public_url(self):
        # Valid HTTPS remote URL
        self.assertEqual(validate_public_url("https://example.com/"), "https://example.com")
        self.assertEqual(validate_public_url("https://YOUR_DOMAIN"), "https://YOUR_DOMAIN")

        # Localhost HTTP allowed for dev
        self.assertEqual(validate_public_url("http://localhost:8765/"), "http://localhost:8765")
        self.assertEqual(validate_public_url("http://127.0.0.1:8765"), "http://127.0.0.1:8765")

        # Insecure remote HTTP rejected
        with self.assertRaises(ValueError):
            validate_public_url("http://example.com")

        # Invalid schemes / malformed rejected
        with self.assertRaises(ValueError):
            validate_public_url("ftp://example.com")
        with self.assertRaises(ValueError):
            validate_public_url("not_a_url")

    def test_extract_client_ip(self):
        # Trusted local proxy with X-Forwarded-For
        headers = {"X-Forwarded-For": "203.0.113.195, 127.0.0.1"}
        self.assertEqual(extract_client_ip(headers, "127.0.0.1"), "203.0.113.195")

        # Trusted local proxy with X-Real-IP
        headers = {"X-Real-IP": "203.0.113.195"}
        self.assertEqual(extract_client_ip(headers, "127.0.0.1"), "203.0.113.195")

        # Untrusted direct connection - ignore spoofed headers
        headers = {"X-Forwarded-For": "203.0.113.195"}
        self.assertEqual(extract_client_ip(headers, "198.51.100.5"), "198.51.100.5")


if __name__ == "__main__":
    unittest.main()

