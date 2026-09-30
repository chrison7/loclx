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
            self.assertIn("Browser Information Demo", body)

    def test_favicon(self):
        req = urllib.request.Request(f"{self.server_url}favicon.ico")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 204)

    def test_static_assets(self):
        for path in ("app.js", "style.css"):
            req = urllib.request.Request(f"{self.server_url}{path}")
            with urllib.request.urlopen(req) as resp:
                self.assertEqual(resp.status, 200)
                body = resp.read().decode("utf-8")
                if path == "app.js":
                    self.assertIn("GEO_FAST_OPTS", body)
                    self.assertIn("GEO_PRECISE_OPTS", body)
                    self.assertIn("startHighAccuracyWatch", body)

    def test_best_gps_fix_tracking(self):
        sess = self.sm.create_session()
        # Initial coarse fix (25,000m)
        sess.update_gps({"lat": 10.1, "lon": 76.1, "accuracy": 25000.0})
        self.assertEqual(sess.best_accuracy, 25000.0)
        self.assertEqual(sess.best_fix["lat"], 10.1)

        # Better fix (800m)
        is_better, old_a, new_a = sess.update_gps({"lat": 10.12, "lon": 76.12, "accuracy": 800.0})
        self.assertTrue(is_better)
        self.assertEqual(old_a, 25000.0)
        self.assertEqual(new_a, 800.0)
        self.assertEqual(sess.best_accuracy, 800.0)
        self.assertEqual(sess.best_fix["lat"], 10.12)

        # Worse fix (12000m) - best_fix should remain 800.0 (10.12, 76.12)
        is_better_2, old_a2, new_a2 = sess.update_gps({"lat": 10.15, "lon": 76.15, "accuracy": 12000.0})
        self.assertFalse(is_better_2)
        self.assertEqual(sess.best_accuracy, 800.0)
        self.assertEqual(sess.best_fix["lat"], 10.12)

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

    def test_post_permission_denied(self):
        payload = json.dumps({"denied": True}).encode("utf-8")
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

    def test_public_admin_route_separation(self):
        proxy_headers = {"X-Forwarded-For": "203.0.113.50"}

        # Public endpoints accessible via proxy
        req_root = urllib.request.Request(self.server_url, headers=proxy_headers)
        with urllib.request.urlopen(req_root) as resp:
            self.assertEqual(resp.status, 200)

        req_js = urllib.request.Request(f"{self.server_url}app.js", headers=proxy_headers)
        with urllib.request.urlopen(req_js) as resp:
            self.assertEqual(resp.status, 200)

        # Admin/management endpoints blocked via proxy
        for admin_path in ("dashboard", "api/config", "api/diagnostics", "api/session/active"):
            req_admin = urllib.request.Request(f"{self.server_url}{admin_path}", headers=proxy_headers)
            with self.assertRaises(urllib.error.HTTPError) as cm:
                urllib.request.urlopen(req_admin)
            self.assertEqual(cm.exception.code, 403)

    def test_forwarded_ip_handling(self):
        sess = self.sm.create_session()
        proxy_headers = {
            "Content-Type": "application/json",
            "X-Forwarded-For": "198.51.100.77",
        }
        payload = json.dumps({"gps": {"lat": 10.5, "lon": 76.5, "accuracy": 10.0}}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.server_url}api/session/{sess.sid}/location",
            data=payload,
            headers=proxy_headers,
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)

        self.assertEqual(sess.client_ip, "198.51.100.77")


    def test_gps_ip_separation_and_map_links(self):
        sess = self.sm.create_session()
        payload = json.dumps({
            "gps": {"lat": 10.123456789, "lon": 76.123456789, "accuracy": 25000.0},
            "ip": {"ip": "203.0.113.1", "lat": 12.9716, "lon": 77.5946, "city": "Bengaluru"},
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.server_url}api/session/{sess.sid}/location",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)

        # Assert GPS and IP locations are strictly separated
        self.assertIsNotNone(sess.best_fix)
        self.assertEqual(sess.best_fix["lat"], 10.123456789)
        self.assertIsNotNone(sess.ip_info)
        self.assertEqual(sess.ip_info["lat"], 12.9716)

        # Assert report map links use GPS coordinates (10.123456789), NOT IP coordinates (12.9716)
        from loclx.dashboard import generate_target_report
        report = generate_target_report(sess)
        self.assertIn("10.123456789", report)
        self.assertIn("q=10.123456789,76.123456789", report)
        self.assertNotIn("12.9716", report.split("MAP LINKS")[1])

    def test_coarse_gps_labelling(self):
        sess = self.sm.create_session()
        payload = json.dumps({
            "gps": {"lat": 10.1076, "lon": 76.3516, "accuracy": 25000.0},
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{self.server_url}api/session/{sess.sid}/location",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)

        self.assertEqual(sess.best_accuracy, 25000.0)
        from loclx.gps import classify_gps_quality
        self.assertEqual(classify_gps_quality(sess.best_accuracy), "COARSE")

    def test_gps_timeout_and_unavailable_handling(self):
        sess = self.sm.create_session()
        for err_code in (1, 2, 3):
            payload = json.dumps({"denied": True, "errorCode": err_code}).encode("utf-8")
            req = urllib.request.Request(
                f"{self.server_url}api/session/{sess.sid}/location",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req) as resp:
                self.assertEqual(resp.status, 200)
                data = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(data["status"], "ok")

    def test_public_https_cors_headers(self):
        public_origin = "https://custom-tunnel.trycloudflare.com"
        req = urllib.request.Request(
            self.server_url,
            headers={"Origin": public_origin},
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), public_origin)
            self.assertEqual(resp.headers.get("Vary"), "Origin")

        req_local = urllib.request.Request(self.server_url)
        with urllib.request.urlopen(req_local) as resp:
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "http://127.0.0.1")


if __name__ == "__main__":
    unittest.main()


