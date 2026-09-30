import importlib
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from loclx.cli import parse_args  # noqa: E402
from loclx.dashboard import generate_target_report  # noqa: E402
from loclx.sessions import SessionManager  # noqa: E402
from loclx.utils import Ansi  # noqa: E402


class TestCLI(unittest.TestCase):
    def test_no_webbrowser_import_in_cli(self):
        """Regression test verifying cli.py does not import webbrowser."""
        cli_mod = importlib.import_module("loclx.cli")
        self.assertFalse(hasattr(cli_mod, "webbrowser"), "cli.py must not import webbrowser")

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
        from loclx.cli import main
        # Ensure env variables are cleared for test
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


if __name__ == "__main__":
    unittest.main()
