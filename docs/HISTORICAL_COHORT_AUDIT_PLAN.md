# Historical cohort correction: decision and audit protocol

## Cohort definition

The existing cohort is a present-day code-filtered address population, not a verified year-long 2022 EOA population. Preserve it as the baseline until correction is evaluated.

For an operational historical comparison, use: addresses in the 2022 ERC-20 dataset with empty code at all twelve observed 2022 month-end blocks. Call these "month-end code-free addresses", not verified always-EOA addresses. Missing RPC responses remain unresolved and never count as empty code. Snapshots can miss within-month changes.

Separately record positive 2022 top-level Ethereum transaction origination. This establishes EOA activity at that transaction time in 2022, not continuous year-long status. ERC-20 transfer senders are not transaction originators. Do not silently combine these definitions into one supposedly verified cohort. Define any union/intersection sensitivity cohort explicitly.

## What the 33-address pilot establishes

Only limited annual sensitivity to those particular 33 additions under the original frozen feature representation. It does not establish the exclusion error rate, resolve token-denomination issues, or measure monthly/network effects. K5 reconstructed archived labels exactly; K4/K6 did not. Resolve estimator provenance or declare new reproducible baselines before attributing changes to cohort correction.

## Offline probability-sample design

Run from the repository root:

```powershell
python scripts/prepare_historical_exclusion_audit.py
```

Inputs are the original raw wallet feature table and all three annual cohort label files. Require identical retained wallet sets. The exclusion population is raw addresses minus that retained set; no alternate data are substituted.

Sample 200 addresses without replacement in each of three predeclared activity strata: total_tx <= 2, 3-10, and >10. Census any smaller stratum. Sort addresses and use fixed seed 20221020. Record stratum population/sample sizes, inclusion probabilities and weights. Draw from the entire exclusion population, including previously audited addresses; reuse existing evidence only AFTER drawing. Do not add the known 33 to the random sample by hand.

This targets false exclusion only. It does not establish that all retained addresses were historically code-free; retained-population checks must be evaluated separately.

### Prepared sample on this checkout

The validated frame contains 2,738,243 raw addresses, 2,443,868 retained addresses and 294,375 excluded addresses. No excluded addresses fall in the <=2 band. The 3-10 band contains 22,036 addresses and the >10 band contains 272,339. Therefore the prepared sample has 400 addresses (200 per nonempty band), not 600. Its maximum twelve-month code-check budget is 4,800 address/block queries, excluding extra evidence requests. None of the 400 overlaps a cached positive origination result; this is missing evidence, not evidence of zero error. The broad >10 band does not oversample the extreme activity tail: inspect activity coverage before choosing any separately labelled tail stress test. Such a stress test must not be pooled unweighted into this probability sample.

## Evidence collection next

1. Review cached evidence for sampled addresses. Keep prior non-probability/stratified audit evidence as a separate inventory, not an unweighted population estimate.
2. Seek positive transaction-origination evidence using actual Ethereum transactions, not token-transfer from fields. Verify transaction sender, block/date and inclusion; cache hashes and provider provenance. No indexed match is unresolved, not a negative result.
3. For all sampled addresses, complete twelve historical month-end code checks using pinned blocks and cached results. Origination-positive addresses still need these checks for the snapshot-defined estimand. At most 7,200 code calls for 600 addresses, minus cached observations; block lookup and origination calls are additional. Do not scan 2.4 million wallets monthly at this stage.
4. Keep code-state results and origination results as distinct outcomes, including unresolved flags. Review historical changes and current delegation separately.

## Estimation after evidence completion

For each fully observed binary outcome, estimate the population proportion as sum_h (N_h/N)*p_h. Use design-based variance sum_h (N_h/N)^2*(1-n_h/N_h)*s_h^2/n_h. Report stratum counts and uncertainty; zero observed events do not imply zero population risk. Use an appropriate finite-population interval rather than a zero-width plug-in interval for zero/all-event strata. Predeclare the interval method before reviewing new outcomes.

With unresolved outcomes, do not report the resolved subset as representative. Report weighted identification bounds: lower = weighted confirmed-positive count/N; upper = weighted (confirmed-positive + unresolved) count/N, with sampling uncertainty separately. These are different from confidence intervals. A failed origination search cannot resolve a negative outcome, so it alone cannot produce a false-exclusion point estimate.

No universal acceptable error threshold is assumed. Assess address share AND activity concentration, with high-activity cases reviewed separately. If correction is warranted, build versioned historical cohorts and rerun annual, temporal and network analyses. If extensive data remain unavailable, retain accurate baseline terminology and disclose uncertainty rather than claiming historical EOA verification.

## Artifacts and non-changes

Design outputs: results_v3/historical_exclusion_audit_design/sample.csv, stratum_design.csv, design.json and previous_evidence_inventory.csv. This preparation makes zero RPC calls. It does not change archived labels, the main cohort or manuscript. No Git push is implied.

## Execution and completed audit

With ETH_RPC_URL set locally (never commit credentials):

```powershell
python scripts/run_historical_exclusion_sample.py --execute
python src/validation/audit_excluded_transaction_origination.py --input-csv results_v3/historical_exclusion_audit_design/sample.csv --output-dir data/interim/historical_exclusion_probability_origination --blocks-csv data/interim/historical_exclusion_probability_audit/month_end_blocks.csv
python scripts/summarize_historical_exclusion_sample.py
python -m unittest discover -s tests -p test_historical_exclusion_audit.py -v
```

Omit --execute for an offline code-audit progress report. Both network stages cache observations; rerunning the same commands resumes the same sample. Never switch samples in the same output directory. The origination search currently uses the provider's external-transfer index to locate positive evidence; it is not an exhaustive all-transaction search and nonmatches remain unresolved.

The completed probability audit has 4,800/4,800 code observations: 69/400 addresses were code-free at all twelve month ends. The weighted snapshot-defined estimate is 19.1631% of the excluded population; a conservative 95% exact finite-population interval is 12.7378%-27.0227%. Separately, 67/400 have verified 2022 top-level origination evidence, all among those 69. The remaining 333 origination searches are unresolved, not confirmed non-originators. These findings are distinct from the earlier non-probability inventory of 33 addresses.

The interval method is hypergeometric tail inversion within strata, with Bonferroni simultaneous coverage across strata and lower/upper bounding outcomes. It remains nonzero-width for zero-event samples. See results_v3/historical_exclusion_audit_results/README.md, estimates.json, stratum_estimates.csv and address_evidence.csv. Input evidence hashes are recorded in estimates.json. Full transaction/receipt/header records remain in the ignored local origination_evidence cache.
