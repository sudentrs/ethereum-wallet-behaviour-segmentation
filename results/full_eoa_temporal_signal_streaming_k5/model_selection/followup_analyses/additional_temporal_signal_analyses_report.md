# Additional Temporal Signal Analyses

This note adds three follow-up analyses requested after the initial time-domain and wavelength report.

## 1. Temporal Transition Predictiveness

- Total consecutive wallet-month pairs: `7,351,546`.
- Overall self-transition rate: `50.0%`.
- Next-state entropy: `1.783` bits.
- Conditional entropy after knowing current state: `1.613` bits.
- Entropy reduction / normalized predictiveness: `9.5%`.

| Current state | Self-transition | Top next state | Top-next probability | Lift vs marginal |
|---:|---:|---:|---:|---:|
| 0 | 48.6% | 0 | 48.6% | 1.73x |
| 1 | 44.7% | 1 | 44.7% | 1.85x |
| 2 | 55.8% | 2 | 55.8% | 1.29x |
| 3 | 41.2% | 3 | 41.2% | 15.57x |
| 4 | 28.4% | 4 | 28.4% | 14.58x |

Interpretation: the current monthly behavior state carries measurable information about the next monthly state. The effect is moderate, not deterministic, which is appropriate for behavioral wallet states.

## 2. Behavior K5 x Signal Outcome Profiling

### Time-domain dominant profile by Behavior K5

| Behavior K5 | Dominant TD state | Share | Mean active days | Mean switches | Mean inactive gap | Mean burstiness |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | TD2 | 66.2% | 9.82 | 15.45 | 206.40 | 0.332 |
| 1 | TD2 | 33.2% | 9.05 | 15.33 | 183.63 | 0.381 |
| 2 | TD1 | 76.5% | 3.30 | 3.60 | 289.71 | 0.544 |
| 3 | TD0 | 33.5% | 24.96 | 30.78 | 151.47 | 0.936 |
| 4 | TD3 | 44.8% | 32.80 | 47.49 | 109.15 | 0.680 |

### Wavelength K3 rhythm relationship by Behavior K5

| Behavior K5 | Dominant W state | Share | Enrichment vs global | Rhythm interpretation |
|---:|---:|---:|---:|---|
| 0 | W0 | 50.2% | 0.95x | distributed rhythm |
| 1 | W0 | 69.9% | 1.33x | distributed rhythm |
| 2 | W1 | 58.0% | 1.42x | distributed rhythm |
| 3 | W1 | 48.8% | 1.19x | distributed rhythm |
| 4 | W1 | 46.9% | 1.15x | distributed rhythm |

### Wavelength K3 global rhythm profiles

| W state | Wallet share | Dominant period | High-frequency share | Low-frequency share | Entropy | Interpretation |
|---:|---:|---:|---:|---:|---:|---|
| W0 | 52.7% | 74.73 | 0.821 | 0.057 | 6.952 | short/medium distributed rhythm |
| W1 | 40.9% | 299.92 | 0.701 | 0.131 | 6.789 | longer distributed rhythm |
| W2 | 6.4% | 342.51 | 0.429 | 0.366 | 5.799 | slow-cycle concentrated rhythm |

Interpretation: Behavior K5 roles have different time-domain profiles and different wavelength K3 rhythm enrichments. This supports the claim that the static K5 taxonomy carries temporal signatures.

## 3. Returner and One-Time Switcher Bridge

This bridge uses the existing monthly K5 trajectory summary by starting behavior state and relates it to the signal-cluster enrichments observed in the full EOA temporal signal analysis.

| Behavior K5 start | Returner share | One-time switcher share | TD4 intermittent enrichment | W2 slow-cycle enrichment |
|---:|---:|---:|---:|---:|
| 0 | 29.8% | 32.7% | 0.00x | 0.60x |
| 1 | 37.0% | 31.0% | 0.00x | 0.07x |
| 2 | 36.5% | 18.6% | 0.04x | 2.14x |
| 3 | 23.3% | 27.4% | 5.32x | 4.55x |
| 4 | 51.5% | 13.7% | 3.59x | 1.85x |

Interpretation: Behavior K5 cluster 3 combines a high one-time-switcher share with strong intermittent-switching and slow-cycle signal enrichment. Behavior K5 clusters 1, 2, and 4 are more returner-oriented, but cluster 4 has weaker monthly self-persistence and still carries slow-cycle signal enrichment.