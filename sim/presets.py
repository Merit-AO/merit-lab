"""
Preset scenarios — the legitimate baseline + the adversarial harness.

Each returns a Scenario. `baseline` is the time-to-trust story (an honest
newcomer earns weight; a noisy one stays pinned). The attacks show capture
stays bounded: anchoring pins un-vouched cliques near zero, and the tether
decays cheap faucet weight that doesn't predict outcomes.
"""
from __future__ import annotations

from .scenario import AgentSpec, Edge, Scenario

TOPICS = ["ai-safety", "markets", "governance"]


def baseline() -> Scenario:
    """Honest newcomer (nova) climbs; noisy participator (drift) stays pinned and
    gets slashed. Founders anchor trust. Reproduces merit/demo.py's headline result."""
    return Scenario(
        name="baseline",
        description="Time-to-trust: an honest newcomer earns weight through calibrated, staked "
                    "votes while a noisy participator stays near the floor.",
        agents=[
            AgentSpec("mira", is_founder=True, competence=.85, reasoning_survival=.85, stake_balance=10, sigma=.08, kind="founder"),
            AgentSpec("praxis", is_founder=True, competence=.85, reasoning_survival=.85, stake_balance=10, sigma=.08, kind="founder"),
            AgentSpec("anke", is_human=True, competence=.70, reasoning_survival=.70, stake_balance=2, sigma=.12, kind="human"),
            AgentSpec("nova", competence=.72, reasoning_survival=.70, stake_balance=1, sigma=.15, kind="newcomer"),
            AgentSpec("drift", competence=.60, reasoning_survival=.50, stake_balance=1, sigma=.42, kind="newcomer"),
        ],
        edges=[
            Edge("mira", "praxis"), Edge("praxis", "mira"),
            Edge("anke", "mira"), Edge("anke", "praxis"),
            Edge("mira", "nova", 1.0, None, round=4),   # trust earned outward once nova proves out
        ],
        topics=TOPICS, rounds=8, pool=1.0, top_k=2, slash=True,
    )


def sybil_swarm(n: int = 6) -> Scenario:
    """A swarm of vetted sybils that all vouch each other (a ring) but have NO edge
    from a founder. Anchoring should pin their aggregate weight near zero however
    confidently they vote."""
    agents = [
        AgentSpec("mira", is_founder=True, competence=.85, reasoning_survival=.85, stake_balance=10, sigma=.08, kind="founder"),
        AgentSpec("praxis", is_founder=True, competence=.85, reasoning_survival=.85, stake_balance=10, sigma=.08, kind="founder"),
    ]
    edges = [Edge("mira", "praxis"), Edge("praxis", "mira")]
    for i in range(1, n + 1):
        agents.append(AgentSpec(f"sybil{i}", competence=.6, reasoning_survival=.55,
                                stake_balance=0, vetted=True, sigma=.30, kind="sybil", strategy="pump"))
        for j in range(1, n + 1):
            if j != i:
                edges.append(Edge(f"sybil{i}", f"sybil{j}"))   # ring, no founder path
    return Scenario(name="sybil-swarm",
                    description=f"{n} vetted sybils vouch each other in a ring with NO founder edge. "
                                "Anchoring zeroes their trust, but the PoAW faucet + neutral priors "
                                "still floor the swarm at ~30% aggregate share — the residual leak to close.",
                    agents=agents, edges=edges, topics=TOPICS, rounds=6, pool=1.0, top_k=2, slash=False)


def poaw_farm(n: int = 8) -> Scenario:
    """Many vetted-but-untrusted identities (faucet stake only, no vouches) voting
    badly. The tether should decay their cheap faucet weight over rounds."""
    agents = [
        AgentSpec("mira", is_founder=True, competence=.85, reasoning_survival=.85, stake_balance=10, sigma=.08, kind="founder"),
        AgentSpec("praxis", is_founder=True, competence=.85, reasoning_survival=.85, stake_balance=10, sigma=.08, kind="founder"),
    ]
    for i in range(1, n + 1):
        agents.append(AgentSpec(f"farm{i}", competence=.5, reasoning_survival=.5,
                                stake_balance=0, vetted=True, sigma=.30, kind="sybil", strategy="adversarial"))
    return Scenario(name="poaw-farm",
                    description=f"{n} PoAW-vetted identities (faucet stake, no trust) confidently backing "
                                "BAD picks. The outcome-tether erodes their share over rounds (~0.36→0.25/8) "
                                "but only slowly — the faucet floor is what the tether can't fully claw back.",
                    agents=agents, edges=[Edge("mira", "praxis"), Edge("praxis", "mira")],
                    topics=TOPICS, rounds=8, pool=1.0, top_k=2, slash=False)


def collusion_ring(n: int = 4) -> Scenario:
    """A ring that mutually vouches AND coordinates confident votes to try to swing
    allocations. With no founder path their coordinated weight is still ~zero."""
    agents = [
        AgentSpec("mira", is_founder=True, competence=.85, reasoning_survival=.85, stake_balance=10, sigma=.08, kind="founder"),
        AgentSpec("praxis", is_founder=True, competence=.85, reasoning_survival=.85, stake_balance=10, sigma=.08, kind="founder"),
    ]
    edges = [Edge("mira", "praxis"), Edge("praxis", "mira")]
    for i in range(1, n + 1):
        agents.append(AgentSpec(f"ring{i}", competence=.7, reasoning_survival=.6,
                                stake_balance=3, vetted=True, sigma=.20, kind="sybil", strategy="pump"))
        for j in range(1, n + 1):
            if j != i:
                edges.append(Edge(f"ring{i}", f"ring{j}"))
    return Scenario(name="collusion-ring",
                    description=f"{n} colluders mutually vouch and vote in lockstep to pump a pick. "
                                "Anchoring zeroes their trust so they can't concentrate, but the faucet "
                                "still floors them at ~30% aggregate — bounded, yet larger than it should be.",
                    agents=agents, edges=edges, topics=TOPICS, rounds=6, pool=1.0, top_k=2, slash=False)


PRESETS = {
    "baseline": baseline,
    "sybil-swarm": sybil_swarm,
    "poaw-farm": poaw_farm,
    "collusion-ring": collusion_ring,
}
