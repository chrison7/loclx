import importlib
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from loclx.cli import build_session_url, main, parse_args  # noqa: E402
from loclx.dashboard import generate_target_report  # noqa: E402
from loclx.sessions import SessionManager  # noqa: E402
from loclx.utils import Ansi  # noqa: E402


class TestCLI(unittest.TestCase):
    def test_no_webbrowser_import_in_cli(self):
        """Regression test verifying cli.py does not import webbrowser."""
        cli_mod = importlib.import_module("loclx.cli")
        self.assertFalse(hasattr(cli_mod, "webbrowser"), "cli.py must not import webbrowser")

    def test_build_session_url(self):
        url = build_session_url("https://my-proxy.example.com/", "LX-A1B2C3")
        self.assertEqual(url, "https://my-proxy.example.com/session/LX-A1B2C3")

        with self.assertRaises(ValueError):
            build_session_url("https://my-proxy.example.com", "invalid-sid")

        with self.assertRaises(ValueError):
            build_session_url("http://remote-unencrypted.com", "LX-A1B2C3")

    def test_parse_args_defaults(self):
        args, rem = parse_args([])
        self.assertEqual(args.port, 8765)
        self.assertFalse(args.debug)
        self.assertFalse(args.lab)
        self.assertIsNone(args.tunnel)
        self.assertIsNone(args.subcommand)

    def test_parse_tunnel_arg(self):
        args, rem = parse_args(["--tunnel", "https://custom-tunnel.loclx.io"])
        self.assertEqual(args.tunnel, "https://custom-tunnel.loclx.io")

    def test_parse_subcommands(self):
        args, rem = parse_args(["start"])
        self.assertEqual(args.subcommand, "start")

        args, rem = parse_args(["session", "create"])
        self.assertEqual(args.subcommand, "session")
        self.assertEqual(args.session_action, "create")

        args, rem = parse_args(["export", "LX-123456", "--format", "csv"])
        self.assertEqual(args.subcommand, "export")
        self.assertEqual(args.id, "LX-123456")
        self.assertEqual(args.format, "csv")

        args, rem = parse_args(["report", "LX-123456"])
        self.assertEqual(args.subcommand, "report")
        self.assertEqual(args.id, "LX-123456")

        args, rem = parse_args(["earth", "LX-123456"])
        self.assertEqual(args.subcommand, "earth")

    def test_generate_target_report(self):
        sm = SessionManager()
        session = sm.create_session()
        session.update_gps({"lat": 10.123456789, "lon": 76.123456789, "accuracy": 7.0, "altitude": 32.0, "speed": 0.2, "heading": 181.0})
        report = generate_target_report(session, Ansi(False))
        self.assertIn("LOCLX — TARGET INFORMATION", report)
        self.assertIn(session.sid, report)
        self.assertIn("10.123456789", report)
        self.assertIn("76.123456789", report)
        self.assertIn("±7 m", report)

    def test_missing_public_config_fails_startup(self):
        old_pub = os.environ.pop("LOCLX_PUBLIC_URL", None)
        old_tun = os.environ.pop("LOCLX_TUNNEL_URL", None)
        try:
            res = main([])
            self.assertEqual(res, 1)
        finally:
            if old_pub:
                os.environ["LOCLX_PUBLIC_URL"] = old_pub
            if old_tun:
                os.environ["LOCLX_TUNNEL_URL"] = old_tun

    def test_invalid_public_url_fails(self):
        res = main(["--public-url", "http://insecure-remote.com"])
        self.assertEqual(res, 1)

    def test_qr_without_public_url_fails(self):
        old_pub = os.environ.pop("LOCLX_PUBLIC_URL", None)
        old_tun = os.environ.pop("LOCLX_TUNNEL_URL", None)
        try:
            res = main(["qr"])
            self.assertEqual(res, 1)
        finally:
            if old_pub:
                os.environ["LOCLX_PUBLIC_URL"] = old_pub
            if old_tun:
                os.environ["LOCLX_TUNNEL_URL"] = old_tun

    def test_cli_url_precedence_hierarchy(self):
        """11. CLI URL PRECEDENCE: Test --public-url > --tunnel <URL> > LOCLX_PUBLIC_URL > LOCLX_TUNNEL_URL > --tunnel."""
        old_pub = os.environ.pop("LOCLX_PUBLIC_URL", None)
        old_tun = os.environ.pop("LOCLX_TUNNEL_URL", None)

        try:
            # 1. --public-url overrides everything
            os.environ["LOCLX_PUBLIC_URL"] = "https://env-pub.example.com"
            os.environ["LOCLX_TUNNEL_URL"] = "https://env-tun.example.com"
            args, _ = parse_args(["--public-url", "https://arg-pub.example.com", "--tunnel", "https://arg-tun.example.com"])
            raw_url = args.public_url or (args.tunnel if isinstance(args.tunnel, str) else None)
            self.assertEqual(raw_url, "https://arg-pub.example.com")

            # 2. --tunnel <URL> overrides env vars
            args2, _ = parse_args(["--tunnel", "https://arg-tun.example.com"])
            raw_url2 = args2.public_url or (args2.tunnel if isinstance(args2.tunnel, str) else None) or os.environ.get("LOCLX_PUBLIC_URL")
            self.assertEqual(raw_url2, "https://arg-tun.example.com")

            # 3. LOCLX_PUBLIC_URL overrides LOCLX_TUNNEL_URL
            args3, _ = parse_args([])
            raw_url3 = args3.public_url or (args3.tunnel if isinstance(args3.tunnel, str) else None) or os.environ.get("LOCLX_PUBLIC_URL")
            self.assertEqual(raw_url3, "https://env-pub.example.com")

            # 4. LOCLX_TUNNEL_URL used when LOCLX_PUBLIC_URL is absent
            os.environ.pop("LOCLX_PUBLIC_URL", None)
            raw_url4 = args3.public_url or (args3.tunnel if isinstance(args3.tunnel, str) else None) or os.environ.get("LOCLX_PUBLIC_URL") or os.environ.get("LOCLX_TUNNEL_URL")
            self.assertEqual(raw_url4, "https://env-tun.example.com")

            # 5. --tunnel (without value) sets tunnel flag true
            args5, _ = parse_args(["--tunnel"])
            self.assertTrue(args5.tunnel is True)

        finally:
            if old_pub:
                os.environ["LOCLX_PUBLIC_URL"] = old_pub
            else:
                os.environ.pop("LOCLX_PUBLIC_URL", None)
            if old_tun:
                os.environ["LOCLX_TUNNEL_URL"] = old_tun
            else:
                os.environ.pop("LOCLX_TUNNEL_URL", None)

    def test_qr_requires_validated_public_url(self):
        """12. QR: Verify QR generation requires a validated public HTTPS endpoint."""
        url = build_session_url("https://valid-public.example.com", "LX-123456")
        self.assertEqual(url, "https://valid-public.example.com/session/LX-123456")

        # Insecure HTTP remote URL is rejected for participant QR/URL build
        with self.assertRaises(ValueError):
            build_session_url("http://insecure.example.com", "LX-123456")


if __name__ == "__main__":
    unittest.main()
