"""
report — a human-readable markdown report for a Trace, so every simulation a
routine runs leaves an auditable write-up (params → outcomes → verdict).
"""
from __future__ import annotations


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
