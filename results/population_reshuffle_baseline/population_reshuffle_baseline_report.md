# Population Reshuffle Baseline

## Purpose

This analysis adds a simple population-level random-mixing baseline for the EOA-only K4, K5, and K6 transaction-network validation results.
It asks what same-role transaction concentration would be expected if wallet labels were randomly mixed across the population while preserving the cluster-size distribution.
This is not a replacement for the edge-level shuffled-label test; it is an additional baseline that makes the role-size effect easier to explain in the paper.

## Summary

| k | Population expected same-role ratio | Observed same-role ratio | Population lift | Edge-shuffle null mean | Edge-shuffle lift | Edge-shuffle p-value |
|---:|---:|---:|---:|---:|---:|---:|
| 4 | 0.3255 | 0.4304 | 1.32x | 0.3426 | 1.26x | 0.0099 |
| 5 | 0.2809 | 0.2955 | 1.05x | 0.2982 | 0.99x | 0.5644 |
| 6 | 0.2126 | 0.2739 | 1.29x | 0.2452 | 1.12x | 0.0495 |

## Interpretation

- K4: Observed same-role transaction concentration is above both the population random-mixing baseline and the edge-level shuffled-label null, supporting K4 as the strongest conservative network-aligned taxonomy.

- K5: Observed same-role transaction concentration is slightly above the population random-mixing baseline but close to, and slightly below, the edge-level shuffled-label null, so K5 should be described as network-mixed rather than strongly network-validated.

- K6: Observed same-role transaction concentration is above the population random-mixing baseline and borderline above the edge-level shuffled-label null, but K6 remains less stable than K5.

## Paper Wording

A population-level random-mixing baseline was added to separate cluster-size effects from network alignment.
For each candidate taxonomy, the expected same-role transaction ratio under random population mixing is the sum of squared cluster shares.
K4 shows the clearest network alignment, with an observed same-role ratio above both the population baseline and the edge-level shuffled-label null.
K5 remains the preferred richer behavioural taxonomy, but its same-role transaction concentration is only slightly above the population baseline and is not above the edge-level shuffled-label null.
Therefore, K5 should be described as feature-space and temporally supported, with mixed same-role network evidence.
