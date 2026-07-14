# Academic Temporal Validation Pack

## Purpose

This package reformats the temporal analysis into paper-ready tests and visuals. It follows the same logic as the earlier six-cluster work: transition matrices, state stability, monthly composition shifts, and statistical checks against null or baseline behaviour.

The report does not claim that external events caused wallet-state transitions. It tests whether event-adjacent months coincide with unusual transition behaviour, then reports the evidence cautiously.

## Event Months Used As Candidate Explanatory Windows

|   event_month | event_label                                | scope                       | source                                     | source_url                                                  |
|--------------:|:-------------------------------------------|:----------------------------|:-------------------------------------------|:------------------------------------------------------------|
|        202205 | Terra/UST-LUNA collapse                    | market-wide crypto stress   | Briola et al. 2022; Kim et al. 2022; Wired | https://arxiv.org/abs/2207.13914                            |
|        202206 | Celsius withdrawal halt / liquidity stress | centralized-lending stress  | crypto-market timelines and news reports   | https://en.wikipedia.org/wiki/Cryptocurrency_bubble         |
|        202209 | Ethereum Merge                             | Ethereum protocol event     | Kapengut and Mizrach 2022                  | https://arxiv.org/abs/2210.13655                            |
|        202211 | FTX collapse and bankruptcy                | market-wide exchange crisis | AP timeline; bankruptcy filings/news       | https://apnews.com/article/c519d50b9059aa8bff0ce8b6cd26c40e |

## Event-Adjacent Transition Tests

Rank p-values compare an event-adjacent month pair with all 11 month pairs in 2022. Small values mean that the event-adjacent pair is unusually high or low relative to the observed year. This is a descriptive nonparametric test because the number of monthly pairs is small.

|   k |   event_month | metric                | direction_tested   |   observed |   all_month_pair_mean |   non_event_mean |   event_mean |   rank_p_value |
|----:|--------------:|:----------------------|:-------------------|-----------:|----------------------:|-----------------:|-------------:|---------------:|
|   4 |        202205 | composition_l1_change | higher             |  0.0422674 |             0.0883398 |        0.079448  |     0.1039   |       0.916667 |
|   4 |        202206 | composition_l1_change | higher             |  0.144331  |             0.0883398 |        0.079448  |     0.1039   |       0.166667 |
|   4 |        202209 | composition_l1_change | higher             |  0.103192  |             0.0883398 |        0.079448  |     0.1039   |       0.5      |
|   4 |        202211 | composition_l1_change | higher             |  0.12581   |             0.0883398 |        0.079448  |     0.1039   |       0.333333 |
|   4 |        202205 | self_transition_rate  | lower              |  0.526206  |             0.513618  |        0.514743  |     0.51165  |       0.916667 |
|   4 |        202206 | self_transition_rate  | lower              |  0.512467  |             0.513618  |        0.514743  |     0.51165  |       0.416667 |
|   4 |        202209 | self_transition_rate  | lower              |  0.525964  |             0.513618  |        0.514743  |     0.51165  |       0.833333 |
|   4 |        202211 | self_transition_rate  | lower              |  0.481964  |             0.513618  |        0.514743  |     0.51165  |       0.166667 |
|   4 |        202205 | mean_row_entropy_bits | higher             |  1.5637    |             1.56928   |        1.56964   |     1.56864  |       0.583333 |
|   4 |        202206 | mean_row_entropy_bits | higher             |  1.55195   |             1.56928   |        1.56964   |     1.56864  |       0.833333 |
|   4 |        202209 | mean_row_entropy_bits | higher             |  1.55974   |             1.56928   |        1.56964   |     1.56864  |       0.75     |
|   4 |        202211 | mean_row_entropy_bits | higher             |  1.59918   |             1.56928   |        1.56964   |     1.56864  |       0.25     |
|   5 |        202205 | composition_l1_change | higher             |  0.0470701 |             0.0936108 |        0.0828654 |     0.112415 |       1        |
|   5 |        202206 | composition_l1_change | higher             |  0.144633  |             0.0936108 |        0.0828654 |     0.112415 |       0.166667 |
|   5 |        202209 | composition_l1_change | higher             |  0.123227  |             0.0936108 |        0.0828654 |     0.112415 |       0.416667 |
|   5 |        202211 | composition_l1_change | higher             |  0.134731  |             0.0936108 |        0.0828654 |     0.112415 |       0.25     |
|   5 |        202205 | self_transition_rate  | lower              |  0.509626  |             0.499893  |        0.500434  |     0.498947 |       0.75     |
|   5 |        202206 | self_transition_rate  | lower              |  0.497295  |             0.499893  |        0.500434  |     0.498947 |       0.416667 |
|   5 |        202209 | self_transition_rate  | lower              |  0.516877  |             0.499893  |        0.500434  |     0.498947 |       1        |
|   5 |        202211 | self_transition_rate  | lower              |  0.471991  |             0.499893  |        0.500434  |     0.498947 |       0.166667 |
|   5 |        202205 | mean_row_entropy_bits | higher             |  1.77838   |             1.78417   |        1.78828   |     1.77697  |       0.583333 |
|   5 |        202206 | mean_row_entropy_bits | higher             |  1.75656   |             1.78417   |        1.78828   |     1.77697  |       0.916667 |
|   5 |        202209 | mean_row_entropy_bits | higher             |  1.76115   |             1.78417   |        1.78828   |     1.77697  |       0.833333 |
|   5 |        202211 | mean_row_entropy_bits | higher             |  1.81179   |             1.78417   |        1.78828   |     1.77697  |       0.25     |
|   6 |        202205 | composition_l1_change | higher             |  0.0883222 |             0.103989  |        0.0916228 |     0.12563  |       0.666667 |
|   6 |        202206 | composition_l1_change | higher             |  0.14956   |             0.103989  |        0.0916228 |     0.12563  |       0.166667 |
|   6 |        202209 | composition_l1_change | higher             |  0.130125  |             0.103989  |        0.0916228 |     0.12563  |       0.333333 |
|   6 |        202211 | composition_l1_change | higher             |  0.134512  |             0.103989  |        0.0916228 |     0.12563  |       0.25     |
|   6 |        202205 | self_transition_rate  | lower              |  0.471167  |             0.469122  |        0.470762  |     0.466252 |       0.666667 |
|   6 |        202206 | self_transition_rate  | lower              |  0.468477  |             0.469122  |        0.470762  |     0.466252 |       0.5      |
|   6 |        202209 | self_transition_rate  | lower              |  0.483428  |             0.469122  |        0.470762  |     0.466252 |       0.833333 |
|   6 |        202211 | self_transition_rate  | lower              |  0.441937  |             0.469122  |        0.470762  |     0.466252 |       0.166667 |
|   6 |        202205 | mean_row_entropy_bits | higher             |  1.99567   |             1.9824    |        1.9801    |     1.98642  |       0.5      |
|   6 |        202206 | mean_row_entropy_bits | higher             |  1.93702   |             1.9824    |        1.9801    |     1.98642  |       0.916667 |
|   6 |        202209 | mean_row_entropy_bits | higher             |  2.00637   |             1.9824    |        1.9801    |     1.98642  |       0.333333 |
|   6 |        202211 | mean_row_entropy_bits | higher             |  2.0066    |             1.9824    |        1.9801    |     1.98642  |       0.25     |

