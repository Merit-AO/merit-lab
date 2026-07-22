"""
report — a human-readable markdown report for a Trace, so every simulation a
routine runs leaves an auditable write-up (params → outcomes → verdict).
"""
from __future__ import annotations


def diff_markdown(a: dict, b: dict, la: str = "current", lb: str = "proposed") -> str:
    """Recalibration-preview: compare two runs of the same scenario under different
    parameters. Leads with the metric deltas so a PR reviewer sees the effect at a
    glance. `a` = current params, `b` = proposed."""
    ma, mb = a.get("metrics", {}), b.get("metrics", {})
    ova = {k: v for k, v in (a["scenario"].get("overrides") or {}).items() if v is not None}
    ovb = {k: v for k, v in (b["scenario"].get("overrides") or {}).items() if v is not None}
    L = [f"# Recalibration preview — {a['scenario']['name']}\n",
         "> **SIMULATED** — the real engine under two parameter sets. Not live merit-state; no tally run.\n",
         f"- **{la}**: overrides {ova or '(defaults)'}",
         f"- **{lb}**: overrides {ovb or '(defaults)'}\n",
         "## Effect\n",
         "| metric | " + la + " | " + lb + " | Δ |", "|---|--:|--:|--:|"]
    def row(name, va, vb, pct=False, good_down=True):
        d = (vb or 0) - (va or 0)
        f = (lambda x: f"{x*100:.1f}%") if pct else (lambda x: f"{x}")
        arrow = "→" if abs(d) < 1e-9 else ("↓" if d < 0 else "↑")
        L.append(f"| {name} | {f(va or 0)} | {f(vb or 0)} | {arrow} {f(abs(d)) if pct else round(d,4)} |")
    row("peak adversary share", ma.get("peak_adversarial_share"), mb.get("peak_adversarial_share"), pct=True)
    fa = (ma.get("founder_share_by_round") or [0])[-1]; fb = (mb.get("founder_share_by_round") or [0])[-1]
    row("final founder share", fa, fb, pct=True)
    L.append(f"| adversary won a payout | {ma.get('adversary_committed_a_payout')} | "
             f"{mb.get('adversary_committed_a_payout')} | |")
    ttA = sum(1 for r in (ma.get("time_to_trust") or {}).values() if r)
    ttB = sum(1 for r in (mb.get("time_to_trust") or {}).values() if r)
    L.append(f"| honest agents that ascended | {ttA} | {ttB} | |")
    L.append("")
    # verdict
    dcap = (mb.get("peak_adversarial_share", 0) - ma.get("peak_adversarial_share", 0))
    L.append("## Verdict\n")
    if dcap < -0.02:
        L.append(f"✅ The proposed change **cuts peak adversary share by "
                 f"{abs(dcap)*100:.1f} points** ({ma.get('peak_adversarial_share',0)*100:.1f}% → "
                 f"{mb.get('peak_adversarial_share',0)*100:.1f}%). Recommend proposing via a reviewed PR.")
    elif dcap > 0.02:
        L.append(f"⚠️ The proposed change **increases** adversary share by {dcap*100:.1f} points — reject.")
    else:
        L.append("→ Negligible effect on capture; weigh against its cost to honest ascension.")
    return "\n".join(L) + "\n"


def to_markdown(trace: dict) -> str:
    sc = trace["scenario"]
    m = trace.get("metrics", {})
    rounds = trace["rounds"]
    L = []
    L.append(f"# Merit AO simulation — {sc['name']}\n")
    if sc.get("description"):
        L.append(f"_{sc['description']}_\n")
    L.append("> **SIMULATED** — synthetic identities on the real engine. Not live merit-state.\n")

    L.append("## Parameters\n")
    ov = {k: v for k, v in (sc.get("overrides") or {}).items() if v is not None}
    L.append(f"- rounds **{sc['rounds']}** · pool **{sc['pool']}** · top_k **{sc['top_k']}** · "
             f"seed **{sc['seed']}** · slash **{sc['slash']}** · topics {sc['topics']}")
    L.append(f"- agents: {', '.join(a['pid']+'('+a.get('kind','agent')+')' for a in sc['agents'])}")
    if ov:
        L.append(f"- overrides: {ov}")
    L.append("")

    L.append("## Results\n")
    ttt = m.get("time_to_trust", {})
    if ttt:
        L.append("**Time-to-trust** (round a non-founder first clears the delegate floor):")
        for pid, r in ttt.items():
            L.append(f"- `{pid}`: {'round '+str(r) if r else 'never (stayed near zero)'}")
        L.append("")
    if m.get("adversarial_pids"):
        L.append(f"**Capture-resistance** — peak aggregate share held by adversaries "
                 f"({', '.join(m['adversarial_pids'])}): **{m.get('peak_adversarial_share')}** "
                 f"(round {m.get('peak_adversarial_round')}). "
                 f"Adversary committed a payout: **{m.get('adversary_committed_a_payout')}**.\n")
    if m.get("founder_share_by_round"):
        L.append(f"**Founder share by round**: {m['founder_share_by_round']}\n")

    # final standing
    last = rounds[-1] if rounds else {}
    if last:
        L.append("## Final standing (last round)\n")
        L.append("| agent | share | raw weight | cap | calibration |")
        L.append("|---|--:|--:|--:|--:|")
        nz = last.get("neurons", {})
        for pid in sorted(last["weights"], key=lambda p: -last["weights"][p]):
            L.append(f"| {pid} | {last['weights'][pid]*100:.1f}% | {last['raw_weights'][pid]:.4f} | "
                     f"{last['caps'].get(pid,0):.2f} | {nz.get(pid,{}).get('calibration','—')} |")
        L.append("")

    # verdict
    L.append("## Verdict\n")
    verdict = []
    if m.get("adversarial_pids"):
        held = m.get("peak_adversarial_share", 0)
        if held < 0.15 and not m.get("adversary_committed_a_payout"):
            verdict.append(f"✅ Capture resisted — adversaries peaked at {held*100:.1f}% share and "
                           "never committed a payout.")
        else:
            verdict.append(f"⚠️ Adversaries reached {held*100:.1f}% share"
                           f"{' and committed a payout' if m.get('adversary_committed_a_payout') else ''} "
                           "— inspect the trust graph + tether.")
    honest_climbers = [p for p, r in (m.get("time_to_trust") or {}).items() if r]
    if honest_climbers:
        verdict.append(f"✅ Earned ascension — {', '.join(honest_climbers)} climbed past the floor.")
    L.append("\n".join("- " + v for v in verdict) if verdict else "- (no automated verdict)")
    return "\n".join(L) + "\n"
