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
        self.assertFalse(args.tunnel)
        self.assertIsNone(args.subcommand)

    def test_parse_tunnel_flag(self):
        args, _ = parse_args(["--tunnel"])
        self.assertTrue(args.tunnel)

    def test_start_tunnel_order_flexibility(self):
        """Test both loclx start --tunnel and loclx --tunnel start."""
        args1, _ = parse_args(["start", "--tunnel"])
        self.assertEqual(args1.subcommand, "start")
        self.assertTrue(args1.tunnel)

        args2, _ = parse_args(["--tunnel", "start"])
        self.assertEqual(args2.subcommand, "start")
        self.assertTrue(args2.tunnel)

    def test_tunnel_url_parsing(self):
        args, _ = parse_args(["--tunnel-url", "https://custom-tunnel.loclx.io"])
        self.assertEqual(args.tunnel_url, "https://custom-tunnel.loclx.io")

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

        args, rem = parse_args(["ip", "LX-123456"])
        self.assertEqual(args.subcommand, "ip")

        args, rem = parse_args(["browser", "LX-123456"])
        self.assertEqual(args.subcommand, "browser")

        args, rem = parse_args(["history", "LX-123456"])
        self.assertEqual(args.subcommand, "history")

        args, rem = parse_args(["dashboard", "LX-123456"])
        self.assertEqual(args.subcommand, "dashboard")

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

    def test_invalid_tunnel_url_fails(self):
        res = main(["--tunnel-url", "http://insecure-tunnel.com"])
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
        """CLI URL PRECEDENCE: Test --public-url > --tunnel-url > LOCLX_PUBLIC_URL > LOCLX_TUNNEL_URL > --tunnel."""
        old_pub = os.environ.pop("LOCLX_PUBLIC_URL", None)
        old_tun = os.environ.pop("LOCLX_TUNNEL_URL", None)

        try:
            # 1. --public-url overrides everything
            os.environ["LOCLX_PUBLIC_URL"] = "https://env-pub.example.com"
            os.environ["LOCLX_TUNNEL_URL"] = "https://env-tun.example.com"
            args, _ = parse_args(["--public-url", "https://arg-pub.example.com", "--tunnel-url", "https://arg-tun.example.com"])
            raw_url = args.public_url or args.tunnel_url
            self.assertEqual(raw_url, "https://arg-pub.example.com")

            # 2. --tunnel-url overrides env vars
            args2, _ = parse_args(["--tunnel-url", "https://arg-tun.example.com"])
            raw_url2 = args2.public_url or args2.tunnel_url or os.environ.get("LOCLX_PUBLIC_URL")
            self.assertEqual(raw_url2, "https://arg-tun.example.com")

            # 3. LOCLX_PUBLIC_URL overrides LOCLX_TUNNEL_URL
            args3, _ = parse_args([])
            raw_url3 = args3.public_url or args3.tunnel_url or os.environ.get("LOCLX_PUBLIC_URL")
            self.assertEqual(raw_url3, "https://env-pub.example.com")

            # 4. LOCLX_TUNNEL_URL used when LOCLX_PUBLIC_URL is absent
            os.environ.pop("LOCLX_PUBLIC_URL", None)
            raw_url4 = args3.public_url or args3.tunnel_url or os.environ.get("LOCLX_PUBLIC_URL") or os.environ.get("LOCLX_TUNNEL_URL")
            self.assertEqual(raw_url4, "https://env-tun.example.com")

            # 5. --tunnel sets boolean flag True
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
        """QR: Verify QR generation requires a validated public HTTPS endpoint."""
        url = build_session_url("https://valid-public.example.com", "LX-123456")
        self.assertEqual(url, "https://valid-public.example.com/session/LX-123456")

        with self.assertRaises(ValueError):
            build_session_url("http://insecure.example.com", "LX-123456")

    def test_pep668_safe_installation_docs(self):
        """Verify README and install.sh enforce PEP 668 safe installation procedures."""
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        readme_path = os.path.join(repo_root, "README.md")
        install_path = os.path.join(repo_root, "install.sh")

        with open(readme_path, "r", encoding="utf-8") as f:
            readme_text = f.read()
        with open(install_path, "r", encoding="utf-8") as f:
            install_text = f.read()

        self.assertIn("python3 -m venv .venv", readme_text)
        self.assertIn("source .venv/bin/activate", readme_text)
        self.assertNotIn("--break-system-packages", readme_text)

        self.assertIn("python3 -m venv", install_text)
        self.assertIn(".venv/bin/python -m pip install -e .", install_text)

    def test_launcher_file_permission(self):
        """Verify ./loclx file launcher is present and imports correctly."""
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        launcher_path = os.path.join(repo_root, "loclx")
        self.assertTrue(os.path.isfile(launcher_path))


if __name__ == "__main__":
    unittest.main()
