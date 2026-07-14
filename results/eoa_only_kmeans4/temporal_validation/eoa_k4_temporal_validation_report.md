# EOA-Only K4 Temporal Validation

## Purpose

This analysis checks whether the EOA-Only K4 roles behave like stable behavioural states over time. Each wallet-month is assigned to the nearest full-year prototype in robust-scaled feature space, then month-to-month transitions are summarized.

## Months

202201, 202202, 202203, 202204, 202205, 202206, 202207, 202208, 202209, 202210, 202211, 202212

## Monthly State Summary

|   month |   daily_rows_read |   daily_rows_matching_cluster_wallets |   active_wallets_assigned |   state_entropy_bits |   matches_full_year_cluster_ratio |   median_assignment_margin |   state_C0_share |   state_C1_share |   state_C2_share |   state_C3_share |
|--------:|------------------:|--------------------------------------:|--------------------------:|---------------------:|----------------------------------:|---------------------------:|-----------------:|-----------------:|-----------------:|-----------------:|
|  202201 |           6684799 |                               2982981 |                    830309 |              1.64098 |                          0.304744 |                    1.5598  |        0.0307018 |         0.215005 |         0.262326 |         0.491966 |
|  202202 |           5695147 |                               2657655 |                    846549 |              1.53517 |                          0.255304 |                    1.85628 |        0.0229709 |         0.171117 |         0.252971 |         0.552941 |
|  202203 |           7273463 |                               3300538 |                    984649 |              1.6     |                          0.288495 |                    1.71415 |        0.027358  |         0.190333 |         0.267925 |         0.514384 |
|  202204 |           5991429 |                               3134539 |                    967399 |              1.57087 |                          0.266544 |                    1.84467 |        0.0256781 |         0.19239  |         0.243986 |         0.537946 |
|  202205 |           6436520 |                               3237974 |                   1010310 |              1.54539 |                          0.265561 |                    1.92464 |        0.0208936 |         0.203341 |         0.227637 |         0.548129 |
|  202206 |           5074326 |                               2622192 |                    895866 |              1.44007 |                          0.21649  |                    2.27607 |        0.0152355 |         0.136833 |         0.259705 |         0.588226 |
|  202207 |           6214191 |                               3220118 |                   1036233 |              1.473   |                          0.230377 |                    2.00659 |        0.0185335 |         0.150947 |         0.249289 |         0.581231 |
|  202208 |           6228351 |                               3403015 |                   1012028 |              1.57793 |                          0.293714 |                    1.87392 |        0.024528  |         0.212165 |         0.230665 |         0.532642 |
|  202209 |           8605533 |                               4125144 |                   1196575 |              1.58975 |                          0.314008 |                    1.51543 |        0.0202678 |         0.263761 |         0.208813 |         0.507158 |
|  202210 |           7267599 |                               3589331 |                   1064560 |              1.61213 |                          0.320979 |                    1.80291 |        0.0286325 |         0.226034 |         0.229892 |         0.515441 |
|  202211 |           8714425 |                               4037251 |                   1158839 |              1.56882 |                          0.299904 |                    1.68972 |        0.0208925 |         0.174045 |         0.292797 |         0.512265 |
|  202212 |           9333709 |                               3543004 |                    988214 |              1.53038 |                          0.3095   |                    1.79704 |        0.0218708 |         0.143479 |         0.304673 |         0.529977 |

## Overall Transition Probability Matrix

|   from_state |          0 |        1 |         2 |        3 |
|-------------:|-----------:|---------:|----------:|---------:|
|            0 | 0.449031   | 0.280763 | 0.0742599 | 0.195946 |
|            1 | 0.0318186  | 0.435233 | 0.177145  | 0.355804 |
|            2 | 0.00638639 | 0.122303 | 0.47228   | 0.399031 |
|            3 | 0.0132106  | 0.16431  | 0.240077  | 0.582402 |

## State Stability