## Largest Monthly State-Share Z-Scores

|   k |   month | state   |      share |   z_score_vs_months | is_event_month   |
|----:|--------:|:--------|-----------:|--------------------:|:-----------------|
|   5 |  202201 | C4      | 0.0246607  |             2.81659 | False            |
|   6 |  202209 | C0      | 0.226099   |             2.40126 | True             |
|   6 |  202201 | C5      | 0.214514   |             2.24476 | False            |
|   6 |  202212 | C1      | 0.285427   |             2.14785 | False            |
|   5 |  202209 | C1      | 0.293954   |             2.14262 | True             |
|   5 |  202212 | C0      | 0.310633   |             2.04512 | False            |
|   4 |  202209 | C1      | 0.263761   |             1.98769 | True             |
|   4 |  202212 | C2      | 0.304673   |             1.89387 | False            |
|   6 |  202206 | C2      | 0.548263   |             1.88221 | True             |
|   5 |  202206 | C2      | 0.554892   |             1.84618 | True             |
|   4 |  202206 | C3      | 0.588226   |             1.83777 | True             |
|   6 |  202206 | C4      | 0.00603773 |            -1.8022  | True             |
|   4 |  202206 | C0      | 0.0152355  |            -1.77668 | True             |
|   6 |  202211 | C1      | 0.274981   |             1.75432 | True             |
|   4 |  202201 | C0      | 0.0307018  |             1.70396 | False            |
|   4 |  202207 | C3      | 0.581231   |             1.59912 | False            |
|   4 |  202209 | C2      | 0.208813   |            -1.5896  | True             |
|   5 |  202207 | C2      | 0.546461   |             1.57687 | False            |
|   6 |  202207 | C2      | 0.537722   |             1.54464 | False            |
|   6 |  202201 | C4      | 0.0123279  |             1.53833 | False            |
|   6 |  202201 | C2      | 0.442782   |            -1.49578 | False            |
|   5 |  202211 | C0      | 0.294398   |             1.47234 | True             |
|   5 |  202206 | C1      | 0.156667   |            -1.46773 | True             |
|   4 |  202211 | C2      | 0.292797   |             1.46233 | True             |
|   6 |  202204 | C3      | 0.0269517  |             1.45917 | False            |
|   5 |  202210 | C3      | 0.0299701  |             1.45779 | False            |
|   4 |  202201 | C3      | 0.491966   |            -1.44629 | False            |
|   5 |  202201 | C2      | 0.452168   |            -1.43509 | False            |
|   5 |  202206 | C4      | 0.00949584 |            -1.43133 | True             |
|   4 |  202206 | C1      | 0.136833   |            -1.4306  | True             |

