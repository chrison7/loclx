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
                    self.assertIn("GEO_WATCH_OPTS", body)
                    self.assertIn("GEO_PRECISE_OPTS", body)
                    self.assertIn("startHighAccuracyWatch", body)
                    self.assertIn("getLocationPermissionState", body)
                    self.assertIn("enableContinueButton", body)
                    self.assertIn("runWatchFallback", body)
                    self.assertIn("runPreciseFallback", body)
                    self.assertIn("clearWatchSafely", body)
                    self.assertIn("isValidCoordinate", body)

    def test_invalid_gps_payloads(self):
        sess = self.sm.create_session()
        invalid_gps_cases = [
            {"lat": 100.0, "lon": 76.0},          # Invalid latitude (>90)
            {"lat": -95.0, "lon": 76.0},          # Invalid latitude (<-90)
            {"lat": 10.0, "lon": 190.0},          # Invalid longitude (>180)
            {"lat": 10.0, "lon": -200.0},         # Invalid longitude (<-180)
            {"lat": "NaN", "lon": 76.0},          # Non-numeric string
            {"lat": 10.0, "lon": 76.0, "accuracy": -5.0}, # Negative accuracy
            {"lat": 10.0},                        # Missing lon
            {"lon": 76.0},                        # Missing lat
            "not-a-dict",                         # Malformed gps type
        ]

        for bad_gps in invalid_gps_cases:
            payload = json.dumps({"gps": bad_gps}).encode("utf-8")
            req = urllib.request.Request(
                f"{self.server_url}api/session/{sess.sid}/location",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with self.assertRaises(urllib.error.HTTPError) as cm:
                urllib.request.urlopen(req)
            self.assertEqual(cm.exception.code, 400)

    def test_browser_and_ip_only_payloads(self):
        sess = self.sm.create_session()

        # Browser-only payload
        b_payload = json.dumps({"browser": {"userAgent": "TestBrowser"}}).encode("utf-8")
        req_b = urllib.request.Request(
            f"{self.server_url}api/session/{sess.sid}/location",
            data=b_payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req_b) as resp:
            self.assertEqual(resp.status, 200)

        # IP-only payload
        ip_payload = json.dumps({"ip": {"ip": "1.1.1.1", "city": "TestCity"}}).encode("utf-8")
        req_ip = urllib.request.Request(
            f"{self.server_url}api/session/{sess.sid}/location",
            data=ip_payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req_ip) as resp:
            self.assertEqual(resp.status, 200)

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
            self.assertIn("LOCLX Security &amp; OSINT Dashboard", body)
            self.assertIn("https://unpkg.com/leaflet@1.9.4/dist/leaflet.js", body)
            self.assertIn("Browser GPS — Permission Based", body)
            self.assertIn("IP Geolocation — Approximate", body)

    def test_dashboard_api_and_session_isolation(self):
        sess_a = self.sm.create_session()
        sess_b = self.sm.create_session()

        # Update sess_a with GPS and IP
        sess_a.update_gps({"lat": 10.123456, "lon": 76.123456, "accuracy": 15.0})
        sess_a.set_ip_info({"ip": "1.2.3.4", "lat": 12.0, "lon": 77.0, "city": "TestCity", "country": "TestCountry"})

        # Call GET /api/session/LX-A.../dashboard for sess_a
        req_a = urllib.request.Request(f"{self.server_url}api/session/{sess_a.sid}/dashboard")
        with urllib.request.urlopen(req_a) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["session"]["id"], sess_a.sid)
            self.assertEqual(data["gps"]["current"]["lat"], 10.123456)
            self.assertEqual(data["ip"]["ip"], "1.2.3.4")
            self.assertIsNotNone(data["comparison"])
            self.assertIn("km coordinate difference", data["comparison"]["text"])

        # Call GET /api/session/LX-B.../dashboard for sess_b (assert sess_a data is NOT exposed)
        req_b = urllib.request.Request(f"{self.server_url}api/session/{sess_b.sid}/dashboard")
        with urllib.request.urlopen(req_b) as resp:
            self.assertEqual(resp.status, 200)
            data_b = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data_b["session"]["id"], sess_b.sid)
            self.assertIsNone(data_b["gps"]["current"])
            self.assertIsNone(data_b["ip"])
            self.assertIsNone(data_b["comparison"])

        # Test invalid SID -> 400
        req_invalid = urllib.request.Request(f"{self.server_url}api/session/invalid-sid-format/dashboard")
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(req_invalid)
        self.assertEqual(cm.exception.code, 400)

        # Test non-existent SID -> 404
        req_nonexistent = urllib.request.Request(f"{self.server_url}api/session/LX-FFFFFF/dashboard")
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(req_nonexistent)
        self.assertEqual(cm.exception.code, 404)

        # Test export format json & csv for sess_a
        req_json = urllib.request.Request(f"{self.server_url}api/session/{sess_a.sid}/export?format=json")
        with urllib.request.urlopen(req_json) as resp:
            self.assertEqual(resp.status, 200)
            history = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(len(history), 1)

        req_csv = urllib.request.Request(f"{self.server_url}api/session/{sess_a.sid}/export?format=csv")
        with urllib.request.urlopen(req_csv) as resp:
            self.assertEqual(resp.status, 200)
            csv_text = resp.read().decode("utf-8")
            self.assertIn("timestamp,lat,lon,accuracy", csv_text)
            self.assertIn("10.123456", csv_text)

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

    def test_participant_page_requirements(self):
        """1. PARTICIPANT HTML TESTS: Verify landing page structure & JS logic statically."""
        req = urllib.request.Request(self.server_url)
        with urllib.request.urlopen(req) as resp:
            html = resp.read().decode("utf-8")

        req_js = urllib.request.Request(f"{self.server_url}app.js")
        with urllib.request.urlopen(req_js) as resp:
            js = resp.read().decode("utf-8")

        # Explicit continue action
        self.assertIn("btn-continue", html)
        self.assertIn("Continue", html)
        self.assertIn("addEventListener", js)
        self.assertIn("click", js)

        # Geolocation calls are inside functions triggered on click, NOT top-level page load
        # Top-level DOMContentLoaded only collects browser info & looks up IP
        self.assertIn("DOMContentLoaded", js)
        self.assertIn("lookupIp()", js)
        self.assertIn("postPayload({ browser: bInfo })", js)
        # Ensure getCurrentPosition and watchPosition are inside function definitions, not top-level execution
        self.assertIn("function startDemo", js)
        self.assertIn("navigator.geolocation", js)
        self.assertIn("getCurrentPosition", js)
        self.assertIn("watchPosition", js)
        self.assertIn("getLocationPermissionState", js)
        self.assertIn("isValidCoordinate", js)
        self.assertIn("clearWatchSafely", js)
        self.assertNotIn("<iframe", html)
        self.assertNotIn("<iframe", js)

    def test_gps_quality_sequence(self):
        """3. GPS QUALITY: Test sequence 25000m -> 5000m -> 800m -> 50m and verify best_fix tracking."""
        sess = self.sm.create_session()
        sequence = [25000.0, 5000.0, 800.0, 50.0]
        lat_base = 10.0
        lon_base = 76.0

        for idx, acc in enumerate(sequence):
            lat = lat_base + (idx * 0.01)
            lon = lon_base + (idx * 0.01)
            payload = json.dumps({"gps": {"lat": lat, "lon": lon, "accuracy": acc}}).encode("utf-8")
            req = urllib.request.Request(
                f"{self.server_url}api/session/{sess.sid}/location",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req) as resp:
                self.assertEqual(resp.status, 200)

            self.assertEqual(sess.best_accuracy, acc)
            self.assertEqual(sess.best_fix["lat"], lat)
            self.assertEqual(sess.best_fix["lon"], lon)

        # Now send a worse fix (20,000m)
        worse_payload = json.dumps({"gps": {"lat": 10.99, "lon": 76.99, "accuracy": 20000.0}}).encode("utf-8")
        req_worse = urllib.request.Request(
            f"{self.server_url}api/session/{sess.sid}/location",
            data=worse_payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req_worse) as resp:
            self.assertEqual(resp.status, 200)

        # best_fix must remain 50m fix (lat=10.03, lon=76.03)
        self.assertEqual(sess.best_accuracy, 50.0)
        self.assertEqual(sess.best_fix["lat"], 10.03)
        self.assertEqual(sess.best_fix["lon"], 76.03)

        # Test accuracy = 0
        zero_acc_payload = json.dumps({"gps": {"lat": 10.04, "lon": 76.04, "accuracy": 0.0}}).encode("utf-8")
        req_zero = urllib.request.Request(
            f"{self.server_url}api/session/{sess.sid}/location",
            data=zero_acc_payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req_zero) as resp:
            self.assertEqual(resp.status, 200)
        self.assertEqual(sess.best_accuracy, 0.0)
        self.assertEqual(sess.best_fix["lat"], 10.04)

        # Test missing accuracy (None)
        missing_acc_payload = json.dumps({"gps": {"lat": 10.05, "lon": 76.05}}).encode("utf-8")
        req_missing = urllib.request.Request(
            f"{self.server_url}api/session/{sess.sid}/location",
            data=missing_acc_payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req_missing) as resp:
            self.assertEqual(resp.status, 200)

    def test_dashboard_xss_protection(self):
        """6. DASHBOARD XSS: Verify script tags in browser fields are sanitized and safely output."""
        sess = self.sm.create_session()
        xss_payload = json.dumps({
            "browser": {
                "userAgent": "<script>alert(1)</script>",
                "platform": "<img src=x onerror=alert(1)>",
                "browser": "<b>InjectedBrowser</b>",
            }
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.server_url}api/session/{sess.sid}/location",
            data=xss_payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)

        # Verify Dashboard API returns valid JSON
        req_dash = urllib.request.Request(f"{self.server_url}api/session/{sess.sid}/dashboard")
        with urllib.request.urlopen(req_dash) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["session"]["id"], sess.sid)
            self.assertIn("alert(1)", data["browser"]["userAgent"])

        # Verify sanitize_input escapes HTML elements according to existing design
        from loclx.security import sanitize_input
        self.assertEqual(sanitize_input("<script>alert(1)</script>"), "&lt;script&gt;alert(1)&lt;/script&gt;")
        self.assertEqual(sanitize_input("<img src=x onerror=alert(1)>"), "&lt;img src=x onerror=alert(1)&gt;")

    def test_exports_comprehensive(self):
        """7. EXPORTS: Test JSON and CSV export with multiple history entries and session boundaries."""
        sess_a = self.sm.create_session()
        sess_b = self.sm.create_session()

        # Update Session A with multiple GPS fixes, IP, and browser data
        for i in range(3):
            payload = json.dumps({
                "gps": {"lat": 10.1000 + i * 0.01, "lon": 76.1000 + i * 0.01, "accuracy": 10.0 + i},
                "browser": {"userAgent": f"BrowserA-{i}"},
                "ip": {"ip": "1.1.1.1", "city": "CityA"},
            }).encode("utf-8")
            req = urllib.request.Request(
                f"{self.server_url}api/session/{sess_a.sid}/location",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req) as resp:
                self.assertEqual(resp.status, 200)

        # Update Session B with 1 fix
        payload_b = json.dumps({
            "gps": {"lat": 20.2000, "lon": 80.2000, "accuracy": 5.0},
            "browser": {"userAgent": "BrowserB"},
        }).encode("utf-8")
        req_b = urllib.request.Request(
            f"{self.server_url}api/session/{sess_b.sid}/location",
            data=payload_b,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req_b) as resp:
            self.assertEqual(resp.status, 200)

        # Export Session A JSON
        req_json = urllib.request.Request(f"{self.server_url}api/session/{sess_a.sid}/export?format=json")
        with urllib.request.urlopen(req_json) as resp:
            self.assertEqual(resp.status, 200)
            data_json = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(len(data_json), 3)
            # Ensure Session B coordinates (20.2000) are NOT in Session A export
            for entry in data_json:
                self.assertNotEqual(entry["lat"], 20.2000)

        # Export Session A CSV
        req_csv = urllib.request.Request(f"{self.server_url}api/session/{sess_a.sid}/export?format=csv")
        with urllib.request.urlopen(req_csv) as resp:
            self.assertEqual(resp.status, 200)
            csv_lines = resp.read().decode("utf-8").strip().splitlines()
            self.assertGreaterEqual(len(csv_lines), 4) # header + 3 rows
            self.assertTrue(csv_lines[0].startswith("timestamp,lat,lon,accuracy"))
            self.assertIn("10.1", csv_lines[1])
            self.assertNotIn("20.2", "\n".join(csv_lines))

    def test_realistic_http_e2e_workflow(self):
        """13. REALISTIC END-TO-END TEST: Simulate full browser -> server -> session -> dashboard workflow."""
        # Step 1: Create session
        sess = self.sm.create_session()
        self.assertEqual(sess.status, "ACTIVE")

        # Step 2: GET participant landing page & static JS
        req_html = urllib.request.Request(f"{self.server_url}session/{sess.sid}")
        with urllib.request.urlopen(req_html) as resp:
            self.assertEqual(resp.status, 200)
            html_content = resp.read().decode("utf-8")
            self.assertIn("Browser Information", html_content)

        req_js = urllib.request.Request(f"{self.server_url}app.js")
        with urllib.request.urlopen(req_js) as resp:
            self.assertEqual(resp.status, 200)

        # Step 3: Send initial browser connection payload (simulating DOMContentLoaded)
        b_payload = json.dumps({
            "browser": {
                "userAgent": "Mozilla/5.0 (Android 14; Mobile; rv:124.0) Gecko/124.0 Firefox/124.0",
                "platform": "Android",
                "browser": "Firefox Mobile",
                "deviceType": "Mobile"
            },
            "ip": {"ip": "203.0.113.88", "city": "Kochi", "country": "India", "lat": 9.9312, "lon": 76.2673}
        }).encode("utf-8")
        req_post1 = urllib.request.Request(
            f"{self.server_url}api/session/{sess.sid}/location",
            data=b_payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_post1) as resp:
            self.assertEqual(resp.status, 200)

        self.assertTrue(sess.connected)
        self.assertEqual(sess.browser_info.browser, "Firefox Mobile")

        # Step 4: Send browser GPS fix payload (simulating Continue click and GPS fix acquisition)
        gps_payload = json.dumps({
            "gps": {
                "lat": 9.965432100,
                "lon": 76.245678900,
                "accuracy": 8.0,
                "altitude": 15.0,
                "speed": 0.5,
                "heading": 90.0,
                "timestamp": "12:34:56 PM"
            }
        }).encode("utf-8")
        req_post2 = urllib.request.Request(
            f"{self.server_url}api/session/{sess.sid}/location",
            data=gps_payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_post2) as resp:
            self.assertEqual(resp.status, 200)

        # Step 5: Verify dashboard API state
        req_dash = urllib.request.Request(f"{self.server_url}api/session/{sess.sid}/dashboard")
        with urllib.request.urlopen(req_dash) as resp:
            self.assertEqual(resp.status, 200)
            dash_data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(dash_data["session"]["id"], sess.sid)
            self.assertEqual(dash_data["gps"]["current"]["lat"], 9.965432100)
            self.assertEqual(dash_data["ip"]["ip"], "203.0.113.88")
            self.assertIsNotNone(dash_data["comparison"])

        # Step 6: Export session data
        req_exp = urllib.request.Request(f"{self.server_url}api/session/{sess.sid}/export?format=json")
        with urllib.request.urlopen(req_exp) as resp:
            self.assertEqual(resp.status, 200)
            exp_data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(len(exp_data), 1)

        # Step 7: Stop session and verify subsequent location POST returns 409
        self.sm.stop_session(sess.sid)
        req_stopped = urllib.request.Request(
            f"{self.server_url}api/session/{sess.sid}/location",
            data=gps_payload,
            headers={"Content-Type": "application/json"}
        )
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(req_stopped)
        self.assertEqual(cm.exception.code, 409)


if __name__ == "__main__":
    unittest.main()
