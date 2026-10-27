# Historical cohort rebuild v1

## Status and definition

This is a versioned rebuild, not a modification of the archived annual cohort.
The candidate population is exactly the 2,738,243 addresses in the original
wallet feature table. Inclusion requires empty code at all twelve pinned
2022 month-end blocks. This means snapshot-code-free, not proven continuous
EOA status. Missing evidence is unresolved. A single nonempty month-end
observation rejects this particular all-empty definition.

The original 2,443,868 retained addresses are NOT automatically accepted.
They also need historical checks. Rechecking only excluded addresses would
address false exclusions but would not validate the retained population.

Positive transaction-origination evidence is stored separately. It does not
substitute for twelve month-end observations or establish year-long status.
The earlier 33-address evidence inventory and the probability audit are both
reused without treating their combined address list as a corrected cohort.

## Offline preparation

From the repository root:

```powershell
python scripts/build_historical_wallet_cohort.py
```

This validates raw/label file hashes against the previously validated audit
frame, creates a local SQLite registry, imports pinned code observations,
and records verified origination evidence. It makes zero RPC calls.

Local registry: data/interim/historical_wallet_cohort_v1/registry.sqlite.
Small shareable outputs: results_v3/historical_wallet_cohort_v1/.
The verified_snapshot_subset.csv is only the observed qualifying subset,
not the final population and not a representative clustering input.

## Bounded historical execution

After configuring a rotated archive-capable Ethereum RPC in a local ignored
file containing ETH_RPC_URL:

```powershell
python scripts/build_historical_wallet_cohort.py --execute --env-file .env --max-code-queries 1000
```

The numeric limit is a bound on successful new address/block observations
per invocation, not a provider credit limit. Retries may repeat requests;
chain and block-hash validation calls are additional. No provider cost is
estimated here. Agree on the account's budget before a large run.

The runner checks latest month ends first, prioritizes previously excluded
addresses, skips cached observations, and stops querying an address once
the all-empty criterion is disproven. Selection order is for computation,
not a probability sample; do not extrapolate interim queue results.

At most 32,858,916 observations are needed before caching and early exclusion
(2,738,243 x 12). Actual remaining upper bound is in cohort_status.json.
The same command resumes the registry. Do not change the raw population,
snapshot definition or pinned blocks within a version directory.

## Completion and downstream reruns

The builder will NOT write cohort_members.csv or COHORT_READY.json until
every original address is either excluded by positive code evidence or
included by twelve empty observations. The final manifest has a SHA256 and
the explicit snapshot definition. Lack of COHORT_READY.json means a full
historical-cohort comparison must not be presented as completed.

Once ready, the downstream sequence is:

1. Select raw feature rows using the completed cohort manifest. Keep an
   unchanged-scaled-representation sensitivity run separate from a new
   representation/scaler analysis; the token-denomination issue is not
   repaired by changing the cohort.
2. Fit reproducible K4/K5/K6 baseline and corrected-cohort models with saved
   estimators, versions, settings and seeds. Do not pretend the archived
   K4/K6 estimators were exactly recovered; prior reconstruction was imperfect.
3. Compare shared-wallet ARI/NMI/Hungarian agreement, size/profile changes,
   seed variability and full additions/removals. Do not select K5 by default.
4. Rebuild monthly assignments and repeat transition, persistence and two-step
   return tests using the new membership; distinguish annual and monthly IDs.
5. Repeat monthly network null tests and temporal signal analyses. Preserve
   null-model definitions, correction for multiple tests, and holdout rules.
6. Regenerate figures/tables and only then update manuscript population counts
   and conclusions. Archive the original outputs for comparison.

No paper claims or old cluster label files are changed by this builder.

## Alternative year-end definition and bounded benchmark

A single-year-end cohort is a different population definition, not an
optimization that proves twelve-month status. Its benchmark is implemented
in scripts/benchmark_year_end_rpc.py. Results and caveats are in
results_v3/year_end_2022_rpc_benchmark/README.md. A full year-end scan/export
has not been run. The most reliable tested setting was batch 20 with one
worker; concurrent settings had unresolved failures. Provider quota still
needs checking before a full run.
