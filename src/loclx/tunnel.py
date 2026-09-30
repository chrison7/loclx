"""Cloudflare Quick Tunnel integration for LOCLX v2.4.6."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from typing import Optional, Tuple

from loclx.security import validate_public_url

CLOUDFLARED_DOWNLOAD_URL = "https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"


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


def start_cloudflare_tunnel(port: int, timeout: float = 20.0) -> Tuple[subprocess.Popen, str]:
    """Start cloudflared quick tunnel targeting local HTTP listener and return (proc, public_url)."""
    if not is_cloudflared_installed():
        raise RuntimeError(get_cloudflared_install_instructions())

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

    url_regex = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
    start_time = time.time()
    found_url: Optional[str] = None

    while time.time() - start_time < timeout:
        if proc.poll() is not None:
            break

        line = proc.stdout.readline() if proc.stdout else ""
        if not line:
            time.sleep(0.1)
            continue

        match = url_regex.search(line)
        if match:
            found_url = match.group(0)
            break

    if not found_url:
        proc.kill()
        proc.wait()
        raise RuntimeError(
            "Could not parse Cloudflare quick tunnel URL within timeout.\n"
            "Ensure outbound network connection is available."
        )

    validated = validate_public_url(found_url)
    return proc, validated
