import importlib
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from loclx.cli import parse_args  # noqa: E402


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
        self.assertIsNone(args.subcommand)

    def test_parse_subcommands(self):
        args, rem = parse_args(["start"])
        self.assertEqual(args.subcommand, "start")

        args, rem = parse_args(["session", "list"])
        self.assertEqual(args.subcommand, "session")
        self.assertEqual(args.session_action, "list")

        args, rem = parse_args(["export", "LX-123456", "--format", "csv"])
        self.assertEqual(args.subcommand, "export")
        self.assertEqual(args.id, "LX-123456")
        self.assertEqual(args.format, "csv")

        args, rem = parse_args(["diagnostics"])
        self.assertEqual(args.subcommand, "diagnostics")

        args, rem = parse_args(["config"])
        self.assertEqual(args.subcommand, "config")

        args, rem = parse_args(["qr"])
        self.assertEqual(args.subcommand, "qr")

        args, rem = parse_args(["target"])
        self.assertEqual(args.subcommand, "target")

        args, rem = parse_args(["map"])
        self.assertEqual(args.subcommand, "map")


if __name__ == "__main__":
    unittest.main()
