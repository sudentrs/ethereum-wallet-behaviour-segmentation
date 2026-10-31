# Complete year-end 2022 wallet cohort

All 2,738,243 original addresses were checked at Ethereum Mainnet block
16,308,189, the last block of 2022. The list contains 2,508,997 addresses
with empty code at this block; 229,246 addresses had nonempty code.
This is a year-end snapshot definition, not proof of continuous EOA status
throughout 2022. Clustering and manuscript results have not been rerun.

`cohort_members.csv.gz` is a losslessly compressed CSV with a `wallet` column.
Wallets are lowercase, 40 hexadecimal characters without the `0x` prefix.
Preserve them as strings to retain leading zeros:

```python
import pandas as pd
wallets = pd.read_csv("cohort_members.csv.gz", dtype={"wallet": str})
```

Alternatively extract the gzip file with 7-Zip or `gzip -dk cohort_members.csv.gz`.
`YEAR_END_READY.json` records the block identity, wallet count, compressed-file
SHA256, and the SHA256 of the original uncompressed CSV. The decompressed
content and wallet count were verified before publication.
