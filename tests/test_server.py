import json
import os
import sys
import unittest
import urllib.request

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from loclx.server import shutdown_server, start_server_background  # noqa: E402


class TestServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd, cls.server_url = start_server_background(0)

    @classmethod
    def tearDownClass(cls):
        shutdown_server()

    def test_get_root(self):
        req = urllib.request.Request(self.server_url)
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            body = resp.read().decode("utf-8")
            self.assertIn("LOCLX", body)

    def test_get_dashboard(self):
        req = urllib.request.Request(f"{self.server_url}dashboard")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            body = resp.read().decode("utf-8")
            self.assertIn("LOCLX Security Dashboard", body)

    def test_api_active_session(self):
        req = urllib.request.Request(f"{self.server_url}api/session/active")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data["id"].startswith("LX-"))

    def test_post_location(self):
        payload = json.dumps({"gps": {"lat": 10.123456, "lon": 76.123456, "accuracy": 5.0}}).encode("utf-8")
        req = urllib.request.Request(f"{self.server_url}report", data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "ok")


if __name__ == "__main__":
    unittest.main()
