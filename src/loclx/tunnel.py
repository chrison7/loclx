"""Cloudflare Quick Tunnel integration for LOCLX v2.4.7."""

from __future__ import annotations

import os
import queue
import re
import shutil
import subprocess
import threading
import time
import urllib.request
from typing import Optional, Tuple

from loclx.security import validate_public_url

CLOUDFLARED_DOWNLOAD_URL = "https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
URL_PATTERN = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")


def is_cloudflared_installed() -> bool:
    """Check if cloudflared binary is available in PATH."""
    return shutil.which("cloudflared") is not None


def get_cloudflared_install_instructions() -> str:
    """Return platform-specific installation instructions for cloudflared."""
    return (
        "[-] cloudflared is not installed or not in PATH.\n"
        "[*] Installation options:\n"
        "    Linux:   sudo apt install cloudflared\n"
        "    macOS:   brew install cloudflared\n"
        "    Windows: winget install Cloudflare.cloudflared\n"
        f"    Manual:  {CLOUDFLARED_DOWNLOAD_URL}"
    )


def stop_cloudflare_tunnel(proc: Optional[subprocess.Popen], timeout: float = 2.0) -> None:
    """Safely terminate and clean up a cloudflared process (idempotent)."""
    if proc is None:
        return
    try:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=timeout)
            except Exception:
                proc.kill()
                proc.wait(timeout=1.0)
    except Exception:
        pass


def verify_local_server_ready(port: int, timeout: float = 3.0) -> bool:
    """Perform a lightweight local HTTP check to verify server readiness at 127.0.0.1:<port>."""
    url = f"http://127.0.0.1:{port}/favicon.ico"
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=0.5) as resp:
                if resp.status in (200, 204):
                    return True
        except Exception:
            time.sleep(0.05)
    return False


def start_cloudflare_tunnel(port: int, timeout: float = 20.0) -> Tuple[subprocess.Popen, str]:
    """Start cloudflared quick tunnel targeting local HTTP listener and return (proc, public_url)."""
    if not is_cloudflared_installed():
        raise RuntimeError(get_cloudflared_install_instructions())

    if not verify_local_server_ready(port):
        raise RuntimeError(f"[-] Local LOCLX server on 127.0.0.1:{port} is not ready.")

    cmd = ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}"]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to execute cloudflared: {exc}")

    output_queue: queue.Queue[Optional[str]] = queue.Queue()

    def _enqueue_output(stream, q):
        try:
            for line in iter(stream.readline, ""):
                if line:
                    q.put(line)
        except Exception:
            pass
        finally:
            q.put(None)

    reader_thread = threading.Thread(
        target=_enqueue_output,
        args=(proc.stdout, output_queue),
        daemon=True,
    )
    reader_thread.start()

    start_time = time.time()
    found_url: Optional[str] = None
    captured_lines: list[str] = []

    while time.time() - start_time < timeout:
        if proc.poll() is not None and output_queue.empty():
            break

        try:
            line = output_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        if line is None:
            break

        captured_lines.append(line.rstrip())
        match = URL_PATTERN.search(line)
        if match:
            found_url = match.group(0)
            break

    if not found_url:
        exited = proc.poll() is not None
        exit_code = proc.returncode if exited else None
        stop_cloudflare_tunnel(proc)

        diag = ""
        if captured_lines:
            diag_str = "\n".join(f"    {l}" for l in captured_lines[-5:])
            diag = f"\n[-] Recent output:\n{diag_str}"

        if exited:
            msg = (
                f"[-] cloudflared exited before producing a public URL (exit code {exit_code}).{diag}\n"
                f"[-] Check command manually: cloudflared tunnel --url http://127.0.0.1:{port}"
            )
        else:
            msg = (
                f"[-] Cloudflare tunnel startup timed out after {timeout:.0f}s.{diag}\n"
                f"[-] Check command manually: cloudflared tunnel --url http://127.0.0.1:{port}"
            )

        raise RuntimeError(msg)

    validated = validate_public_url(found_url)
    return proc, validated
