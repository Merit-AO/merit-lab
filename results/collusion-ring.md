# Merit AO simulation — collusion-ring

_4 colluders mutually vouch and vote in lockstep to pump a pick. Anchoring zeroes their trust so they can't concentrate, but the faucet still floors them at ~30% aggregate — bounded, yet larger than it should be._

> **SIMULATED** — synthetic identities on the real engine. Not live merit-state.

## Parameters

- rounds **6** · pool **1.0** · top_k **2** · seed **42** · slash **False** · topics ['ai-safety', 'markets', 'governance']
- agents: mira(founder), praxis(founder), ring1(sybil), ring2(sybil), ring3(sybil), ring4(sybil)

## Results

**Time-to-trust** (round a non-founder first clears the delegate floor):
- `ring1`: round 1
- `ring2`: round 1
- `ring3`: round 1
- `ring4`: round 1

**Capture-resistance** — peak aggregate share held by adversaries (ring1, ring2, ring3, ring4): **0.3058** (round 1). Adversary committed a payout: **True**.

**Founder share by round**: [0.6942, 0.7479, 0.7226, 0.733, 0.731, 0.726]

## Final standing (last round)

| agent | share | raw weight | cap | calibration |
|---|--:|--:|--:|--:|
| praxis | 36.3% | 0.5228 | 5.00 | 0.9104 |
| mira | 36.3% | 0.5222 | 5.00 | 0.9094 |
| ring4 | 6.9% | 0.0998 | 3.34 | 0.7586 |
| ring3 | 6.8% | 0.0986 | 3.30 | 0.7458 |
| ring1 | 6.8% | 0.0981 | 3.29 | 0.7478 |
| ring2 | 6.8% | 0.0980 | 3.28 | 0.7468 |

## Verdict

- ⚠️ Adversaries reached 30.6% share and committed a payout — inspect the trust graph + tether.
- ✅ Earned ascension — ring1, ring2, ring3, ring4 climbed past the floor.
