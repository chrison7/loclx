import os
import re
import sys
import unittest
import subprocess
from importlib.machinery import SourceFileLoader
import importlib.util

LOCLX_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "loclx"))
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

FORBIDDEN_TERMS = [
    "0." + "0.0.0",
    "-" + "-host",
    "ng" + "rok",
    "cloud" + "flared",
    "local" + "tunnel",
    "ser" + "veo",
    "ssh " + "-R",
    "session" + "_id",
    "sqlite" + "3",
]


def load_loclx_module():
    loader = SourceFileLoader("loclx", LOCLX_PATH)
    spec = importlib.util.spec_from_loader("loclx", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def get_tracked_files():
    try:
        res = subprocess.run(
            ["git", "ls-files"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        files = [f.strip() for f in res.stdout.splitlines() if f.strip()]
        if files:
            return [os.path.join(REPO_ROOT, f) for f in files]
    except Exception:
        pass

    tracked = []
    for root, dirs, files in os.walk(REPO_ROOT):
        if ".git" in dirs:
            dirs.remove(".git")
        if "__pycache__" in dirs:
            dirs.remove("__pycache__")
        for file in files:
            if file.endswith((".pyc", ".pyo")):
                continue
            tracked.append(os.path.join(root, file))
    return tracked


class TestGuard(unittest.TestCase):
    def setUp(self):
        self.loclx = load_loclx_module()

    def test_version_constant(self):
        self.assertTrue(hasattr(self.loclx, "VERSION"))
        self.assertEqual(self.loclx.VERSION, "2.1.1")

    def test_bind_addr_fixed(self):
        self.assertTrue(hasattr(self.loclx, "BIND_ADDR"))
        self.assertEqual(self.loclx.BIND_ADDR, "127.0.0.1")
        with open(LOCLX_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn('BIND_ADDR = "127.0.0.1"', content)

    def test_version_flag(self):
        res = subprocess.run(
            [sys.executable, LOCLX_PATH, "--version"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn(f"loclx {self.loclx.VERSION}", res.stdout)

    def test_help_epilog(self):
        res = subprocess.run(
            [sys.executable, LOCLX_PATH, "--help"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("The bind address is fixed at 127.0.0.1 and cannot be changed.", res.stdout)

    def test_no_remote_bind_flags(self):
        args = self.loclx.parse_args([])
        self.assertFalse(hasattr(args, "host"))
        self.assertFalse(hasattr(args, "bind"))
        self.assertFalse(hasattr(args, "listen"))
        self.assertFalse(hasattr(args, "remote"))

    def test_accuracy_svg_viz(self):
        self.assertTrue(hasattr(self.loclx, "HTML_PAGE"))
        html = self.loclx.HTML_PAGE
        self.assertIn("updateAccuracySvg", html)
        self.assertIn("http://www.w3.org/2000/svg", html)
        self.assertIn("gps-acc-viz", html)

    def test_world_view_map(self):
        self.assertTrue(hasattr(self.loclx, "HTML_PAGE"))
        html = self.loclx.HTML_PAGE
        self.assertIn("worldMarker", html)
        self.assertIn("updateWorldView", html)
        self.assertNotIn("<iframe", html)

        forbidden_map_assets = [
            "tile.openstreetmap",
            "leaflet",
            "mapbox",
            "googleapis.com/maps",
            '<img src="http',
            "cdn.",
            "<embed",
        ]
        for asset in forbidden_map_assets:
            self.assertNotIn(asset, html)

        hrefs = re.findall(r'href=["\'](.*?)["\']', html)
        srcs = re.findall(r'src=["\'](.*?)["\']', html)

        hosts = ["openstreetmap.org", "google.com/maps"]
        for host in hosts:
            self.assertTrue(any(host in href for href in hrefs), f"{host} should appear in an href attribute")
            self.assertFalse(any(host in src for src in srcs), f"{host} must not appear in a src attribute")

    def test_no_forbidden_strings_in_tracked_files(self):
        tracked_files = get_tracked_files()
        violations = []
        for file_path in tracked_files:
            if not os.path.isfile(file_path):
                continue
            rel_path = os.path.relpath(file_path, REPO_ROOT)
            if rel_path in ("CONTRIBUTING.md", "SECURITY.md"):
                continue
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue
            for term in FORBIDDEN_TERMS:
                if term in content:
                    violations.append(f"Forbidden term '{term}' found in {rel_path}")
        self.assertEqual(violations, [], f"Forbidden terms detected: {violations}")


if __name__ == "__main__":
    unittest.main()
