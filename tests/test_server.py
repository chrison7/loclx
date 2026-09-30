import json
import os
import sys
import time
import unittest
import urllib.error
import urllib.request

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from loclx.server import get_session_manager, shutdown_server, start_server_background  # noqa: E402


class TestServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd, cls.server_url = start_server_background(0)
        cls.sm = get_session_manager()

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

    def test_invalid_session_url(self):
        req = urllib.request.Request(f"{self.server_url}session/LX-FFFFFF")
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(req)
        self.assertEqual(cm.exception.code, 404)

    def test_malformed_sid_url(self):
        req = urllib.request.Request(f"{self.server_url}session/invalid-session-identifier-format")
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(req)
        self.assertIn(cm.exception.code, (400, 404))

    def test_sid_traversal_attempt(self):
        req = urllib.request.Request(f"{self.server_url}session/../../etc/passwd")
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(req)
        self.assertIn(cm.exception.code, (400, 404))

    def test_stopped_session_url(self):
        sess = self.sm.create_session()
        self.sm.stop_session(sess.sid)
        payload = json.dumps({"gps": {"lat": 10.12, "lon": 76.12, "accuracy": 5.0}}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.server_url}api/session/{sess.sid}/location",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(req)
        self.assertEqual(cm.exception.code, 409)

    def test_expired_session_url(self):
        sess = self.sm.create_session()
        sess.expires_at = time.time() - 10
        payload = json.dumps({"gps": {"lat": 10.12, "lon": 76.12, "accuracy": 5.0}}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.server_url}api/session/{sess.sid}/location",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(req)
        self.assertIn(cm.exception.code, (404, 410))

    def test_session_isolation(self):
        sess_a = self.sm.create_session()
        sess_b = self.sm.create_session()

        # Send GPS & browser for Session A
        payload_a = json.dumps({
            "gps": {"lat": 10.111111, "lon": 76.111111, "accuracy": 4.0},
            "browser": {"userAgent": "TestBrowserA", "platform": "Linux"},
            "ip": {"ip": "1.1.1.1", "city": "CityA"},
        }).encode("utf-8")
        req_a = urllib.request.Request(
            f"{self.server_url}api/session/{sess_a.sid}/location",
            data=payload_a,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req_a) as resp:
            self.assertEqual(resp.status, 200)

        # Assert Session A has data
        self.assertIsNotNone(sess_a.current_fix)
        self.assertEqual(sess_a.current_fix["lat"], 10.111111)
        self.assertIsNotNone(sess_a.browser_info)
        self.assertEqual(sess_a.browser_info.user_agent, "TestBrowserA")
        self.assertEqual(sess_a.ip_info["ip"], "1.1.1.1")

        # Assert Session B remains completely clean and isolated
        self.assertIsNone(sess_b.current_fix)
        self.assertIsNone(sess_b.browser_info)
        self.assertIsNone(sess_b.ip_info)
        self.assertEqual(sess_b.gps_updates, 0)
        self.assertEqual(len(sess_b.storage.get_history()), 0)

    def test_session_specific_report_and_qr(self):
        sess = self.sm.create_session()
        req_rep = urllib.request.Request(f"{self.server_url}api/session/{sess.sid}/report")
        with urllib.request.urlopen(req_rep) as resp:
            self.assertEqual(resp.status, 200)
            body = resp.read().decode("utf-8")
            self.assertIn(sess.sid, body)

        req_qr = urllib.request.Request(f"{self.server_url}api/session/{sess.sid}/qr")
        with urllib.request.urlopen(req_qr) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["id"], sess.sid)
            self.assertIn(sess.sid, data["url"])


if __name__ == "__main__":
    unittest.main()
