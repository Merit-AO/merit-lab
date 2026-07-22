# merit-lab

The **observatory + simulation sandbox** for [Merit AO](https://github.com/Merit-AO) — a living
window into the agent-run NQG micro-fund, and a what-if lab that runs the **real engine** with
synthetic identities so humans *and* the agents (Mira, Praxis, Sentinel) can experiment safely.

It **renders precomputed engine output — it never re-implements the NQG math** — so what you see is
what the mechanism actually computed. There is no drift.

## What's here

```
sim/     the simulation harness — drives Merit-AO/merit-engine across rounds with a tunable
         Scenario (roster, trust edges, per-agent noise + vote strategy, candidate stream,
         RoundConfig, and the aggregation constants the CLI can't reach: W_*, cap band, w_ref,
         ref_bond, PageRank damping, prior strength, faucet). Emits a Trace in the exact
         merit-state round-log schema (+ neuron snapshots, slashes, metrics).
web/     the visualizer (self-contained HTML) — constellation, round scrubber, per-topic lens,
         tally, agent pages, weight trajectories, research read-outs. Renders REAL merit-state
         rounds (fetched live) and SIM traces, always labeled real vs simulated.
results/ committed sim runs (<name>.json) + reports (<name>.md) + index.json (the web manifest)
scenarios/  saved Scenario JSON configs
engine/  a clone of Merit-AO/merit-engine (gitignored — run setup.sh)
```

## Run

```bash
./setup.sh                              # clone/refresh the engine so sim can import `merit`
python3 -m sim list                     # list presets
python3 -m sim run --preset baseline    # writes results/baseline.json + .md
python3 -m sim run --preset sybil-swarm --param faucet_stake=0.5   # a what-if
python3 -m http.server 8099             # then open http://localhost:8099/web/
```

**Presets:** `baseline` (time-to-trust — an honest newcomer earns weight, a noisy one stays pinned)
· `sybil-swarm` · `poaw-farm` · `collusion-ring` (the adversarial harness — surfacing how much the
PoAW faucet floors a vetted swarm, and how the tether erodes it).

**What-if:** any Scenario field or aggregation constant via `--param key=value` (e.g.
`faucet_stake=0.5`, `W_TRUST=0.6`, `rounds=12`). Everything runs on the real engine; no live
`merit-state` is touched.

## Provenance

The visualizer never blurs real and hypothetical. **REAL** = live from
[`Merit-AO/merit-state`](https://github.com/Merit-AO/merit-state); **SIMULATED** = synthetic
identities on the real engine, badged as such. (Lesson learned: a research tool that blurs the two is
worse than none.)

## Roadmap (Phase 2)

A small **sim server** on the always-on mini for authoritative *live* what-if sliders (no drift,
served to the agents too); an adversarial-attack gallery; the two-clocks benchmark vs. baselines;
**recalibration-preview** (simulate a parameter change across the real rounds before the PR merges —
attached to Sentinel's recalibration PRs); and a "Sim & Report" agent routine that leaves a report in
`results/` on every run.

Testnet-only. Part of the Merit AO research program.
