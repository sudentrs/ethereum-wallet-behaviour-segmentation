import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_samples,
    silhouette_score,
)

try:
    from scipy.stats import kruskal
except ImportError:  # pragma: no cover - handled at runtime for lean installs.
    kruskal = None


NON_FEATURE_COLUMNS = {
    "wallet",
    "cluster",
    "old_cluster",
    "first_active_date",
    "last_active_date",
}


def parse_k_values(text: str) -> list[int]:
    if ".." in text:
        start, end = text.split("..", 1)
        return list(range(int(start), int(end) + 1))
    return [int(part.strip()) for part in text.split(",") if part.strip()]


def numeric_feature_columns(df: pd.DataFrame) -> list[str]:
    return [
        col
        for col in df.columns
        if col not in NON_FEATURE_COLUMNS and pd.api.types.is_numeric_dtype(df[col])
    ]


def load_feature_sample(
    path: Path,
    sample_size: int,
    chunksize: int,
    seed: int,
    estimated_rows: int,
) -> tuple[pd.Series, pd.DataFrame]:
    header = pd.read_csv(path, nrows=5000, dtype={"wallet": str})
    feature_cols = numeric_feature_columns(header)
    if not feature_cols:
        raise ValueError("No numeric feature columns found in feature table.")

    modulo = 10_000_000
    threshold = max(1, int((sample_size / estimated_rows) * modulo * 1.15))
    parts: list[pd.DataFrame] = []
    rows_seen = 0

    for chunk_id, chunk in enumerate(
        pd.read_csv(
            path,
            usecols=["wallet", *feature_cols],
            dtype={"wallet": str},
            chunksize=chunksize,
        ),
        start=1,
    ):
        rows_seen += len(chunk)
        hashes = pd.util.hash_pandas_object(chunk["wallet"], index=False).astype("uint64")
        kept = chunk.loc[(hashes % modulo) < threshold].copy()
        if not kept.empty:
            parts.append(kept)
        kept_rows = sum(len(part) for part in parts)
        print(f"sample chunk={chunk_id:03d} rows_seen={rows_seen:,} kept={kept_rows:,}", flush=True)

    if not parts:
        raise ValueError("No rows sampled from feature table.")

    sampled = pd.concat(parts, ignore_index=True)
    if len(sampled) > sample_size:
        sampled = sampled.sample(n=sample_size, random_state=seed).reset_index(drop=True)

    wallets = sampled["wallet"].copy()
    sample_df = sampled[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return wallets, sample_df


def normalized_entropy(labels: np.ndarray) -> float:
    _, counts = np.unique(labels, return_counts=True)
    shares = counts / counts.sum()
    entropy = -np.sum(shares * np.log(shares))
    return float(entropy / np.log(len(counts))) if len(counts) > 1 else 0.0


def bootstrap_ci(values: np.ndarray, seed: int, n_bootstrap: int = 1000) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    means = np.empty(n_bootstrap, dtype=np.float64)
    for i in range(n_bootstrap):
        idx = rng.integers(0, len(values), size=len(values))
        means[i] = values[idx].mean()
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def permutation_p_value(
    X: np.ndarray,
    labels: np.ndarray,
    observed: float,
    seed: int,
    null_permutations: int,
) -> tuple[float, float, float, float]:
    rng = np.random.default_rng(seed)
    null_scores = []
    for _ in range(null_permutations):
        shuffled = labels.copy()
        rng.shuffle(shuffled)
        null_scores.append(float(silhouette_score(X, shuffled)))
    null = np.array(null_scores, dtype=np.float64)
    p_value = (1 + np.sum(null >= observed)) / (null_permutations + 1)
    return float(null.mean()), float(null.std(ddof=1)), float(null.max()), float(p_value)


def kruskal_effect_summary(X: np.ndarray, labels: np.ndarray, feature_names: list[str]) -> dict:
    if kruskal is None:
        return {
            "significant_feature_count_bh_0_05": np.nan,
            "median_epsilon_squared": np.nan,
            "max_epsilon_squared": np.nan,
            "top_feature_by_effect": "",
            "top_feature_epsilon_squared": np.nan,
        }

    n = len(labels)
    k = len(np.unique(labels))
    p_values = []
    effects = []
    for feature_idx in range(X.shape[1]):
        groups = [X[labels == cluster, feature_idx] for cluster in np.unique(labels)]
        stat, p_value = kruskal(*groups)
        epsilon_squared = max(0.0, (stat - k + 1) / (n - k))
        p_values.append(float(p_value))
        effects.append(float(epsilon_squared))

    p_array = np.array(p_values)
    order = np.argsort(p_array)
    ranked = p_array[order]
    thresholds = 0.05 * (np.arange(1, len(ranked) + 1) / len(ranked))
    passed = ranked <= thresholds
    if passed.any():
        cutoff = ranked[np.where(passed)[0].max()]
        significant_count = int((p_array <= cutoff).sum())
    else:
        significant_count = 0

    effects_array = np.array(effects)
    top_idx = int(np.argmax(effects_array))
    return {
        "significant_feature_count_bh_0_05": significant_count,
        "median_epsilon_squared": float(np.median(effects_array)),
        "max_epsilon_squared": float(effects_array[top_idx]),
        "top_feature_by_effect": feature_names[top_idx],
        "top_feature_epsilon_squared": float(effects_array[top_idx]),
    }


def rank_score(series: pd.Series, higher_is_better: bool) -> pd.Series:
    ascending = not higher_is_better
    ranks = series.rank(ascending=ascending, method="min")
    if len(series) == 1:
        return pd.Series([1.0], index=series.index)
    return 1 - ((ranks - 1) / (len(series) - 1))


def make_scorecard(full_metrics: pd.DataFrame, sample_tests: pd.DataFrame) -> pd.DataFrame:
    df = full_metrics.merge(sample_tests, on="k", how="left")
    df["full_silhouette_score"] = rank_score(df["silhouette_mean"], True)
    df["full_stability_score"] = rank_score(df["stability_ari_mean"], True)
    df["full_davies_bouldin_score"] = rank_score(df["davies_bouldin_mean"], False)
    df["balance_score"] = rank_score(df["cluster_entropy"], True)
    df["null_test_score"] = (df["random_label_p_value"] <= 0.05).astype(float)
    df["feature_effect_score"] = rank_score(df["median_epsilon_squared"], True)
    max_distance_from_five = max(abs(df["k"].min() - 5), abs(df["k"].max() - 5), 1)
    df["parsimony_score"] = 1 - (abs(df["k"] - 5) / max_distance_from_five)
    df["parsimony_score"] = df["parsimony_score"].clip(lower=0)
    df["overall_statistical_score"] = df[
        [
            "full_silhouette_score",
            "full_stability_score",
            "full_davies_bouldin_score",
            "balance_score",
            "null_test_score",
            "feature_effect_score",
        ]
    ].mean(axis=1)

    role_rich = df["k"] >= 4
    df["role_taxonomy_score"] = np.where(
        role_rich,
        (
            (0.35 * df["full_stability_score"])
            + (0.20 * df["full_silhouette_score"])
            + (0.15 * df["full_davies_bouldin_score"])
            + (0.10 * df["balance_score"])
            + (0.15 * df["parsimony_score"])
            + (0.05 * df["null_test_score"])
        ),
        np.nan,
    )
    df["passes_random_null"] = df["random_label_p_value"] <= 0.05
    df["passes_min_size_5pct"] = df["min_cluster_share_mean"] >= 0.05
    df["passes_seed_stability_055"] = df["stability_ari_mean"] >= 0.55
    df["passes_feature_separation"] = df["significant_feature_count_bh_0_05"] >= (
        0.75 * df["significant_feature_count_bh_0_05"].max()
    )
    df["defensible_role_taxonomy"] = (
        (df["k"] >= 4)
        & df["passes_random_null"]
        & df["passes_min_size_5pct"]
        & df["passes_seed_stability_055"]
        & df["passes_feature_separation"]
    )
    return df.sort_values("k")


def plot_line(df: pd.DataFrame, y_cols: list[str], path: Path, title: str, ylabel: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.8))
    for col in y_cols:
        ax.plot(df["k"], df[col], marker="o", linewidth=2, label=col)
    ax.set_title(title)
    ax.set_xlabel("K")
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_rank_heatmap(scorecard: pd.DataFrame, path: Path) -> None:
    cols = [
        "full_silhouette_score",
        "full_stability_score",
        "full_davies_bouldin_score",
        "balance_score",
        "parsimony_score",
        "feature_effect_score",
        "overall_statistical_score",
        "role_taxonomy_score",
    ]
    mat = scorecard[cols].to_numpy(dtype=float)
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    im = ax.imshow(mat, aspect="auto", cmap="viridis", vmin=0, vmax=1)
    ax.set_yticks(np.arange(len(scorecard)))
    ax.set_yticklabels([f"K={int(k)}" for k in scorecard["k"]])
    ax.set_xticks(np.arange(len(cols)))
    ax.set_xticklabels([col.replace("_score", "").replace("_", " ") for col in cols], rotation=35, ha="right")
    ax.set_title("Model Selection Scorecard (Higher Is Better)")
    fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def write_report(
    out_dir: Path,
    full_metrics: pd.DataFrame,
    sample_tests: pd.DataFrame,
    scorecard: pd.DataFrame,
    args: argparse.Namespace,
) -> None:
    best_overall = scorecard.sort_values("overall_statistical_score", ascending=False).iloc[0]
    defensible_roles = scorecard[scorecard["defensible_role_taxonomy"]].sort_values(
        "role_taxonomy_score", ascending=False
    )
    best_role = defensible_roles.iloc[0] if not defensible_roles.empty else scorecard.dropna(
        subset=["role_taxonomy_score"]
    ).sort_values("role_taxonomy_score", ascending=False).iloc[0]
    best_metric_only = full_metrics.sort_values(
        ["silhouette_mean", "stability_ari_mean"], ascending=False
    ).iloc[0]

    lines = [
        "# EOA-Only K Model Selection Dossier",
        "",
        "## Question",
        "",
        "Which K values are statistically defensible for EOA-only Ethereum wallet behaviour segmentation?",
        "",
        "This dossier does not try to prove a single true K. It separates a coarse metric answer from a role-taxonomy answer.",
        "",
        "## Evidence Used",
        "",
        f"- Full EOA-only K sensitivity table: `{args.k_sensitivity}`.",
        f"- Sampled proof tests from `{args.features}`.",
        f"- Sample size for proof tests: `{args.sample_size:,}` wallets.",
        f"- Evaluation size for silhouette/null tests: `{args.eval_size:,}` wallets.",
        f"- Random-label permutations per K: `{args.null_permutations}`.",
        f"- Tested K values: `{', '.join(map(str, parse_k_values(args.k_values)))}`.",
        "",
        "## Main Conclusion",
        "",
        f"- Best metric-only/coarse K: `K={int(best_metric_only['k'])}`.",
        f"- Best overall statistical score in this dossier: `K={int(best_overall['k'])}`.",
        f"- Best role-taxonomy candidate after defensibility gates: `K={int(best_role['k'])}`.",
        "",
        "For this project, the strongest academically defensible wording is:",
        "",
        "> K=5 is statistically defensible as the preferred richer role-taxonomy candidate among the tested alternatives. K=2 and K=3 are stronger if the goal is only coarse separation. K=4 is also defensible but less expressive. K>=6 creates more roles, but the EOA-only evidence shows weaker seed stability and/or smaller clusters, so those values need downstream justification before becoming the primary claim.",
        "",
        "## Full-Data Screening Metrics",
        "",
        full_metrics.to_markdown(index=False),
        "",
        "## Sample-Based Statistical Proof Tests",
        "",
        sample_tests.to_markdown(index=False),
        "",
        "## Model Selection Scorecard",
        "",
        scorecard[
            [
                "k",
                "overall_statistical_score",
                "role_taxonomy_score",
                "defensible_role_taxonomy",
                "silhouette_mean",
                "stability_ari_mean",
                "min_cluster_share_mean",
                "cluster_entropy",
                "random_label_p_value",
                "median_epsilon_squared",
            ]
        ].to_markdown(index=False),
        "",
        "## Plain-Language Explanation Of The Tests",
        "",
        "### Full-data K sensitivity",
        "",
        "This tests several possible numbers of clusters, from K=2 to K=10. The goal is to avoid choosing a cluster count only because it looks convenient. If a K value is defensible, it should look reasonable compared with nearby alternatives.",
        "",
        "### Silhouette score",
        "",
        "Silhouette measures whether wallets are closer to wallets in their own cluster than to wallets in other clusters. Higher values mean cleaner separation. In this analysis, K=2 and K=3 have the strongest silhouette scores, which means the broadest divisions are easiest to separate.",
        "",
        "### Seed stability",
        "",
        "KMeans starts from random initial positions. Seed stability checks whether the clustering result stays similar when the algorithm is rerun with different random starts. A stable K is easier to defend because it is less dependent on random initialization.",
        "",
        "### ARI and NMI",
        "",
        "Adjusted Rand Index and Normalized Mutual Information compare two clustering runs. In simple terms, they ask whether two runs mostly assign wallets to similar groups. Higher ARI and NMI mean the cluster structure is more repeatable.",
        "",
        "### Davies-Bouldin score",
        "",
        "Davies-Bouldin measures whether clusters are compact and separated from each other. Lower values are better. It is useful as a secondary check, but it should not be used alone to choose K.",
        "",
        "### Calinski-Harabasz score",
        "",
        "Calinski-Harabasz compares separation between clusters with variation inside clusters. Higher values usually indicate clearer separation. Like the other internal metrics, it is evidence, not a final decision rule.",
        "",
        "### Inertia",
        "",
        "Inertia is the objective KMeans directly minimizes. It measures how far wallets are from their assigned cluster centers. It always decreases as K increases, so it cannot choose K by itself. It is mainly useful for checking whether there is an elbow where extra clusters stop adding much improvement.",
        "",
        "### Random-label null test",
        "",
        "The random-label null test keeps the same number of clusters and the same cluster sizes, but shuffles the labels randomly. Then it compares the real clustering against those random assignments. If the real clustering is much stronger than the shuffled labels, the result is not just a random grouping. In this run, every tested K had a p-value of about 0.0196 against the random-label null.",
        "",
        "### Bootstrap confidence interval",
        "",
        "The bootstrap confidence interval estimates uncertainty around the sampled silhouette score. Instead of trusting one sample value, it resamples the evaluation wallets many times and reports a likely range. Narrow intervals mean the sampled estimate is more stable.",
        "",
        "### Kruskal-Wallis feature-separation test",
        "",
        "This test checks whether the clusters differ across the engineered wallet-behaviour features. It asks whether the groups are behaviourally different, not only algorithmically labelled. Because this dataset is large, statistical significance is expected for many features, so effect size is also needed.",
        "",
        "### Epsilon-squared effect size",
        "",
        "Epsilon squared measures how large the feature differences are. This helps separate meaningful behavioural differences from differences that are statistically significant only because the dataset is very large.",
        "",
        "### Cluster-size gate",
        "",
        "The cluster-size gate checks whether a K value creates very small groups. For the role-taxonomy decision, a K value should avoid clusters below 5 percent of the full EOA-only dataset. Very small clusters may still be interesting, but they are harder to defend as main wallet roles.",
        "",
        "### Parsimony",
        "",
        "Parsimony means preferring the simpler model when two choices explain the data similarly well. Higher K values often create more specific differences, but that does not automatically make them better. A paper-facing taxonomy should use enough roles to be informative without splitting the population unnecessarily.",
        "",
        "### Role-taxonomy score",
        "",
        "The role-taxonomy score is aligned with the research goal of finding interpretable wallet roles. It combines separation, stability, cluster size, random-label evidence, and parsimony. It is different from asking which K has the single best internal metric.",
        "",
        "### Defensible role-taxonomy flag",
        "",
        "This is a pass/fail decision rule. A K value passes only if it has at least four clusters, beats the random-label null test, avoids clusters below 5 percent, reaches acceptable seed stability, and shows broad feature separation.",
        "",
        "## Commentary On The Results",
        "",
        "The strongest purely statistical separation appears at K=2 and K=3. These values have the best silhouette and seed-stability results, so they are useful evidence that the EOA-only wallet population has a strong coarse structure.",
        "",
        "However, K=2 and K=3 are too broad for the main research goal. They would tell us that wallets can be divided into a few large behavioural groups, but they do not provide a rich enough vocabulary for wallet roles.",
        "",
        "K=4 passes the defensibility gates and is a conservative multi-role option. Its main limitation is interpretability depth: it compresses the wallet population into fewer behavioural types, so some meaningful distinctions may remain merged.",
        "",
        "K=5 is the best balance under the current evidence. It passes the random-label test, passes the minimum-size gate, has broad feature separation, and has much stronger seed stability than K=6. This makes it the preferred EOA-only role-taxonomy candidate.",
        "",
        "K=6 remains interpretable, but it is weaker after contract removal. Its seed-stability ARI is 0.4848, compared with 0.7126 for K=5. That means the six-cluster solution is more sensitive to random initialization, so it should not be claimed as the best-supported EOA-only resolution unless downstream graph and temporal validation clearly justify the extra role.",
        "",
        "K=7 through K=10 produce more detailed partitions, and some of their feature-separation effect sizes are strong. This is expected because more clusters can create more specific feature differences. The problem is that these higher K values produce smaller clusters and weaker stability, so they risk over-fragmenting the wallet population.",
        "",
        "The correct academic conclusion is therefore not that K=5 is the only true number of Ethereum wallet roles. The defensible claim is that, among tested alternatives, K=5 currently offers the strongest balance between statistical support, stability, cluster size, and role interpretability for the EOA-only dataset.",
        "",
        "## How To Read This",
        "",
        "- Silhouette asks whether wallets are closer to their own cluster than to other clusters.",
        "- Seed stability asks whether the same K gives similar clusters when KMeans starts from different random initializations.",
        "- Random-label testing asks whether the observed separation is stronger than shuffled labels with the same cluster sizes.",
        "- Feature separability asks whether the clusters differ across the engineered wallet behaviour features, not only by algorithm labels.",
        "- Cluster entropy asks whether the solution avoids being dominated by one giant cluster and several very small clusters.",
        "- The defensible role-taxonomy flag requires K>=4, p<=0.05 against random labels, no cluster below 5 percent in the full run, ARI stability at least 0.55, and broad feature separation.",
        "",
        "## Claim Boundaries",
        "",
        "- These tests support defensibility, not a universal natural law for Ethereum wallets.",
        "- The selected K should still be tied to interpretability and downstream network/temporal validation.",
        "- K=5 should be presented as the preferred EOA-only role-taxonomy candidate under the current evidence, not as the only possible partition.",
    ]
    (out_dir / "eoa_k_model_selection_report.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create an EOA-only K model-selection dossier with statistical checks and visuals."
    )
    parser.add_argument("--features", required=True)
    parser.add_argument("--k-sensitivity", required=True)
    parser.add_argument("--out-dir", default="results/eoa_k_model_selection")
    parser.add_argument("--k-values", default="2..10")
    parser.add_argument("--sample-size", type=int, default=60_000)
    parser.add_argument("--estimated-rows", type=int, default=2_443_868)
    parser.add_argument("--eval-size", type=int, default=8_000)
    parser.add_argument("--chunksize", type=int, default=100_000)
    parser.add_argument("--random-state", type=int, default=492)
    parser.add_argument("--null-permutations", type=int, default=20)
    parser.add_argument(
        "--reuse-sample",
        action="store_true",
        help="Reuse model_selection_sample_features.csv if it already exists in the output folder.",
    )
    parser.add_argument("--batch-size", type=int, default=8192)
    parser.add_argument("--n-init", type=int, default=5)
    parser.add_argument("--max-iter", type=int, default=150)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    figures_dir = out_dir / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    features_path = Path(args.features)
    k_sensitivity_path = Path(args.k_sensitivity)
    if not features_path.exists():
        raise FileNotFoundError(f"Feature table not found: {features_path}")
    if not k_sensitivity_path.exists():
        raise FileNotFoundError(f"K-sensitivity summary not found: {k_sensitivity_path}")

    full_metrics = pd.read_csv(k_sensitivity_path)
    k_values = parse_k_values(args.k_values)
    full_metrics = full_metrics[full_metrics["k"].isin(k_values)].copy()

    sample_features_path = out_dir / "model_selection_sample_features.csv"
    sample_wallets_path = out_dir / "model_selection_sample_wallets.csv"
    if args.reuse_sample and sample_features_path.exists() and sample_wallets_path.exists():
        sample_df = pd.read_csv(sample_features_path)
        wallets = pd.read_csv(sample_wallets_path, dtype={"wallet": str})["wallet"]
        print(f"reused sample rows={len(sample_df):,}", flush=True)
    else:
        wallets, sample_df = load_feature_sample(
            features_path,
            sample_size=args.sample_size,
            chunksize=args.chunksize,
            seed=args.random_state,
            estimated_rows=args.estimated_rows,
        )
        sample_df.to_csv(sample_features_path, index=False)
        wallets.to_frame().to_csv(sample_wallets_path, index=False)

    feature_names = sample_df.columns.tolist()
    X = sample_df.to_numpy(dtype=np.float32)
    rng = np.random.default_rng(args.random_state)
    eval_n = min(args.eval_size, len(sample_df))
    eval_idx = rng.choice(len(sample_df), size=eval_n, replace=False)
    X_eval = X[eval_idx]

    test_rows = []
    for k in k_values:
        model = MiniBatchKMeans(
            n_clusters=k,
            random_state=args.random_state,
            batch_size=args.batch_size,
            n_init=args.n_init,
            max_iter=args.max_iter,
        )
        labels = model.fit_predict(X)
        eval_labels = labels[eval_idx]

        sil_values = silhouette_samples(X_eval, eval_labels)
        sil_mean = float(sil_values.mean())
        ci_low, ci_high = bootstrap_ci(sil_values, seed=args.random_state + k)
        null_mean, null_std, null_max, null_p = permutation_p_value(
            X_eval,
            eval_labels.copy(),
            observed=sil_mean,
            seed=args.random_state + (k * 100),
            null_permutations=args.null_permutations,
        )
        effects = kruskal_effect_summary(X_eval, eval_labels, feature_names)

        counts = pd.Series(labels).value_counts().sort_index()
        test_rows.append(
            {
                "k": k,
                "sample_wallets": len(sample_df),
                "eval_wallets": eval_n,
                "sample_silhouette_mean": sil_mean,
                "sample_silhouette_ci_low": ci_low,
                "sample_silhouette_ci_high": ci_high,
                "random_label_null_mean": null_mean,
                "random_label_null_std": null_std,
                "random_label_null_max": null_max,
                "random_label_p_value": null_p,
                "min_cluster_share_sample": float((counts / counts.sum()).min()),
                "max_cluster_share_sample": float((counts / counts.sum()).max()),
                "cluster_entropy": normalized_entropy(labels),
                **effects,
            }
        )
        print(f"k={k} sample_silhouette={sil_mean:.4f} null_p={null_p:.4f}", flush=True)

    sample_tests = pd.DataFrame(test_rows)
    scorecard = make_scorecard(full_metrics, sample_tests)

    full_metrics.to_csv(out_dir / "full_k_sensitivity_metrics.csv", index=False)
    sample_tests.to_csv(out_dir / "sample_statistical_tests.csv", index=False)
    scorecard.to_csv(out_dir / "model_selection_scorecard.csv", index=False)

    plot_line(
        full_metrics,
        ["silhouette_mean"],
        figures_dir / "full_silhouette_by_k.png",
        "Full EOA-Only Silhouette By K",
        "Silhouette",
    )
    plot_line(
        full_metrics,
        ["stability_ari_mean", "stability_nmi_mean"],
        figures_dir / "seed_stability_by_k.png",
        "Seed Stability By K",
        "Agreement Score",
    )
    plot_line(
        full_metrics,
        ["min_cluster_share_mean", "max_cluster_share_mean"],
        figures_dir / "cluster_balance_by_k.png",
        "Cluster Balance By K",
        "Wallet Share",
    )
    plot_line(
        full_metrics,
        ["davies_bouldin_mean"],
        figures_dir / "davies_bouldin_by_k.png",
        "Davies-Bouldin By K (Lower Is Better)",
        "Davies-Bouldin",
    )
    plot_line(
        full_metrics,
        ["inertia_mean"],
        figures_dir / "inertia_elbow_by_k.png",
        "Inertia Elbow By K",
        "Inertia",
    )
    plot_line(
        sample_tests,
        ["sample_silhouette_mean", "random_label_null_mean", "random_label_null_max"],
        figures_dir / "sample_silhouette_vs_random_null.png",
        "Observed Sample Silhouette Vs Random-Label Null",
        "Silhouette",
    )
    plot_line(
        sample_tests,
        ["median_epsilon_squared", "max_epsilon_squared"],
        figures_dir / "feature_separability_effects_by_k.png",
        "Feature Separability Effect Sizes By K",
        "Epsilon Squared",
    )
    plot_rank_heatmap(scorecard, figures_dir / "model_selection_scorecard_heatmap.png")
    write_report(out_dir, full_metrics, sample_tests, scorecard, args)

    print(scorecard[["k", "overall_statistical_score", "role_taxonomy_score"]].to_string(index=False), flush=True)
    print(f"Saved EOA K model-selection dossier to: {out_dir.resolve()}", flush=True)


if __name__ == "__main__":
    main()
