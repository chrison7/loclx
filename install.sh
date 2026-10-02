#!/usr/bin/env bash
set -e

echo "=== Installing LOCLX ==="

# 1. Check python3
if ! command -v python3 >/dev/null 2>&1; then
    echo "[-] Error: python3 is not installed." >&2
    echo "[!] Please install Python 3 (e.g. sudo apt install python3) and retry." >&2
    exit 1
fi

# 2. Check python venv support
if ! python3 -m venv --help >/dev/null 2>&1; then
    echo "[-] Error: Python venv module is missing." >&2
    echo "[!] On Debian/Parrot/Ubuntu, install it using:" >&2
    echo "    sudo apt update && sudo apt install python3-venv" >&2
    exit 1
fi

# 3. Create .venv if not exists
if [ ! -d ".venv" ]; then
    echo "[*] Creating virtual environment in .venv..."
    python3 -m venv .venv || {
        echo "[-] Failed to create virtual environment." >&2
        echo "[!] Make sure python3-venv is installed: sudo apt install python3-venv" >&2
        exit 1
    }
fi

# 4 & 5. Upgrade pip inside venv
echo "[*] Upgrading pip inside virtual environment..."
.venv/bin/python -m pip install --upgrade pip

# 6. Install LOCLX in editable mode
echo "[*] Installing LOCLX in editable mode..."
.venv/bin/python -m pip install -e .

# 7. Verify installation
echo "[*] Verifying installation..."
if ! .venv/bin/loclx --version >/dev/null 2>&1; then
    echo "[-] Verification failed: loclx command did not execute properly." >&2
    exit 1
fi

echo ""
echo "========================================================"
echo "[+] LOCLX Installation Completed Successfully!"
echo "========================================================"
echo "To activate the environment:"
echo "    source .venv/bin/activate"
echo ""
echo "To start LOCLX with Cloudflare Quick Tunnel:"
echo "    loclx start --tunnel"
echo "========================================================"
