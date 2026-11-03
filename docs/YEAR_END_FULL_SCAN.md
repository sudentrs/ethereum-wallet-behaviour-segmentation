# Full year-end 2022 scan

Run from the repository root with an archive-capable Ethereum Mainnet RPC
configured as `ETH_RPC_URL` in the environment or the ignored `.env` file:

```powershell
python scripts/run_year_end_scan.py --execute
```

This checks all remaining original-population addresses at block 16,308,189.
It uses batches of 20 and one worker per configured RPC endpoint, with at most
four HTTP batch starts per second per endpoint. Add additional connections as
`ETH_RPC_URL_2`, `ETH_RPC_URL_3`, etc. in the ignored `.env` file. Environment
variables override corresponding file entries; identical URLs are deduplicated.
All connections are validated against Ethereum Mainnet and the pinned block
before scanning. The coordinator distributes nonoverlapping batches and is the
only SQLite writer. Each endpoint has independent pacing and recovery waits.
Status includes `rpc_workers`. Use `--rpc-count 1` to select only the first RPC.
Retries can consume additional provider allowance. The short benchmark projects
about 14 hours; sustained throughput and provider quota can change this.
Keep the terminal running and prevent the computer from sleeping.

Each successful batch commits to the shared registry. Ctrl+C stops the run;
the same command resumes, skipping recorded year-end observations. After three
failed attempts on a batch the scanner waits and retries the same batch.
There are five extra recovery rounds by default, with cooldowns of 15, 30,
60, 120 and 120 seconds. Persistent failure then stops the run, leaving the
batch unresolved. In-flight successful results from other workers are saved
before stopping. `--recovery-rounds 0` disables these extra rounds.
Do not run the historical builder or benchmark concurrently with this scanner.
A second instance of this scanner is rejected automatically.

For a bounded execution, add `--max-code-queries 1000`. Without `--execute`,
the script prints local status without making RPC calls:

```powershell
python scripts/run_year_end_scan.py
```

Status is saved about every 30 seconds to
`data/interim/year_end_2022_full_scan/status.json`. Once all addresses are
resolved, this directory receives `cohort_members.csv` (wallets without the
`0x` prefix) and `YEAR_END_READY.json` with the SHA256 digest and block identity.
Partial runs never export a completed cohort. This is a separate year-end
definition; it does not prove year-long EOA identity or complete the twelve
month-end rebuild. Existing clustering and manuscript outputs are unchanged.
