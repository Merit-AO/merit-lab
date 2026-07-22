"""
run_scenario — drive the REAL Merit engine across rounds with synthetic
identities + tunable parameters, and emit a Trace the visualizer renders.

No math is reimplemented: weights, trust PageRank, the topic-aware tally, caps
and the neurons all come from the `merit` package (imported from the engine/
clone). This module only (a) applies the aggregation-constant overrides the CLI
can't reach — reassigning module globals and patching default-arg constants
in-process — and (b) orchestrates the round the way production does: the
topic-aware tally of cmd_round + the outcome-grading of resolve, plus optional
bond-slashing for hypotheticals. Each round is emitted in the exact merit-state
round-log schema so the viz has one renderer for real and simulated alike.
"""
from __future__ import annotations

import os
import random
import sys
from contextlib import contextmanager

# Import the real engine from the engine/ clone (sibling of sim/).
_ENGINE = os.environ.get("MERIT_ENGINE") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine")
if _ENGINE not in sys.path:
    sys.path.insert(0, _ENGINE)

from merit import neurons, nqg                      # noqa: E402
from merit.model import Candidate, Participant, Vote  # noqa: E402
from merit.round import RoundConfig, apply_delegation  # noqa: E402

from .scenario import Scenario                        # noqa: E402

UNIT = "MERIT"


def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


@contextmanager
def _overrides(ov):
    """Apply aggregation-constant overrides to the live engine, then restore.
    Module globals are reassigned; default-arg constants are patched via
    __defaults__ (they're bound at def-time, so a global reassignment alone
    wouldn't take — see the engine's own note)."""
    import merit.operate as operate
    saved_g = {k: getattr(nqg, k) for k in
               ("W_TRUST", "W_COMPETENCE", "W_PAYOUT", "W_REASONING", "CAP_FLOOR", "CAP_CEIL")}
    saved_faucet = operate.FAUCET_STAKE
    saved_cap_def = nqg.spend_cap.__defaults__
    saved_pr_def = nqg.trust_pagerank.__defaults__
    saved_stake_def = neurons.stake.__defaults__
    saved_shrink_def = neurons._shrink.__defaults__
    try:
        for k in saved_g:
            v = getattr(ov, k, None)
            if v is not None:
                setattr(nqg, k, v)
        if ov.faucet_stake is not None:
            operate.FAUCET_STAKE = ov.faucet_stake
        if ov.w_ref is not None:
            nqg.spend_cap.__defaults__ = (ov.w_ref,)
        if ov.damping is not None:
            d = list(saved_pr_def); d[1] = ov.damping      # (topic, damping, iterations, tol)
            nqg.trust_pagerank.__defaults__ = tuple(d)
        if ov.ref_bond is not None:
            neurons.stake.__defaults__ = (ov.ref_bond,)
        if ov.prior_strength is not None:
            s = list(saved_shrink_def); s[1] = ov.prior_strength  # (prior, strength)
            neurons._shrink.__defaults__ = tuple(s)
        yield
    finally:
        for k, v in saved_g.items():
            setattr(nqg, k, v)
        operate.FAUCET_STAKE = saved_faucet
        nqg.spend_cap.__defaults__ = saved_cap_def
        nqg.trust_pagerank.__defaults__ = saved_pr_def
        neurons.stake.__defaults__ = saved_stake_def
        neurons._shrink.__defaults__ = saved_shrink_def


def _build_participants(sc: Scenario):
    P = {}
    for a in sc.agents:
        p = Participant(a.pid, is_founder=a.is_founder, is_human=a.is_human,
                        competence=a.competence, reasoning_survival=a.reasoning_survival,
                        stake_balance=a.stake_balance)
        P[a.pid] = p
    # genesis edges (round 0)
    for e in sc.edges:
        if e.round == 0 and e.truster in P:
            P[e.truster].vouch_for(e.target, e.weight, e.topic)
    return P


def _apply_scheduled_edges(P, sc, r):
    added = 0
    for e in sc.edges:
        if e.round == r and e.truster in P:
            P[e.truster].vouch_for(e.target, e.weight, e.topic)
            added += 1
    return added


