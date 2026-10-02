import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from loclx.gps import GPSFix, classify_gps_quality, format_accuracy, format_altitude, generate_map_urls, haversine_m, validate_coordinates  # noqa: E402


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
        self.assertEqual(format_accuracy(25000.0), "±25 km")
        self.assertEqual(format_accuracy(None), "n/a")


    def test_classify_gps_quality(self):
        self.assertEqual(classify_gps_quality(15.0), "HIGH")
        self.assertEqual(classify_gps_quality(50.0), "GOOD")
        self.assertEqual(classify_gps_quality(500.0), "MODERATE")
        self.assertEqual(classify_gps_quality(5000.0), "LOW")
        self.assertEqual(classify_gps_quality(25000.0), "COARSE")
        self.assertEqual(classify_gps_quality(None), "UNKNOWN")

    def test_format_altitude(self):
        self.assertEqual(format_altitude(34.0), "34 m")
        self.assertEqual(format_altitude(None), "n/a")

    def test_generate_map_urls(self):
        urls = generate_map_urls(10.123456789, 76.123456789)
        self.assertIn("q=10.123456789,76.123456789", urls["google_maps"])
        self.assertIn("search/10.123456789,76.123456789", urls["google_earth"])
        self.assertIn("mlat=10.123457&mlon=76.123457", urls["openstreetmap"])
        self.assertEqual(urls["geouri"], "geo:10.123457,76.123457?z=16")


if __name__ == "__main__":
    unittest.main()
