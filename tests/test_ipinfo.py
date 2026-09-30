import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from loclx.ipinfo import IPApiProvider, IPManager, IPWhoIsProvider  # noqa: E402


class TestIPInfo(unittest.TestCase):
    def test_provider_names(self):
        p1 = IPWhoIsProvider()
        p2 = IPApiProvider()
        self.assertEqual(p1.name(), "ipwho.is")
        self.assertEqual(p2.name(), "ipapi.co")

    def test_ip_manager(self):
        mgr = IPManager()
        self.assertEqual(len(mgr.providers), 2)


if __name__ == "__main__":
    unittest.main()