## Two-Step Return Null Tests

The two-step test checks whether wallets that leave a state at month t+1 return to their original month-t state at month t+2 more often than expected after shuffling the t+2 states among wallets that left. This tests the temporary-deviation interpretation directly.

|   k |   month_t |   month_t1 |   month_t2 |   left_original_state_count |   observed_two_step_return_rate |   null_mean |    null_std |   p_value_upper |   observed_minus_null |
|----:|----------:|-----------:|-----------:|----------------------------:|--------------------------------:|------------:|------------:|----------------:|----------------------:|
|   4 |    202201 |     202202 |     202203 |                      219334 |                        0.356196 |    0.307522 | 0.000919254 |      0.00199601 |            0.0486748  |
|   4 |    202202 |     202203 |     202204 |                      219420 |                        0.376889 |    0.341635 | 0.000891363 |      0.00199601 |            0.0352537  |
|   4 |    202203 |     202204 |     202205 |                      227527 |                        0.348882 |    0.325248 | 0.000932195 |      0.00199601 |            0.0236337  |
|   4 |    202204 |     202205 |     202206 |                      195043 |                        0.380501 |    0.343307 | 0.000991149 |      0.00199601 |            0.0371939  |
|   4 |    202205 |     202206 |     202207 |                      204878 |                        0.351609 |    0.313155 | 0.000953628 |      0.00199601 |            0.0384544  |
|   4 |    202206 |     202207 |     202208 |                      195760 |                        0.36134  |    0.332126 | 0.000984026 |      0.00199601 |            0.0292148  |
|   4 |    202207 |     202208 |     202209 |                      260261 |                        0.308433 |    0.3115   | 0.000848804 |      1          |           -0.00306688 |
|   4 |    202208 |     202209 |     202210 |                      244175 |                        0.388819 |    0.333527 | 0.000885413 |      0.00199601 |            0.0552924  |
|   4 |    202209 |     202210 |     202211 |                      267378 |                        0.340914 |    0.313187 | 0.000808886 |      0.00199601 |            0.0277274  |
|   4 |    202210 |     202211 |     202212 |                      269556 |                        0.331067 |    0.315769 | 0.000839306 |      0.00199601 |            0.0152978  |
|   5 |    202201 |     202202 |     202203 |                      224334 |                        0.340827 |    0.283737 | 0.000907963 |      0.00199601 |            0.0570899  |
|   5 |    202202 |     202203 |     202204 |                      224856 |                        0.359817 |    0.312349 | 0.000901125 |      0.00199601 |            0.0474684  |
|   5 |    202203 |     202204 |     202205 |                      232778 |                        0.340496 |    0.302276 | 0.000908685 |      0.00199601 |            0.0382205  |
|   5 |    202204 |     202205 |     202206 |                      200447 |                        0.363388 |    0.315221 | 0.000937656 |      0.00199601 |            0.0481669  |
|   5 |    202205 |     202206 |     202207 |                      210289 |                        0.342809 |    0.29305  | 0.000971196 |      0.00199601 |            0.0497589  |
|   5 |    202206 |     202207 |     202208 |                      201369 |                        0.350511 |    0.30964  | 0.000976818 |      0.00199601 |            0.0408703  |
|   5 |    202207 |     202208 |     202209 |                      265949 |                        0.299471 |    0.293056 | 0.000844323 |      0.00199601 |            0.0064154  |
|   5 |    202208 |     202209 |     202210 |                      246010 |                        0.376867 |    0.311949 | 0.000850353 |      0.00199601 |            0.064918   |
|   5 |    202209 |     202210 |     202211 |                      273867 |                        0.325932 |    0.294103 | 0.000853088 |      0.00199601 |            0.0318289  |
|   5 |    202210 |     202211 |     202212 |                      272261 |                        0.32106  |    0.298691 | 0.000831513 |      0.00199601 |            0.0223681  |
|   6 |    202201 |     202202 |     202203 |                      233294 |                        0.312498 |    0.244018 | 0.0008954   |      0.00199601 |            0.0684805  |
|   6 |    202202 |     202203 |     202204 |                      238579 |                        0.332992 |    0.270141 | 0.000808321 |      0.00199601 |            0.0628511  |
|   6 |    202203 |     202204 |     202205 |                      253344 |                        0.308328 |    0.250481 | 0.000791337 |      0.00199601 |            0.0578468  |
|   6 |    202204 |     202205 |     202206 |                      217832 |                        0.33233  |    0.270085 | 0.000888508 |      0.00199601 |            0.0622448  |
|   6 |    202205 |     202206 |     202207 |                      224032 |                        0.303707 |    0.241041 | 0.000821073 |      0.00199601 |            0.0626658  |
|   6 |    202206 |     202207 |     202208 |                      214113 |                        0.318416 |    0.262409 | 0.000816536 |      0.00199601 |            0.0560074  |
|   6 |    202207 |     202208 |     202209 |                      282896 |                        0.270085 |    0.242474 | 0.000773192 |      0.00199601 |            0.0276107  |
|   6 |    202208 |     202209 |     202210 |                      265736 |                        0.350671 |    0.264372 | 0.000801164 |      0.00199601 |            0.0862989  |
|   6 |    202209 |     202210 |     202211 |                      295198 |                        0.293193 |    0.240654 | 0.000740229 |      0.00199601 |            0.0525392  |
|   6 |    202210 |     202211 |     202212 |                      289505 |                        0.295539 |    0.249037 | 0.000731036 |      0.00199601 |            0.0465018  |

