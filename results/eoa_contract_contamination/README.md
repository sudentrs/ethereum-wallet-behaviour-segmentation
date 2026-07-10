# EOA/Contract Contamination Check

This folder contains the first Gate 1 contamination sample requested for publication preparation.

## Method

- Input labels: `../dataverse_files/wallet_kmeans6_expanded_daily_features.csv`
- Sampling: 1,000 wallet addresses per cluster
- Address classification: Ethereum JSON-RPC `eth_getCode`
- Block tag: `latest`
- RPC provider: Alchemy Ethereum Mainnet
- Cache: local ignored file under `data/interim/eoa_contract_cache.csv`

An address is classified as:

- `EOA` if `eth_getCode(address)` returns `0x`
- `contract` if `eth_getCode(address)` returns non-empty bytecode

## Result

| Cluster | Sampled addresses | EOA count | Contract count | Contract share |
|---:|---:|---:|---:|---:|
| C0 | 1,000 | 920 | 80 | 0.080 |
| C1 | 1,000 | 857 | 143 | 0.143 |
| C2 | 1,000 | 898 | 102 | 0.102 |
| C3 | 1,000 | 528 | 472 | 0.472 |
| C4 | 1,000 | 960 | 40 | 0.040 |
| C5 | 1,000 | 899 | 101 | 0.101 |

## Interpretation

C3 is materially contract-contaminated in this sample.

C1 is close to the supervisor's working threshold of 15%.

This means the project should not proceed directly with the old role interpretation until Gate 1 is resolved.

Recommended next step:

Run a larger or full-cluster EOA/contract classification for C3 and C1, then decide whether to rerun clustering on EOA-only data.

## Caution

This run used the `latest` block tag.

For a paper submission, a historical block near the end of the 2022 observation window would be cleaner.

