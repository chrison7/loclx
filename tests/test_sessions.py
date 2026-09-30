import os
import sys
import time
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from loclx.sessions import Session, SessionManager  # noqa: E402


class TestSessions(unittest.TestCase):
    def setUp(self):
        self.sm = SessionManager(default_timeout=2.0)

    def test_create_session(self):
        session = self.sm.create_session()
        self.assertTrue(session.sid.startswith("LX-"))
        self.assertEqual(session.status, "ACTIVE")
        self.assertEqual(session.gps_updates, 0)

    def test_session_expiration(self):
        session = self.sm.create_session()
        self.assertFalse(session.is_expired())
        time.sleep(2.1)
        self.assertTrue(session.is_expired())
        self.assertIsNone(self.sm.get_session(session.sid))

    def test_stop_session(self):
        session = self.sm.create_session()
        self.assertTrue(self.sm.stop_session(session.sid))
        self.assertEqual(session.status, "STOPPED")

    def test_delete_session(self):
        session = self.sm.create_session()
        self.assertTrue(self.sm.delete_session(session.sid))
        self.assertIsNone(self.sm.get_session(session.sid))

    def test_update_gps(self):
        session = self.sm.create_session()
        session.update_gps({"lat": 10.123456, "lon": 76.123456, "accuracy": 10.0, "altitude": 20.0})
        self.assertEqual(session.gps_updates, 1)
        self.assertEqual(session.current_fix["lat"], 10.123456)
        self.assertEqual(session.current_fix["lon"], 76.123456)


if __name__ == "__main__":
    unittest.main()
