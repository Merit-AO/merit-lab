"""
merit-lab simulation CLI.

  python -m sim list
  python -m sim run --preset baseline [--out results/baseline.json]
  python -m sim run --preset sybil-swarm --param faucet_stake=1 --param W_TRUST=0.6
  python -m sim run --scenario scenarios/my.json --out results/my.json

Writes <out>.json (the Trace the visualizer renders) + <out>.md (the report).
--param sets Scenario fields or aggregation Overrides in-process (the knobs the
engine CLI can't reach). Everything runs on the real engine; no merit-state is
touched.
"""
from __future__ import annotations

import argparse
import json
import os

from . import metrics, report
from .engine import run_scenario
from .presets import PRESETS
from .scenario import Overrides, Scenario

_BOOL = {"true": True, "false": False, "1": True, "0": False}


def _cast(v: str):
    if v.lower() in _BOOL:
        return _BOOL[v.lower()]
    for f in (int, float):
        try:
            return f(v)
        except ValueError:
            pass
    return v


def _apply_params(sc: Scenario, params: list[str]):
    ov_fields = set(Overrides().__dict__.keys())
    for kv in params or []:
        if "=" not in kv:
            continue
        k, v = kv.split("=", 1)
        val = _cast(v)
        if k in ov_fields:
            setattr(sc.overrides, k, val)
        elif hasattr(sc, k):
            setattr(sc, k, val)
        else:
            raise SystemExit(f"unknown --param {k} (not a Scenario field or Override)")


def main():
    ap = argparse.ArgumentParser(prog="sim", description="Merit AO simulation sandbox")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="list presets")
    r = sub.add_parser("run", help="run a scenario")
    g = r.add_mutually_exclusive_group(required=True)
    g.add_argument("--preset", choices=sorted(PRESETS))
    g.add_argument("--scenario", help="path to a Scenario JSON")
    r.add_argument("--param", action="append", default=[], help="key=value (Scenario field or Override)")
    r.add_argument("--out", default=None, help="output path stem (writes .json + .md)")

    args = ap.parse_args()
    if args.cmd == "list":
        for name, fn in sorted(PRESETS.items()):
            print(f"  {name:16} {fn().description}")
        return

    sc = (Scenario.from_dict(json.load(open(args.scenario))) if args.scenario
          else PRESETS[args.preset]())
    _apply_params(sc, args.param)

    trace = run_scenario(sc)
    trace["metrics"] = metrics.summarize(trace, delegate_floor=sc.delegate_floor_raw)

    out = args.out or os.path.join("results", f"{sc.name}.json")
    if not out.endswith(".json"):
        out += ".json"
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w") as f:
        json.dump(trace, f, indent=2)
    md = out[:-5] + ".md"
    with open(md, "w") as f:
        f.write(report.to_markdown(trace))
    print(f"wrote {out}  +  {md}")
    print(f"  rounds={len(trace['rounds'])} agents={len(trace['agents'])} "
          f"peak_adv_share={trace['metrics'].get('peak_adversarial_share')}")


if __name__ == "__main__":
    main()
