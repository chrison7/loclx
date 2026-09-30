import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from loclx.qrcode import generate_ascii_qr  # noqa: E402


class TestQRCode(unittest.TestCase):
    def test_generate_ascii_qr(self):
        url = "http://127.0.0.1:8765/"
        qr_output = generate_ascii_qr(url)
        self.assertIsInstance(qr_output, str)
        self.assertTrue(len(qr_output) > 50)
        self.assertIn("┌", qr_output)


if __name__ == "__main__":
    unittest.main()
