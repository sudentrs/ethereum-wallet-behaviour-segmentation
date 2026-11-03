# Completed year-end validation

All twelve supplied raw transfer months and all twelve daily CSVs were processed.
Daily validation rejects invalid dates/addresses/counts and duplicate wallet-day records.
Monthly training samples are selected after sorting normalized wallet IDs.

## Network comparisons

|   k |   label_seed |   months |   significant_months |   mean_excess |   min_excess |   max_excess |   min_adjusted_p |   max_adjusted_p |
|----:|-------------:|---------:|---------------------:|--------------:|-------------:|-------------:|-----------------:|-----------------:|
|   2 |          492 |       12 |                    3 |   -0.00942623 |   -0.0675282 |   0.0761699  |           0.0084 |           1      |
|   3 |          492 |       12 |                   12 |    0.090926   |    0.0298587 |   0.133227   |           0.0084 |           0.0084 |
|   3 |          493 |       12 |                   12 |    0.0840336  |    0.0265712 |   0.124862   |           0.0084 |           0.0084 |
|   3 |          494 |       12 |                   12 |    0.0953645  |    0.0327467 |   0.137405   |           0.0084 |           0.0084 |
|   4 |          492 |       12 |                   12 |    0.141911   |    0.0749464 |   0.182524   |           0.0084 |           0.0084 |
|   5 |          492 |       12 |                   12 |    0.0835328  |    0.0414804 |   0.109974   |           0.0084 |           0.0084 |
|   6 |          492 |       12 |                    0 |   -0.0382506  |   -0.0714269 |   0.00520972 |           1      |           1      |

Excesses are proportions; multiply by 100 for percentage points. Significance uses the
single 84-test Holm family, with 9,999 permutations and shared monthly edge samples.
A nonsignificant upper-tail test is not evidence of equivalence or a lower-tail test.

## Matched-estimator holdouts

| removed_family            |   features_removed |   features_retained |   ari_vs_full_k3 |   nmi_vs_full_k3 |   hungarian_agreement_vs_full_k3 |
|:--------------------------|-------------------:|--------------------:|-----------------:|-----------------:|---------------------------------:|
| activity_level            |                  5 |                  11 |         0.392656 |         0.425013 |                         0.780492 |
| persistence_concentration |                  4 |                  12 |         0.357416 |         0.44578  |                         0.595446 |
| directionality            |                  7 |                   9 |         0.711175 |         0.609186 |                         0.909295 |

## All monthly resolutions

|   k |   persistence_min |   persistence_max |   chance_min |   chance_max |   kappa_min |   kappa_max |   return_excess_min |   return_excess_max |   significant_returns |   max_adjusted_return_p |
|----:|------------------:|------------------:|-------------:|-------------:|------------:|------------:|--------------------:|--------------------:|----------------------:|------------------------:|
|   2 |          0.796768 |          0.830879 |     0.652803 |     0.693373 |    0.41465  |    0.448447 |        -1.66533e-16 |        -1.11022e-16 |                     0 |                    1    |
|   3 |          0.639422 |          0.701783 |     0.490565 |     0.538989 |    0.2922   |    0.353124 |         0.0187921   |         0.0257769   |                     4 |                    0.02 |
|   4 |          0.521038 |          0.559586 |     0.379081 |     0.406416 |    0.225667 |    0.258043 |         0.0361378   |         0.0507059   |                     4 |                    0.02 |
|   5 |          0.474747 |          0.487021 |     0.328213 |     0.34203  |    0.201707 |    0.229416 |         0.0415647   |         0.0580724   |                     4 |                    0.02 |
|   6 |          0.426606 |          0.438696 |     0.263952 |     0.289885 |    0.194686 |    0.220982 |         0.0498004   |         0.06145     |                     4 |                    0.02 |

Twenty monthly return tests across K2--K6 form a separate Holm family.
For K2, the starting state of a first-step switcher is fixed by the middle state.
Shuffling future labels within middle-state groups leaves binary return counts unchanged;
the resulting p=1 is structurally uninformative and must not be read as evidence against temporal structure.
## Deterministic held-out K3 excerpt

|   k |   month_from |   month_to |      n |   observed |   chance |    kappa |
|----:|-------------:|-----------:|-------:|-----------:|---------:|---------:|
|   3 |       202207 |     202208 | 676741 |   0.701783 | 0.538989 | 0.353124 |
|   3 |       202208 |     202209 | 769433 |   0.684286 | 0.517699 | 0.3454   |
|   3 |       202209 |     202210 | 786661 |   0.675171 | 0.515035 | 0.330202 |
|   3 |       202210 |     202211 | 769810 |   0.659419 | 0.506515 | 0.309844 |
|   3 |       202211 |     202212 | 763039 |   0.639422 | 0.490565 | 0.2922   |

|   k |   month_start |   n_switchers |   observed |   null_mean |   exact_expectation |     p |   p_holm_all_tests |
|----:|--------------:|--------------:|-----------:|------------:|--------------------:|------:|-------------------:|
|   3 |        202207 |        159677 |   0.419071 |    0.400279 |            0.400273 | 0.001 |               0.02 |
|   3 |        202208 |        178375 |   0.470929 |    0.448218 |            0.448231 | 0.001 |               0.02 |
|   3 |        202209 |        193027 |   0.40858  |    0.382803 |            0.382789 | 0.001 |               0.02 |
|   3 |        202210 |        191976 |   0.458917 |    0.436632 |            0.436626 | 0.001 |               0.02 |

## Reproduction limits

Features and scaled matrix match the archived hashes. Thirteen of fifteen annual label arrays
match exactly; K3 seed494 and K6 seed493 are explicitly identified as reproduced fits.
All five seed492 references and K3 seed493 match archived labels.
The validated, deterministically sampled monthly model supersedes the old unsorted training run.
Its numerical persistence rates differ because deterministic ordering changes the seeded training sample.
training_order_sensitivity.csv retains the old and intermediate summaries for transparent comparison;
this is a preprocessing diagnostic, not a prespecified random-seed robustness study.
See annual_reproduction_audit.json, per-source hashes and REPRODUCE_CURRENT_VALIDATION.md.
No new RPC scan, causal claim, token-value aggregation, or permanent EOA claim is made.

## Final manuscript verification

The expanded manuscript follows the supplied example's Introduction, Motivation, Related Work, Methodology, Results, Discussion and Conclusion structure. It is exactly ten IEEE conference pages including references, with nine figures and ten tables.
All empirical results use the completed year-end code-free count/activity pipeline; previous-cohort frequency-domain findings are not reused.
34 tests passed. The PDF was compiled with Tectonic 0.17.0 and all ten pages were visually reviewed. No unresolved references, missing characters or overfull boxes were found.
The final PDF and Overleaf source ZIP are under `output/pdf/`. `overleaf/manuscript_inputs.json` freezes the numerical inputs, and `scripts/build_extended_manuscript.py` rebuilds tables and the manuscript.
The previous five-page manuscript is archived locally under `tmp/pdfs/pre_ten_page/`. Changes remain local.
