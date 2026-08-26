#!/usr/bin/env bash
# Idempotent dependency setup for RSS-ArchiveORG.
# Creates a project virtualenv (.venv) and installs Python dependencies.
set -euo pipefail

cd "$(dirname "$0")/.."

# The default image may not ship Python venv support; install it if missing.
if ! python3 -c "import ensurepip" >/dev/null 2>&1; then
  echo "Installing python3-venv..."
  sudo apt-get update -qq
  sudo apt-get install -y -qq python3-venv
fi

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -r requirements-dev.txt

echo "Environment ready. Activate with: source .venv/bin/activate"