|   from_state |   self_transition_probability |   transition_entropy_bits | top_destinations             |
|-------------:|------------------------------:|--------------------------:|:-----------------------------|
|            0 |                      0.449031 |                   1.77253 | C0=0.449; C1=0.281; C3=0.196 |
|            1 |                      0.435233 |                   1.65338 | C1=0.435; C3=0.356; C2=0.177 |
|            2 |                      0.47228  |                   1.45735 | C2=0.472; C3=0.399; C1=0.122 |
|            3 |                      0.582402 |                   1.45898 | C3=0.582; C2=0.240; C1=0.164 |

## Monthly Transition Summary

|   from_month |   to_month |   wallets_in_both_months |   self_transition_count |   self_transition_rate |   mean_row_entropy_bits |
|-------------:|-----------:|-------------------------:|------------------------:|-----------------------:|------------------------:|
|       202201 |     202202 |                   577956 |                  289576 |               0.501035 |                 1.58362 |
|       202202 |     202203 |                   622405 |                  321118 |               0.515931 |                 1.57203 |
|       202203 |     202204 |                   673304 |                  348588 |               0.517728 |                 1.55087 |
|       202204 |     202205 |                   655506 |                  344931 |               0.526206 |                 1.5637  |
|       202205 |     202206 |                   598239 |                  306578 |               0.512467 |                 1.55195 |
|       202206 |     202207 |                   599622 |                  319277 |               0.532464 |                 1.56066 |
|       202207 |     202208 |                   651204 |                  321959 |               0.494406 |                 1.61172 |
|       202208 |     202209 |                   741066 |                  389774 |               0.525964 |                 1.55974 |
|       202209 |     202210 |                   756597 |                  391320 |               0.517211 |                 1.54329 |
|       202210 |     202211 |                   740868 |                  357072 |               0.481964 |                 1.59918 |
|       202211 |     202212 |                   734779 |                  385338 |               0.524427 |                 1.56529 |

## Two-Step Return Analysis

|   month_t |   month_t1 |   month_t2 |   wallets_present_all_three |   left_original_state_count |   returned_to_original_state_count |   two_step_return_rate_after_leaving |   same_state_all_three_rate |
|----------:|-----------:|-----------:|----------------------------:|----------------------------:|-----------------------------------:|-------------------------------------:|----------------------------:|
|    202201 |     202202 |     202203 |                      440577 |                      219334 |                              78126 |                             0.356196 |                    0.295356 |
|    202202 |     202203 |     202204 |                      449680 |                      219420 |                              82697 |                             0.376889 |                    0.306596 |
|    202203 |     202204 |     202205 |                      474745 |                      227527 |                              79380 |                             0.348882 |                    0.309969 |
|    202204 |     202205 |     202206 |                      408091 |                      195043 |                              74214 |                             0.380501 |                    0.306856 |
|    202205 |     202206 |     202207 |                      418840 |                      204878 |                              72037 |                             0.351609 |                    0.311221 |
|    202206 |     202207 |     202208 |                      412104 |                      195760 |                              70736 |                             0.36134  |                    0.298597 |
|    202207 |     202208 |     202209 |                      496130 |                      260261 |                              80273 |                             0.308433 |                    0.273235 |
|    202208 |     202209 |     202210 |                      519429 |                      244175 |                              94940 |                             0.388819 |                    0.330342 |
|    202209 |     202210 |     202211 |                      553328 |                      267378 |                              91153 |                             0.340914 |                    0.267919 |
|    202210 |     202211 |     202212 |                      510155 |                      269556 |                              89241 |                             0.331067 |                    0.294418 |

## Interpretation

The diagonal of the transition matrix measures persistence: wallets that remain in the same behavioural state from one month to the next. High diagonal values support the interpretation of clusters as recurring behavioural states rather than one-time labels.

Off-diagonal values show common movement paths between roles. These transitions are useful because wallet behaviour is expected to change over time; the important question is whether those changes are structured.

The two-step return analysis checks the pattern discussed during project review: a wallet can leave its original state for one month and then return to that original state in the following month. A non-trivial return rate supports the idea that some apparent movement is temporary deviation rather than permanent role change.