## Strongest Off-Diagonal Transition Pathways

|   k |   from_state |   to_state |   probability |
|----:|-------------:|-----------:|--------------:|
|   4 |            2 |          3 |    0.399031   |
|   4 |            1 |          3 |    0.355804   |
|   4 |            0 |          1 |    0.280763   |
|   4 |            3 |          2 |    0.240077   |
|   4 |            0 |          3 |    0.195946   |
|   4 |            1 |          2 |    0.177145   |
|   4 |            3 |          1 |    0.16431    |
|   4 |            2 |          1 |    0.122303   |
|   4 |            0 |          2 |    0.0742599  |
|   4 |            1 |          0 |    0.0318186  |
|   4 |            3 |          0 |    0.0132106  |
|   4 |            2 |          0 |    0.00638639 |
|   5 |            0 |          2 |    0.368578   |
|   5 |            1 |          2 |    0.338618   |
|   5 |            4 |          1 |    0.28226    |
|   5 |            3 |          1 |    0.278064   |
|   5 |            2 |          0 |    0.236157   |
|   5 |            4 |          0 |    0.186757   |
|   5 |            3 |          2 |    0.186691   |
|   5 |            2 |          1 |    0.185652   |
|   5 |            1 |          0 |    0.169919   |
|   5 |            4 |          2 |    0.162201   |
|   5 |            0 |          1 |    0.130129   |
|   5 |            4 |          3 |    0.0845526  |
|   6 |            1 |          2 |    0.362485   |
|   6 |            5 |          2 |    0.340066   |
|   6 |            0 |          2 |    0.320949   |
|   6 |            4 |          5 |    0.279845   |
|   6 |            3 |          5 |    0.274665   |
|   6 |            2 |          1 |    0.21562    |
|   6 |            3 |          2 |    0.167219   |
|   6 |            0 |          5 |    0.149118   |
|   6 |            0 |          1 |    0.147331   |
|   6 |            4 |          1 |    0.142177   |
|   6 |            4 |          2 |    0.141951   |
|   6 |            5 |          0 |    0.130853   |

## Interpretation

Across K4, K5, and K6, monthly wallet behaviour is neither fixed nor random. The transition matrices show moderate persistence, while the two-step return tests show that many wallets temporarily leave a behavioural state and then return more often than expected under shuffled future states.

External events should be treated as candidate explanations, not causal conclusions. For example, May and June 2022 correspond to broad crypto-market stress around Terra and Celsius, September 2022 corresponds to the Ethereum Merge, and November 2022 corresponds to the FTX crisis. The correct paper wording is that these months provide plausible contextual windows for observed state-share and persistence changes, but causal attribution would require an explicit event-study design or control series.