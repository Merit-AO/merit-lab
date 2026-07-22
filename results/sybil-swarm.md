# Merit AO simulation — sybil-swarm

_6 vetted sybils vouch each other in a ring with NO founder edge. Anchoring zeroes their trust, but the PoAW faucet + neutral priors still floor the swarm at ~30% aggregate share — the residual leak to close._

> **SIMULATED** — synthetic identities on the real engine. Not live merit-state.

## Parameters

- rounds **6** · pool **1.0** · top_k **2** · seed **42** · slash **False** · topics ['ai-safety', 'markets', 'governance']
- agents: mira(founder), praxis(founder), sybil1(sybil), sybil2(sybil), sybil3(sybil), sybil4(sybil), sybil5(sybil), sybil6(sybil)

## Results

**Time-to-trust** (round a non-founder first clears the delegate floor):
- `sybil1`: round 1
- `sybil2`: round 1
- `sybil3`: round 1
- `sybil4`: round 1
- `sybil5`: round 1
- `sybil6`: round 1

**Capture-resistance** — peak aggregate share held by adversaries (sybil1, sybil2, sybil3, sybil4, sybil5, sybil6): **0.3173** (round 1). Adversary committed a payout: **True**.

**Founder share by round**: [0.6827, 0.7359, 0.7118, 0.7076, 0.7031, 0.705]

## Final standing (last round)

| agent | share | raw weight | cap | calibration |
|---|--:|--:|--:|--:|
| mira | 35.3% | 0.5229 | 5.00 | 0.9114 |
| praxis | 35.2% | 0.5228 | 5.00 | 0.911 |
| sybil5 | 5.1% | 0.0750 | 2.53 | 0.7773 |
| sybil1 | 5.0% | 0.0739 | 2.49 | 0.7697 |
| sybil3 | 4.9% | 0.0733 | 2.47 | 0.7727 |
| sybil6 | 4.9% | 0.0721 | 2.43 | 0.7656 |
| sybil4 | 4.9% | 0.0720 | 2.43 | 0.7599 |
| sybil2 | 4.8% | 0.0712 | 2.40 | 0.7542 |

## Verdict

- ⚠️ Adversaries reached 31.7% share and committed a payout — inspect the trust graph + tether.
- ✅ Earned ascension — sybil1, sybil2, sybil3, sybil4, sybil5, sybil6 climbed past the floor.
