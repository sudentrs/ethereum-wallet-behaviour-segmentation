# Year-end 2022 RPC benchmark

Pinned block: 16,308,189, the last Ethereum block before 2023 UTC. This
benchmark concerns year-end code status, NOT the twelve-snapshot definition
or continuous EOA identity. No full-population scan was started.

| Batch | Workers | Selected | Successful | Unresolved | Seconds | Successful checks/s |
|---|---:|---:|---:|---:|---:|---:|
| 20 | 1 | 400 | 400 | 0 | 7.34 | 54.51 |
| 50 | 2 | 400 | 350 | 50 | 20.75 | 16.87 |
| 20 | 2 | 400 | 380 | 20 | 11.24 | 33.80 |

The final row is recorded in the sibling directory
results_v3/year_end_2022_rpc_benchmark_small_parallel/. The 100:2 profile was
not run: escalation stopped after the 50:2 profile had unresolved failures.
No provider error cause was established; do not assume that all errors were
rate limits. Failed batches were retried at most three times. Those retries
use provider resources and are included in attempted-check counts.

The two invocations selected at most 1,200 address tasks in total; the
fallback could select an earlier unresolved address. 1,130 successful new
year-end observations were persisted. After both runs, 2,530 year-end
observations were cached and 2,735,713 addresses still lacked that snapshot.

At the best error-free SHORT-run rate, remaining work projects to about
13.94 hours. This is a projection, not a promised duration: provider quota,
longer-run throttling, code-response sizes, retries, local I/O and network
conditions can alter throughput. Benchmark timing excludes initial chain
and pinned-block validation, and each configuration used different addresses.
This is not a controlled speedup or error-rate experiment.

Recommendation: use batch 20, one worker as the initial full-run setting,
with pacing/backoff and durable progress reporting. Verify the provider's
remaining allowance before approving millions of calls. Larger or concurrent
requests did not improve reliable throughput in this test.

Raw code sizes were written to the shared historical evidence registry. No
cohort was silently redefined or exported, and no clustering results or paper
claims were updated. Run scripts/build_historical_wallet_cohort.py offline to
refresh the separate twelve-snapshot progress report from shared evidence.
