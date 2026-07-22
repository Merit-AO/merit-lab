"""
Metrics — the research read-outs computed from a Trace.

Time-to-trust: rounds until an honest non-founder first clears the delegate
floor. Capture-resistance: the largest voting share any non-founder (esp. a
sybil/ring) ever reaches, and whether it swung an allocation. These are the two
clocks the observatory plots and the numbers a report leads with.
"""
from __future__ import annotations


def summarize(trace: dict, delegate_floor: float = 0.01) -> dict:
    rounds = trace["rounds"]
    agents = {a["pid"]: a for a in trace["agents"]}
    founders = {p for p, a in agents.items() if a.get("is_founder")}
    kinds = {a["pid"]: a.get("kind", "agent") for a in trace["agents"]}

    # time-to-trust: first round each non-founder's raw_weight exceeds the floor
    ttt = {}
    for pid, a in agents.items():
        if a.get("is_founder"):
            continue
        first = None
        for rl in rounds:
            if rl["raw_weights"].get(pid, 0.0) > delegate_floor:
                first = rl["round_id"]; break
        ttt[pid] = first

    # capture: peak aggregate voting share held by adversarial kinds (sybil/ring/sleeper)
    adversarial = {p for p, k in kinds.items() if k in ("sybil", "ring", "sleeper")}
    peak_adv_share = 0.0
    peak_adv_round = None
    for rl in rounds:
        s = sum(rl["weights"].get(p, 0.0) for p in adversarial)
        if s > peak_adv_share:
            peak_adv_share, peak_adv_round = s, rl["round_id"]

    # did any adversary ever commit (win) a funded candidate?
    adv_committed = any(who in adversarial for rl in rounds for who in rl.get("committers", {}).values())

    # founder share trajectory (concentration over time)
    founder_share = [round(sum(rl["weights"].get(f, 0.0) for f in founders), 4) for rl in rounds]

    return {
        "time_to_trust": ttt,
        "adversarial_pids": sorted(adversarial),
        "peak_adversarial_share": round(peak_adv_share, 4),
        "peak_adversarial_round": peak_adv_round,
        "adversary_committed_a_payout": adv_committed,
        "founder_share_by_round": founder_share,
        "rounds": len(rounds),
        "delegate_floor": delegate_floor,
    }
