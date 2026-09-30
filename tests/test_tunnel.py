import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from loclx.cli import parse_args
from loclx.tunnel import (
    get_cloudflared_install_instructions,
    is_cloudflared_installed,
)


class TestTunnel(unittest.TestCase):
    def test_parse_tunnel_flag_without_value(self):
        args, rem = parse_args(["--tunnel"])
        self.assertTrue(args.tunnel)

    def test_parse_tunnel_flag_with_value(self):
        args, rem = parse_args(["--tunnel", "https://custom.trycloudflare.com"])
        self.assertEqual(args.tunnel, "https://custom.trycloudflare.com")

    def test_install_instructions(self):
        instructions = get_cloudflared_install_instructions()
        self.assertIn("cloudflared is not installed", instructions)
        self.assertIn("https://developers.cloudflare.com", instructions)

    def test_is_cloudflared_installed_returns_bool(self):
        result = is_cloudflared_installed()
        self.assertIsInstance(result, bool)


if __name__ == "__main__":
    unittest.main()
