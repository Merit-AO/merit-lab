# Merit AO simulation — baseline

_Time-to-trust: an honest newcomer earns weight through calibrated, staked votes while a noisy participator stays near the floor._

> **SIMULATED** — synthetic identities on the real engine. Not live merit-state.

## Parameters

- rounds **8** · pool **1.0** · top_k **2** · seed **42** · slash **True** · topics ['ai-safety', 'markets', 'governance']
- agents: mira(founder), praxis(founder), anke(human), nova(newcomer), drift(newcomer)

## Results

**Time-to-trust** (round a non-founder first clears the delegate floor):
- `anke`: round 1
- `nova`: round 1
- `drift`: round 1

**Founder share by round**: [0.846, 0.8456, 0.8419, 0.829, 0.8275, 0.8254, 0.8253, 0.8257]

## Final standing (last round)

| agent | share | raw weight | cap | calibration |
|---|--:|--:|--:|--:|
| mira | 43.8% | 0.5351 | 5.00 | 0.9278 |
| praxis | 38.8% | 0.4743 | 5.00 | 0.9273 |
| anke | 8.2% | 0.0997 | 3.34 | 0.9213 |
| nova | 7.2% | 0.0878 | 2.95 | 0.9208 |
| drift | 2.1% | 0.0256 | 0.89 | 0.8636 |

## Verdict

- ✅ Earned ascension — anke, nova, drift climbed past the floor.
