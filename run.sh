#!/usr/bin/env bash
# Starts the site locally. Open the printed address on the computer, or on a phone on the same Wi-Fi.
# For now it serves the frontend with its example data; it will start the FastAPI backend once the
# routing engine is wired in (step 5).
set -euo pipefail

PORT="${PORT:-8000}"
cd "$(dirname "$0")/frontend"

LAN_IP="$(ipconfig getifaddr en0 2>/dev/null || hostname -I 2>/dev/null | awk '{print $1}' || true)"
echo "Routeur Voile: http://localhost:${PORT}"
if [ -n "${LAN_IP}" ]; then
  echo "On your phone (same Wi-Fi): http://${LAN_IP}:${PORT}"
fi
echo "Stop with Ctrl+C."
exec python3 -m http.server "${PORT}" --bind 0.0.0.0
