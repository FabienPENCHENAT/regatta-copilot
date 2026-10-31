#!/usr/bin/env bash
# Starts the site locally: the FastAPI backend (routing engine + API) also serves the frontend.
# Open the printed address on the computer, or on a phone on the same Wi-Fi.
set -euo pipefail

PORT="${PORT:-8000}"
cd "$(dirname "$0")"

if [ ! -x .venv/bin/uvicorn ]; then
  echo "First run: installing the Python environment in .venv (a few minutes)..."
  python3 -m venv .venv
  .venv/bin/pip install --quiet -r backend/requirements.txt -e backend
fi

LAN_IP="$(ipconfig getifaddr en0 2>/dev/null || hostname -I 2>/dev/null | awk '{print $1}' || true)"
echo "Routeur Voile: http://localhost:${PORT}"
if [ -n "${LAN_IP}" ]; then
  echo "On your phone (same Wi-Fi): http://${LAN_IP}:${PORT}"
fi
echo "Stop with Ctrl+C."
exec .venv/bin/uvicorn sailrouter.api.app_factory:create_app --factory --host 0.0.0.0 --port "${PORT}"
