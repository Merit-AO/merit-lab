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

    d = sub.add_parser("diff", help="recalibration-preview: same scenario under current vs proposed params")
    dg = d.add_mutually_exclusive_group(required=True)
    dg.add_argument("--preset", choices=sorted(PRESETS))
    dg.add_argument("--scenario")
    d.add_argument("--a", action="append", default=[], help="current params (key=value)")
    d.add_argument("--b", action="append", default=[], help="proposed params (key=value)")
    d.add_argument("--out", default=None, help="output stem for the diff report")

    args = ap.parse_args()
    if args.cmd == "list":
        for name, fn in sorted(PRESETS.items()):
            print(f"  {name:16} {fn().description}")
        return

    def _base():
        return (Scenario.from_dict(json.load(open(args.scenario))) if args.scenario
                else PRESETS[args.preset]())

    def _run(sc):
        t = run_scenario(sc)
        t["metrics"] = metrics.summarize(t, delegate_floor=sc.delegate_floor_raw)
        return t

    if args.cmd == "diff":
        a = _base(); _apply_params(a, args.a); ta = _run(a)
        b = _base(); _apply_params(b, args.b); tb = _run(b)
        stem = args.out or os.path.join("results", f"recalib-{a.name}")
        os.makedirs(os.path.dirname(stem) or ".", exist_ok=True)
        json.dump({"current": ta, "proposed": tb}, open(stem + ".json", "w"), indent=2)
        open(stem + ".md", "w").write(report.diff_markdown(ta, tb))
        dcap = tb["metrics"]["peak_adversarial_share"] - ta["metrics"]["peak_adversarial_share"]
        print(f"wrote {stem}.json + {stem}.md")
        print(f"  peak adversary share: {ta['metrics']['peak_adversarial_share']} -> "
              f"{tb['metrics']['peak_adversarial_share']}  (Δ {dcap:+.4f})")
        return

    sc = _base(); _apply_params(sc, args.param)
    trace = _run(sc)
    out = args.out or os.path.join("results", f"{sc.name}.json")
    if not out.endswith(".json"):
        out += ".json"
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    json.dump(trace, open(out, "w"), indent=2)
    open(out[:-5] + ".md", "w").write(report.to_markdown(trace))
    print(f"wrote {out}  +  {out[:-5]}.md")
    print(f"  rounds={len(trace['rounds'])} agents={len(trace['agents'])} "
          f"peak_adv_share={trace['metrics'].get('peak_adversarial_share')}")


if __name__ == "__main__":
    main()
