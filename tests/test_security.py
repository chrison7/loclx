import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from loclx.security import RateLimiter, sanitize_input, validate_json_payload  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
