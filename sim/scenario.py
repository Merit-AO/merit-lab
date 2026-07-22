"""
Scenario — the full parameter surface for a Merit AO what-if simulation.

Everything hardcoded in the engine's demo.py is a knob here: the roster, the
trust edges (general + topic-scoped), per-agent confidence noise, the candidate
stream, the round loop, the RoundConfig, and the aggregation constants that the
CLI never exposes (W_*, cap band, w_ref, ref_bond, PageRank damping, prior
strength, faucet). A Scenario is JSON-serializable so it can be saved under
scenarios/, driven by the CLI, or posted to the (Phase 2) sim server.

The engine itself is never reimplemented — engine.py drives the real `merit`
package with these values. This module only *describes* a run.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class AgentSpec:
    """A synthetic participant. Mirrors merit.model.Participant's live signals plus
    a `sigma` (how far its stated confidence drifts from a candidate's true quality
    — low = reliably calibrated, high = noise) and `vetted` (PoAW-passed → eligible
    for the stake faucet, like a real vetted SafeMolt handle)."""
    pid: str
    is_founder: bool = False
    is_human: bool = False
    competence: float = 0.5
    reasoning_survival: float = 0.5
    stake_balance: float = 0.0
    vetted: bool = False
    sigma: float = 0.20
    kind: str = "agent"       # free label for the viz: founder / human / newcomer / sybil / sleeper
    strategy: str = "honest"  # honest | pump (confidently back everything) | adversarial (back BAD picks)


@dataclass
class Edge:
    """A trust vouch. topic=None is general (context-free) trust; a topic string is
    typed trust. `round` is when it's added (0 = genesis); >0 models trust earned
    outward over time (a founder vouches a newcomer once it proves out)."""
    truster: str
    target: str
    weight: float = 1.0
    topic: str | None = None
    round: int = 0


@dataclass
class Overrides:
    """Aggregation constants. None = keep the engine's default. engine.py applies
    these in-process (module globals reassigned; default-arg constants patched)."""
    W_TRUST: float | None = None
    W_COMPETENCE: float | None = None
    W_PAYOUT: float | None = None
    W_REASONING: float | None = None
    CAP_FLOOR: float | None = None
    CAP_CEIL: float | None = None
    w_ref: float | None = None            # spend_cap saturation point
    ref_bond: float | None = None         # neurons.stake reference bond
    damping: float | None = None          # PageRank damping
    prior_strength: float | None = None   # neurons shrinkage strength
    faucet_stake: float | None = None     # operate.FAUCET_STAKE


@dataclass
class Scenario:
    name: str
    description: str = ""
    agents: list[AgentSpec] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    topics: list[str] = field(default_factory=lambda: ["general"])
    rounds: int = 8
    pool: float = 1.0
    seed: int = 42
    candidates_per_round: int = 4
    top_k: int | None = 2
    # RoundConfig knobs
    slash: bool = False               # production does NOT bond-slash; True models a hypothetical
    slash_confidence: float = 0.70
    bad_outcome: float = 0.30
    slash_fraction: float = 0.50
    delegate_floor_raw: float = 0.01
    # delegation quorums: {below-floor pid: [delegate pids]}
    quorums: dict[str, list[str]] = field(default_factory=dict)
    overrides: Overrides = field(default_factory=Overrides)
    # true_quality distribution for generated candidates: "uniform" | fixed float
    quality: str | float = "uniform"

    # ---- serialization ----
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Scenario":
        d = dict(d)
        d["agents"] = [AgentSpec(**a) for a in d.get("agents", [])]
        d["edges"] = [Edge(**e) for e in d.get("edges", [])]
        ov = d.get("overrides") or {}
        d["overrides"] = Overrides(**ov) if isinstance(ov, dict) else ov
        return cls(**d)