def _make_candidates(sc: Scenario, r: int, rng: random.Random):
    cands, meta = [], []
    for i in range(sc.candidates_per_round):
        topic = sc.topics[i % len(sc.topics)]
        q = rng.uniform(0.0, 1.0) if sc.quality == "uniform" else float(sc.quality)
        cid = f"r{r}c{i}"
        author = f"contrib-{topic}"
        cands.append(Candidate(cid, nominated_by=author, true_quality=round(q, 3)))
        meta.append({"candidate_id": cid, "title": f"{topic} contribution {r}.{i}",
                     "author": author, "topic": topic, "true_quality": round(q, 3)})
    return cands, meta


def _conf_for(strategy, true_q, sigma, rng):
    """Stated confidence by vote strategy. honest tracks true quality (noise=sigma);
    pump backs everything confidently (inflation); adversarial backs BAD picks
    confidently (funding low-quality) — which is what actually tanks calibration
    and lets the tether decay the attacker."""
    if strategy == "pump":
        return _clamp(0.85 + rng.gauss(0.0, 0.08))
    if strategy == "adversarial":
        return _clamp((1.0 - true_q) + rng.gauss(0.0, sigma))
    return _clamp(true_q + rng.gauss(0.0, sigma))


def _cast_votes(sc: Scenario, P, cands, r, rng):
    spec = {a.pid: a for a in sc.agents}
    votes = []
    for pid, p in P.items():
        s = spec.get(pid)
        sigma = s.sigma if s else 0.20
        strat = s.strategy if s else "honest"
        for c in cands:
            conf = _conf_for(strat, c.true_quality, sigma, rng)
            bond = round(0.5 * conf * min(1.0, p.stake_balance), 3)
            votes.append(Vote(r, pid, c.candidate_id, round(conf, 3), bond))
    return votes


def _snapshot_neurons(P, topic_trust_general):
    out = {}
    for pid, p in P.items():
        out[pid] = {"calibration": round(neurons.calibration(p), 4),
                    "stake": round(neurons.stake(p), 4),
                    "competence": round(neurons.competence(p), 4),
                    "payout": round(neurons.payout_quality(p), 4),
                    "reasoning": round(neurons.reasoning(p), 4),
                    "trust": round(topic_trust_general.get(pid, 0.0), 4)}
    return out


