#!/bin/bash
# merit-lab setup — clone (or refresh) the engine so the sim imports the real `merit`.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -d "$DIR/engine/.git" ]; then
  echo "refreshing engine…"; git -C "$DIR/engine" pull --ff-only
else
  echo "cloning merit-engine…"; git clone https://github.com/Merit-AO/merit-engine.git "$DIR/engine"
fi
echo
echo "engine ready. Try:"
echo "  python3 -m sim run --preset baseline"
echo "  python3 -m http.server 8099   # then open http://localhost:8099/web/"
