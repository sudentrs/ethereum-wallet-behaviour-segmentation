# Historical audit of sampled excluded addresses

Audit date: 2026-10-20. Existing cohort and cluster labels were not changed.

## Scope and findings

Two disjoint samples contain 120 addresses originally excluded by the latest-code filter. Every address has 12 historical month-end code observations in 2022. Current code was subsequently inspected at Ethereum Mainnet block 26235924.

| Historical group | Current code | Addresses | Verified 2022 top-level senders |
|---|---|---:|---:|
| Empty at all month ends | Exact EIP-7702 delegation indicator | 31 | 31 |
| Empty at all month ends | Empty | 2 | 2 |
| Code at some month ends | Other nonempty code | 50 | No indexed match found |
| Code at every month end | Other nonempty code | 37 | No indexed match found |

All 33 historically code-free addresses have positive evidence of EOA transaction origination in 2022. For each address, an external-transfer index search supplied a candidate transaction hash. The Ethereum transaction was fetched separately and checked for an exact outer `from` match, 2022 block/time range, nonzero signature fields, consistent block hash and receipt, and inclusion of the transaction hash in the block. All 33 receipts indicate success. All 33 addresses had empty code both immediately before the transaction's block and after that block. This establishes transaction origination at an observed historical time, not continuous EOA status at every instant in 2022.

The 31 current delegation indicators have exactly 23 bytes and prefix `0xef0100`. The original cache recorded a 23-byte code length for all 33 addresses, including the two now empty. The original raw code was not preserved, so the two earlier code values cannot be identified from length alone. Clearing delegation is a possible explanation, not a verified event history.

The 33 addresses have 1,646 combined wallet-level ERC-20 transfer counts in the existing feature table. This is neither an economically meaningful pooled token volume nor necessarily 1,646 unique Ethereum transactions.

## Interpretation and limits

The filter wrongly excluded at least these 33 demonstrated historical transaction-originating accounts from an EOA behaviour cohort on the basis of present-day nonempty code. EIP-7702 explains the current code for 31. The existing retained sample of 4,692 addresses has no code-bearing observations at the 12 sampled month ends, which is reassuring but not a population-wide or continuous-history guarantee.

For the other 87 addresses, an empty indexed external-transfer search is NOT proof that no top-level transaction exists. They remain without positive origination evidence from this search. Their observed code status supports historical contract treatment at the relevant snapshots, but deployment blocks and transfer-time states were not reconstructed.

No full-population exclusion rate or clustering effect has been estimated. Do not extrapolate the unweighted 33/120 count to all 294,375 excluded addresses. Keep the baseline cohort; next assess the broader scope of delegation-related exclusions and sensitivity to independently supported restorations.

## Local artifacts

Under `data/interim/excluded_code_type_audit/` (ignored local outputs):

- `excluded_address_audit.csv`: current code classification and historical groups.
- `historical_origination_audit.csv`: all 120 addresses with positive-evidence or unresolved status.
- `origination_evidence/<address>.json`: index-derived candidate and fetched transaction, receipt, block header, and code states for positive matches; negative index searches have status only.
- `origination_summary.csv`: aggregate evidence counts.
- `cached_code_length_crosscheck.csv`: comparison with the original cached classification.
- `excluded_activity.csv`: local activity features for the audited addresses.
- `metadata.json`: pinned current-code block and audit time.

Evidence is supplied by the configured Alchemy Mainnet endpoint. We did not independently recover transaction signatures or cross-check another node provider. Nonzero signature fields are a consistency check, not independent cryptographic verification.

References: [EIP-7702](https://eips.ethereum.org/EIPS/eip-7702), [EIP-3607](https://eips.ethereum.org/EIPS/eip-3607).
