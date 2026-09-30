import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from loclx.diagnostics import DiagnosticRunner  # noqa: E402


class TestDiagnostics(unittest.TestCase):
    def test_run_all_diagnostics(self):
        runner = DiagnosticRunner(port=8765)
        results = runner.run_all()
        self.assertTrue(len(results) >= 8)

        categories = [r[0] for r in results]
        self.assertIn("Environment", categories)
        self.assertIn("Network", categories)
        self.assertIn("Assets", categories)
        self.assertIn("Security", categories)

        for cat, item, status, details in results:
            self.assertIn(status, ("OK", "WARN", "FAIL"))
            self.assertTrue(len(item) > 0)
            self.assertTrue(len(details) > 0)


if __name__ == "__main__":
    unittest.main()
