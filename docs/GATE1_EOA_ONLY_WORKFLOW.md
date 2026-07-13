# Gate 1 EOA-Only Workflow

Gate 1 is triggered when any behavioural cluster has more than 15% contract contamination.

The current sample check triggered Gate 1 because C3 had 47.2% contracts. The next defensible branch is therefore an EOA-only segmentation branch.

## Step 1: Build expanded features

```powershell
python src\features\build_full_kmeans6_expanded_features.py `
  --daily-file data\processed\wallet_daily_2022.csv `
  --cluster-file data\processed\wallet_kmeans_clusters.csv `
  --output data\processed\wallet_kmeans6_expanded_daily_features.csv `
  --chunksize 1000000
```

## Step 2: Run full EOA/contract classification

Use a historical block near the end of the 2022 observation window if possible. Use `latest` only for exploratory checks.

```powershell
python src\validation\eoa_contract_contamination_check.py `
  --labels-csv data\processed\wallet_kmeans6_expanded_daily_features.csv `
  --sample-per-cluster 0 `
  --block latest `
  --cache-csv data\interim\eoa_contract_cache.csv `
  --output-dir results\eoa_contract_contamination_full
```

This requires `ETH_RPC_URL` or `--rpc-url`.

## Step 3: Filter to EOA-only features

```powershell
python src\validation\filter_eoa_only_features.py `
  --features data\processed\wallet_kmeans6_expanded_daily_features.csv `
  --classifications results\eoa_contract_contamination_full\sampled_address_classifications.csv `
  --output data\processed\wallet_kmeans6_expanded_daily_features_eoa_only.csv
```

The script fails if classification coverage is incomplete. That is intentional.

## Step 4: Robust-scale EOA-only features

```powershell
python src\features\robust_scale_expanded_features.py `
  --input data\processed\wallet_kmeans6_expanded_daily_features_eoa_only.csv `
  --output data\processed\wallet_kmeans6_expanded_daily_features_eoa_only_robust_scaled.csv
```

## Step 5: Re-run KMeans6 on EOA-only wallets

```powershell
python src\clustering\run_eoa_only_kmeans.py `
  --features data\processed\wallet_kmeans6_expanded_daily_features_eoa_only_robust_scaled.csv `
  --out-dir results\eoa_only_kmeans6 `
  --k 6 `
  --random-state 492
```

## Step 6: Treat all downstream results as post-Gate-1

The old mixed-address KMeans6 result can remain as a pre-Gate-1 baseline. Paper claims should use the EOA-only branch if Gate 1 remains failed after full classification.
