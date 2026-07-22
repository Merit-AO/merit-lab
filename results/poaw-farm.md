# Merit AO simulation — poaw-farm

_8 PoAW-vetted identities (faucet stake, no trust) confidently backing BAD picks. The outcome-tether erodes their share over rounds (~0.36→0.25/8) but only slowly — the faucet floor is what the tether can't fully claw back._

> **SIMULATED** — synthetic identities on the real engine. Not live merit-state.

## Parameters

- rounds **8** · pool **1.0** · top_k **2** · seed **42** · slash **False** · topics ['ai-safety', 'markets', 'governance']
- agents: mira(founder), praxis(founder), farm1(sybil), farm2(sybil), farm3(sybil), farm4(sybil), farm5(sybil), farm6(sybil), farm7(sybil), farm8(sybil)

## Results

**Time-to-trust** (round a non-founder first clears the delegate floor):
- `farm1`: round 1
- `farm2`: round 1
- `farm3`: round 1
- `farm4`: round 1
- `farm5`: round 1
- `farm6`: round 1
- `farm7`: round 1
- `farm8`: round 1

**Capture-resistance** — peak aggregate share held by adversaries (farm1, farm2, farm3, farm4, farm5, farm6, farm7, farm8): **0.3622** (round 1). Adversary committed a payout: **True**.

**Founder share by round**: [0.6378, 0.6897, 0.7244, 0.751, 0.7624, 0.7515, 0.7481, 0.7501]

## Final standing (last round)

| agent | share | raw weight | cap | calibration |
|---|--:|--:|--:|--:|
| mira | 37.6% | 0.5410 | 5.00 | 0.9293 |
| praxis | 37.4% | 0.5389 | 5.00 | 0.9256 |
| farm5 | 3.4% | 0.0495 | 1.68 | 0.6357 |
| farm7 | 3.4% | 0.0493 | 1.68 | 0.6617 |
| farm8 | 3.3% | 0.0478 | 1.63 | 0.6328 |
| farm1 | 3.0% | 0.0434 | 1.48 | 0.616 |
| farm3 | 3.0% | 0.0432 | 1.48 | 0.5925 |
| farm6 | 3.0% | 0.0426 | 1.46 | 0.5916 |
| farm4 | 2.9% | 0.0423 | 1.45 | 0.5861 |
| farm2 | 2.9% | 0.0417 | 1.42 | 0.5738 |

## Verdict

- ⚠️ Adversaries reached 36.2% share and committed a payout — inspect the trust graph + tether.
- ✅ Earned ascension — farm1, farm2, farm3, farm4, farm5, farm6, farm7, farm8 climbed past the floor.
