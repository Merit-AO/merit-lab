"""
merit-lab sim server — authoritative live what-if on the real engine.

Serves the static observatory (web/ + results/) and a single compute endpoint,
POST /api/sim, that runs a Scenario/params through the REAL engine and returns a
Trace. This is what turns the visualizer's what-if controls into results with no
drift (the browser can't run the Python engine; it asks this). Stdlib only.

Runs on the always-on mini, bound to the tailnet (like the Hermes gateways).
It touches no secrets and no live merit-state — the sim is pure — so it runs as
an ordinary user. Concurrent sims are serialized (a lock) because run_scenario
temporarily overrides engine module globals.

  python3 server/app.py [--host 0.0.0.0] [--port 8646]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "engine"))

from sim import metrics, report             # noqa: E402
from sim.engine import run_scenario         # noqa: E402
from sim.presets import PRESETS             # noqa: E402
from sim.scenario import Overrides, Scenario  # noqa: E402

# Compute + size clamps — bound a single what-if so the endpoint can't be DoS'd.
CLAMP = {"rounds": (1, 30), "candidates_per_round": (1, 20)}
MAX_AGENTS = 60
MAX_EDGES = 600
MAX_TOPICS = 24
MAX_QUORUMS = 60
MAX_BODY = 262144          # 256 KB request-body cap
_OV_FIELDS = set(Overrides().__dict__.keys())
_lock = threading.Lock()   # run_scenario overrides engine globals; serialize (one sim at a time)


def _clampi(v, lo, hi):
    return max(lo, min(hi, int(v)))


def _finite(x):
    f = float(x)
    if not math.isfinite(f):
        raise ValueError("non-finite number rejected")
    return f


def build_scenario(payload: dict) -> Scenario:
    """From {preset?, scenario?, params?} build a bounded Scenario."""
    if payload.get("scenario"):
        sc = Scenario.from_dict(payload["scenario"])
    else:
        name = payload.get("preset", "baseline")
        if name not in PRESETS:
            raise ValueError(f"unknown preset {name}")
        sc = PRESETS[name]()
    for k, v in (payload.get("params") or {}).items():
        if k in _OV_FIELDS:
            setattr(sc.overrides, k, None if v in ("", None) else _finite(v))
        elif k == "slash":
            sc.slash = bool(v)
        elif k in ("top_k",):
            sc.top_k = None if v in ("", None) else int(v)
        elif hasattr(sc, k):
            cur = getattr(sc, k)
            setattr(sc, k, type(cur)(v) if cur is not None else v)
    # reject non-finite overrides from either path (params or a raw scenario payload)
    for k in _OV_FIELDS:
        val = getattr(sc.overrides, k)
        if val is not None:
            setattr(sc.overrides, k, _finite(val))
    # clamp + size bounds
    for f, (lo, hi) in CLAMP.items():
        setattr(sc, f, _clampi(getattr(sc, f), lo, hi))
    if len(sc.agents) > MAX_AGENTS:
        raise ValueError(f"too many agents (>{MAX_AGENTS})")
    if len(sc.edges) > MAX_EDGES:
        raise ValueError(f"too many edges (>{MAX_EDGES})")
    if len(sc.topics) > MAX_TOPICS:
        raise ValueError(f"too many topics (>{MAX_TOPICS})")
    if len(sc.quorums) > MAX_QUORUMS:
        raise ValueError(f"too many quorums (>{MAX_QUORUMS})")
    return sc


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):   # add CORS to static responses too
        if not getattr(self, "_cors_done", False):
            self._cors()
            self._cors_done = True
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()

    def do_GET(self):
        p = self.path.split("?")[0]
        if p == "/api/health":
            return self._json(200, {"ok": True, "presets": sorted(PRESETS)})
        # serve ONLY the observatory + committed results — never .git/, source, or engine/
        if not (p in ("/", "/index.html") or p.startswith("/web/") or p.startswith("/results/")):
            return self._json(404, {"error": "not found"})
        return super().do_GET()

    def _run(self, sc):
        trace = run_scenario(sc)
        trace["metrics"] = metrics.summarize(trace, delegate_floor=sc.delegate_floor_raw)
        return trace

    def do_POST(self):
        path = self.path.split("?")[0]
        if path not in ("/api/sim", "/api/diff"):
            return self._json(404, {"error": "not found"})
        try:
            n = int(self.headers.get("Content-Length", 0))
            if n > MAX_BODY:
                return self._json(413, {"error": f"request too large (>{MAX_BODY} bytes)"})
            payload = json.loads(self.rfile.read(n) or b"{}")
        except Exception as e:
            return self._json(400, {"error": str(e)})
        # one sim at a time; reject (429) rather than queue, so a flood can't pile up threads
        if not _lock.acquire(blocking=False):
            return self._json(429, {"error": "busy — a simulation is already running; retry shortly"})
        try:
            if path == "/api/sim":
                return self._json(200, self._run(build_scenario(payload)))
            # recalibration-preview: same base under current (a) vs proposed (b) params
            base = {k: payload[k] for k in ("preset", "scenario") if k in payload}
            ta = self._run(build_scenario({**base, "params": payload.get("a") or {}}))
            tb = self._run(build_scenario({**base, "params": payload.get("b") or {}}))
            return self._json(200, {"current": ta, "proposed": tb,
                                    "report": report.diff_markdown(ta, tb)})
        except Exception as e:
            return self._json(400, {"error": str(e)})
        finally:
            _lock.release()

    def log_message(self, *a):   # quieter
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")   # safe default; the daemon passes the tailnet IP explicitly
    ap.add_argument("--port", type=int, default=8646)
    args = ap.parse_args()
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"merit-lab sim server on http://{args.host}:{args.port}  (root={ROOT})", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
