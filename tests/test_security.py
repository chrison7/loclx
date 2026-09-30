import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from loclx.security import RateLimiter, sanitize_input, validate_gps_payload, validate_json_payload  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
