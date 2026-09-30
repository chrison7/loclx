import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from loclx.gps import GPSFix, format_accuracy, format_altitude, haversine_m, validate_coordinates  # noqa: E402


class TestGPS(unittest.TestCase):
    def test_validate_coordinates(self):
        self.assertTrue(validate_coordinates(10.123456, 76.123456))
        self.assertTrue(validate_coordinates(-90.0, 180.0))
        self.assertFalse(validate_coordinates(95.0, 76.0))
        self.assertFalse(validate_coordinates("invalid", 76.0))

    def test_haversine_m(self):
        dist = haversine_m(0.0, 0.0, 0.0, 1.0)
        self.assertAlmostEqual(dist, 111195.0, delta=1000)

    def test_format_accuracy(self):
        self.assertEqual(format_accuracy(8.0), "±8 m")
        self.assertEqual(format_accuracy(12.5), "±12.5 m")
        self.assertEqual(format_accuracy(None), "n/a")

    def test_format_altitude(self):
        self.assertEqual(format_altitude(34.0), "34 m")
        self.assertEqual(format_altitude(None), "n/a")

    def test_gps_fix_object(self):
        fix = GPSFix(latitude=10.1, longitude=76.1, accuracy=5.0)
        d = fix.to_dict()
        self.assertEqual(d["lat"], 10.1)
        self.assertEqual(d["lon"], 76.1)
        self.assertEqual(d["accuracy"], 5.0)


if __name__ == "__main__":
    unittest.main()
