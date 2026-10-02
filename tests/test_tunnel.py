import os
import sys
import time
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from loclx.cli import parse_args
from loclx.tunnel import (
    get_cloudflared_install_instructions,
    is_cloudflared_installed,
    start_cloudflare_tunnel,
    stop_cloudflare_tunnel,
    verify_local_server_ready,
)


class DummyStream:
    def __init__(self, lines: list[str], delay: float = 0.0):
        self.lines = lines
        self.delay = delay
        self.index = 0

    def readline(self) -> str:
        if self.index < len(self.lines):
            line = self.lines[self.index]
            self.index += 1
            if self.delay > 0:
                time.sleep(self.delay)
            return line
        return ""


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

    def test_stop_cloudflare_tunnel_idempotent(self):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        stop_cloudflare_tunnel(mock_proc)
        mock_proc.terminate.assert_called_once()

        # Calling again on None or finished process must not crash
        stop_cloudflare_tunnel(None)
        mock_proc.poll.return_value = 0
        stop_cloudflare_tunnel(mock_proc)

    @patch("loclx.tunnel.verify_local_server_ready", return_value=True)
    @patch("loclx.tunnel.is_cloudflared_installed", return_value=True)
    @patch("subprocess.Popen")
    def test_url_appears_quickly(self, mock_popen, mock_installed, mock_ready):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.stdout = DummyStream(["2026-10-01 INF https://quick-test.trycloudflare.com\n"])
        mock_popen.return_value = mock_proc

        proc, url = start_cloudflare_tunnel(8765, timeout=2.0)
        self.assertEqual(url, "https://quick-test.trycloudflare.com")
        self.assertEqual(proc, mock_proc)
        mock_popen.assert_called_once()
        cmd_arg = mock_popen.call_args[0][0]
        self.assertIn("http://127.0.0.1:8765", cmd_arg)

    @patch("loclx.tunnel.verify_local_server_ready", return_value=True)
    @patch("loclx.tunnel.is_cloudflared_installed", return_value=True)
    @patch("subprocess.Popen")
    def test_url_appears_after_several_lines(self, mock_popen, mock_installed, mock_ready):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.stdout = DummyStream([
            "2026-10-01 INF Starting tunnel...\n",
            "2026-10-01 INF Connecting to edge...\n",
            "2026-10-01 INF Tunnel registered: https://delayed-url.trycloudflare.com\n",
        ])
        mock_popen.return_value = mock_proc

        proc, url = start_cloudflare_tunnel(8765, timeout=2.0)
        self.assertEqual(url, "https://delayed-url.trycloudflare.com")

    @patch("loclx.tunnel.verify_local_server_ready", return_value=True)
    @patch("loclx.tunnel.is_cloudflared_installed", return_value=True)
    @patch("subprocess.Popen")
    def test_cloudflared_produces_no_url(self, mock_popen, mock_installed, mock_ready):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.stdout = DummyStream(["2026-10-01 INF No URL here...\n"])
        mock_popen.return_value = mock_proc

        with self.assertRaises(RuntimeError) as cm:
            start_cloudflare_tunnel(8765, timeout=0.3)
        self.assertIn("Cloudflare tunnel startup timed out", str(cm.exception))
        mock_proc.terminate.assert_called_once()

    @patch("loclx.tunnel.verify_local_server_ready", return_value=True)
    @patch("loclx.tunnel.is_cloudflared_installed", return_value=True)
    @patch("subprocess.Popen")
    def test_cloudflared_exits_before_url(self, mock_popen, mock_installed, mock_ready):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = 1
        mock_proc.returncode = 1
        mock_proc.stdout = DummyStream(["Error: failed to connect\n"])
        mock_popen.return_value = mock_proc

        with self.assertRaises(RuntimeError) as cm:
            start_cloudflare_tunnel(8765, timeout=2.0)
        self.assertIn("cloudflared exited before producing a public URL", str(cm.exception))

    @patch("loclx.tunnel.verify_local_server_ready", return_value=True)
    @patch("loclx.tunnel.is_cloudflared_installed", return_value=True)
    @patch("subprocess.Popen")
    def test_timeout_enforced_on_silent_stream(self, mock_popen, mock_installed, mock_ready):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        # Blocking stream simulation with delay greater than timeout
        mock_proc.stdout = DummyStream(["slow line\n"], delay=1.0)
        mock_popen.return_value = mock_proc

        start = time.time()
        with self.assertRaises(RuntimeError):
            start_cloudflare_tunnel(8765, timeout=0.2)
        elapsed = time.time() - start
        self.assertLess(elapsed, 0.9, "Timeout must be enforced even if stream blocks")

    @patch("loclx.tunnel.verify_local_server_ready", return_value=False)
    @patch("loclx.tunnel.is_cloudflared_installed", return_value=True)
    def test_server_not_ready_fails(self, mock_installed, mock_ready):
        with self.assertRaises(RuntimeError) as cm:
            start_cloudflare_tunnel(8765, timeout=2.0)
        self.assertIn("is not ready", str(cm.exception))

    @patch("loclx.tunnel.is_cloudflared_installed", return_value=False)
    def test_cloudflared_not_installed_fails(self, mock_installed):
        with self.assertRaises(RuntimeError) as cm:
            start_cloudflare_tunnel(8765, timeout=2.0)
        self.assertIn("cloudflared is not installed", str(cm.exception))

    @patch("loclx.tunnel.verify_local_server_ready", return_value=True)
    @patch("loclx.tunnel.is_cloudflared_installed", return_value=True)
    @patch("subprocess.Popen")
    def test_malformed_tunnel_url_output(self, mock_popen, mock_installed, mock_ready):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.stdout = DummyStream(["2026-10-01 INF Tunnel registered: http://invalid-tunnel.example.com\n"])
        mock_popen.return_value = mock_proc

        with self.assertRaises(RuntimeError) as cm:
            start_cloudflare_tunnel(8765, timeout=0.3)
        self.assertIn("Cloudflare tunnel startup timed out", str(cm.exception))
        mock_proc.terminate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
