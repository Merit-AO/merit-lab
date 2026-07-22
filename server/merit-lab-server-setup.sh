#!/bin/bash
#
# merit-lab-server-setup.sh — stand up the merit-lab sim server as an always-on
# LaunchDaemon on the mini, bound to the tailnet (like the Hermes gateways). It
# serves the observatory (web/) + committed results + the POST /api/sim compute
# endpoint that powers live, authoritative what-if. It handles NO secrets and no
# live merit-state (the sim is pure), so it runs as the ordinary `macmini` user.
#
# Usage:  sudo bash "merit-lab-server-setup.sh"
# Idempotent: re-run to refresh the repo + engine and restart the daemon.
set -euo pipefail

RUN_USER="macmini"
REPO="/Users/${RUN_USER}/Projects/merit-lab"
TAILNET_IP="100.72.2.116"
PORT="8646"
LABEL="ai.meritlab.simserver"
PLIST="/Library/LaunchDaemons/${LABEL}.plist"
PY="/usr/bin/python3"

[ "$(id -u)" = "0" ] || { echo "Run with sudo: sudo bash \"merit-lab-server-setup.sh\""; exit 1; }
cd /tmp   # neutral cwd before dropping to the run user

echo "==> 1/4  clone / refresh merit-lab + engine (as ${RUN_USER})"
sudo -u "$RUN_USER" -H bash -c "
  set -e; cd /tmp
  mkdir -p '$(dirname "$REPO")'
  if [ -d '$REPO/.git' ]; then git -C '$REPO' pull --ff-only; else git clone -q https://github.com/Merit-AO/merit-lab.git '$REPO'; fi
  bash '$REPO/setup.sh'
"

echo "==> 2/4  write LaunchDaemon ${PLIST}"
cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>${LABEL}</string>
  <key>UserName</key><string>${RUN_USER}</string>
  <key>WorkingDirectory</key><string>${REPO}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${PY}</string><string>${REPO}/server/app.py</string>
    <string>--host</string><string>${TAILNET_IP}</string>
    <string>--port</string><string>${PORT}</string>
  </array>
  <key>KeepAlive</key><true/>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>/tmp/meritlab-simserver.log</string>
  <key>StandardErrorPath</key><string>/tmp/meritlab-simserver.err</string>
</dict></plist>
PL
chmod 644 "$PLIST"

echo "==> 3/4  (re)load the daemon"
launchctl bootout system "$PLIST" 2>/dev/null || true
launchctl bootstrap system "$PLIST"
launchctl kickstart -k "system/${LABEL}" 2>/dev/null || true

echo "==> 4/4  verify"
sleep 2
code="$(/usr/bin/curl -sS -m6 -o /dev/null -w '%{http_code}' "http://${TAILNET_IP}:${PORT}/api/health" 2>/dev/null || echo fail)"
echo "  http://${TAILNET_IP}:${PORT}/api/health -> ${code}"
echo
echo "DONE. Observatory (live what-if): http://${TAILNET_IP}:${PORT}/web/"
echo "Public read-only mirror stays at https://merit-ao.github.io/merit-lab/"