def run_scenario(sc: Scenario) -> dict:
    """Run the scenario and return a Trace (JSON-serializable)."""
    rng = random.Random(sc.seed)
    cfg = RoundConfig(top_k=sc.top_k, slash_confidence=sc.slash_confidence,
                      bad_outcome=sc.bad_outcome, slash_fraction=sc.slash_fraction,
                      delegate_floor_raw=sc.delegate_floor_raw)
    rounds_out = []
    traj = {a.pid: [] for a in sc.agents}

    with _overrides(sc.overrides):
        # faucet: a vetted agent with no stake gets the (possibly overridden) starter stake
        import merit.operate as operate
        P = _build_participants(sc)
        for a in sc.agents:
            if a.vetted and P[a.pid].stake_balance <= 0:
                P[a.pid].stake_balance = operate.FAUCET_STAKE

        for r in range(1, sc.rounds + 1):
            edges_added = _apply_scheduled_edges(P, sc, r)
            cands, cand_meta = _make_candidates(sc, r, rng)
            candidate_topics = {m["candidate_id"]: m["topic"] for m in cand_meta}
            votes = _cast_votes(sc, P, cands, r, rng)

            # permissionless join for any vote-only pid not in the roster (rare)
            for v in votes:
                if v.voter not in P:
                    P[v.voter] = Participant(v.voter)

            tally_votes = apply_delegation(P, votes, sc.quorums, cfg) if sc.quorums else votes

            # weights/caps global (as production does); scores topic-aware
            raw = nqg.raw_weights(P)
            weights = nqg.voting_weights(P)
            caps = {pid: nqg.spend_cap(raw[pid]) for pid in P}
            scores = nqg.tally(P, tally_votes, candidate_topics)
            allocated = nqg.allocate(scores, sc.pool, top_k=cfg.top_k)

            # authorize by cap (committer = highest-weight backer with conf > 0.5)
            supporters = {}
            for v in tally_votes:
                if v.confidence > 0.5:
                    supporters.setdefault(v.candidate, []).append(v)
            paid, clipped, committers = {}, {}, {}
            for cand, amount in allocated.items():
                bk = supporters.get(cand, [])
                if not bk or amount <= 0:
                    continue
                comm = max(bk, key=lambda v: weights.get(v.voter, 0.0)).voter
                committers[cand] = comm
                auth = min(amount, caps[comm])
                if auth < amount - 1e-12:
                    clipped[cand] = amount - auth
                paid[cand] = auth

            # accrue to authors
            authors = {m["candidate_id"]: m["author"] for m in cand_meta}
            accrued = {}
            for cand, amt in paid.items():
                h = authors.get(cand, "?")
                accrued[h] = accrued.get(h, 0.0) + amt

            # learn: grade outcomes (calibration/payout decay), optional slash, feed history
            resolved = {c.candidate_id: (c.true_quality or 0.0) for c in cands}
            funded_ids = {c for c, amt in paid.items() if amt > 0}
            slashes = {}
            for v in votes:  # original votes → each agent's own calibration
                v.outcome = resolved.get(v.candidate)
                v.funded = v.candidate in funded_ids
                if v.outcome is None:
                    continue
                if sc.slash and v.confidence >= cfg.slash_confidence and \
                        v.outcome <= cfg.bad_outcome and v.bond > 0:
                    burn = min(cfg.slash_fraction * v.bond, P[v.voter].stake_balance)
                    P[v.voter].stake_balance -= burn
                    P[v.voter].total_slashed += burn
                    v.slashed = burn
                    slashes[v.voter] = slashes.get(v.voter, 0.0) + burn
                P[v.voter].history.append(v)

            trust_general = nqg.trust_pagerank(P)
            log = {
                "round_id": r, "pool": sc.pool, "top_k": cfg.top_k, "unit": UNIT, "dry": True,
                "weights": {k: round(x, 6) for k, x in weights.items()},
                "raw_weights": {k: round(x, 6) for k, x in raw.items()},
                "caps": {k: round(x, 4) for k, x in caps.items()},
                "scores": {k: round(x, 6) for k, x in scores.items()},
                "allocated": {k: round(x, 6) for k, x in allocated.items()},
                "paid": {k: round(x, 6) for k, x in paid.items()},
                "committers": committers, "clipped": {k: round(x, 6) for k, x in clipped.items()},
                "accrued_pending": {k: round(x, 6) for k, x in accrued.items()},
                "candidate_topics": candidate_topics, "trust_edges_applied": edges_added,
                "candidates": cand_meta,
                "slashes": {k: round(x, 4) for k, x in slashes.items()},
                "neurons": _snapshot_neurons(P, trust_general),
                "votes": [{"voter": v.voter, "candidate": v.candidate,
                           "confidence": v.confidence, "bond": v.bond,
                           "external": not any(a.pid == v.voter and a.is_founder for a in sc.agents),
                           "rationale": ""} for v in votes],
            }
            rounds_out.append(log)
            for pid in P:
                traj[pid] = traj.get(pid, [])
                traj[pid].append({"round": r, "raw_weight": round(raw.get(pid, 0.0), 6),
                                  "share": round(weights.get(pid, 0.0), 6),
                                  "cap": round(caps.get(pid, 0.0), 4),
                                  "calibration": round(neurons.calibration(P[pid]), 4),
                                  "trust": round(trust_general.get(pid, 0.0), 4)})

    from merit import store
    participants_final = [store._p_to_dict(p) for p in P.values()]
    return {
        "kind": "sim",
        "scenario": sc.to_dict(),
        "topics": sc.topics,
        "agents": [{"pid": a.pid, "kind": a.kind, "is_founder": a.is_founder,
                    "is_human": a.is_human} for a in sc.agents],
        "rounds": rounds_out,
        "participants_final": participants_final,
        "trajectories": traj,
        "metrics": {},   # filled by metrics.summarize()
    }
