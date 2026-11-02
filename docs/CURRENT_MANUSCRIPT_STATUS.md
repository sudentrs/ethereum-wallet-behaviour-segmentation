# Current Manuscript Status

`overleaf/main.tex` is the current manuscript.
It is based only on the year-end code-free cohort and the count/activity/direction representation documented in `results_v3/year_end_2022_count_cohort/`.

## Claims Supported by Tracked Results

- The year-end code-free cohort contains 2,508,997 addresses from an initial 2,738,243-address universe.
- Annual K3 is highly stable across the three fitted seeds, whereas annual K4--K6 are less stable.
- K3 labels are sensitive to removal of persistence/concentration features; they are a representation-specific behavioural summary, not ground truth.
- In all twelve monthly snapshots, annual K3 same-state transfer concentration exceeds a 999-permutation shuffled-label null within the retained cohort subgraph.
- A separately trained frozen monthly K3 model has above-chance held-out persistence and above-null two-step return for active wallet-months.

## Claims Deliberately Excluded

- Permanent EOA identity or ownership claims.
- Economic claims based on pooled ERC-20 token amounts.
- Causal claims about why same-state wallets interact, or claims about the full ERC-20 network beyond the retained cohort subgraph.
- A claim that K3 is Ethereum's unique or natural number of wallet types.

## Before Submission

1. Audit historical address code at transfer-time or defined monthly block boundaries if the paper needs a stronger EOA statement.
2. Rebuild a token-aware economic representation before making any value-flow interpretation.
3. Tag a commit only after reproducing the compact tables and compiling the manuscript from a clean checkout.

`docs/REVIEW_REVISION_STATUS.md` records the older K4/K5/K6 review path and is retained only as project history.
