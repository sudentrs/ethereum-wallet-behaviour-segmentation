from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results" / "population_reshuffle_baseline"


def load_cluster_sizes(k: int) -> pd.DataFrame:
    path = ROOT / "results" / f"eoa_only_kmeans{k}" / "cluster_sizes.csv"
    return pd.read_csv(path)


def load_network_summary(k: int) -> pd.Series:
    path = ROOT / "results" / f"eoa_only_kmeans{k}" / "network_validation" / "network_validation_summary.csv"
    return pd.read_csv(path).iloc[0]


def build_summary() -> pd.DataFrame:
    rows = []
    for k in (4, 5, 6):
        sizes = load_cluster_sizes(k)
        network = load_network_summary(k)

        population_expected_same_role = float((sizes["wallet_share"] ** 2).sum())
        observed_sample_same_role = float(network["observed_sample_same_cluster_ratio"])
        edge_shuffle_null_mean = float(network["null_mean"])

        rows.append(
            {
                "k": k,
                "wallets": int(sizes["wallet_count"].sum()),
                "population_expected_same_role_ratio": population_expected_same_role,
                "observed_sample_same_role_ratio": observed_sample_same_role,
                "population_random_mixing_lift": observed_sample_same_role / population_expected_same_role,
                "edge_shuffle_null_mean": edge_shuffle_null_mean,
                "edge_shuffle_lift": observed_sample_same_role / edge_shuffle_null_mean,
                "edge_shuffle_p_value_upper": float(network["p_value_upper"]),
                "interpretation": interpretation(k),
            }
        )
    return pd.DataFrame(rows)


def interpretation(k: int) -> str:
    if k == 4:
        return "Observed same-role transaction concentration is above both the population random-mixing baseline and the edge-level shuffled-label null, supporting K4 as the strongest conservative network-aligned taxonomy."
    if k == 5:
        return "Observed same-role transaction concentration is slightly above the population random-mixing baseline but close to, and slightly below, the edge-level shuffled-label null, so K5 should be described as network-mixed rather than strongly network-validated."
    return "Observed same-role transaction concentration is above the population random-mixing baseline and borderline above the edge-level shuffled-label null, but K6 remains less stable than K5."


def write_report(summary: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUT_DIR / "population_reshuffle_baseline_summary.csv", index=False)

    lines = [
        "# Population Reshuffle Baseline",
        "",
        "## Purpose",
        "",
        "This analysis adds a simple population-level random-mixing baseline for the EOA-only K4, K5, and K6 transaction-network validation results.",
        "It asks what same-role transaction concentration would be expected if wallet labels were randomly mixed across the population while preserving the cluster-size distribution.",
        "This is not a replacement for the edge-level shuffled-label test; it is an additional baseline that makes the role-size effect easier to explain in the paper.",
        "",
        "## Summary",
        "",
        "| k | Population expected same-role ratio | Observed same-role ratio | Population lift | Edge-shuffle null mean | Edge-shuffle lift | Edge-shuffle p-value |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for row in summary.itertuples(index=False):
        lines.append(
            f"| {row.k} | {row.population_expected_same_role_ratio:.4f} | "
            f"{row.observed_sample_same_role_ratio:.4f} | "
            f"{row.population_random_mixing_lift:.2f}x | "
            f"{row.edge_shuffle_null_mean:.4f} | "
            f"{row.edge_shuffle_lift:.2f}x | "
            f"{row.edge_shuffle_p_value_upper:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
        ]
    )

    for row in summary.itertuples(index=False):
        lines.extend([f"- K{row.k}: {row.interpretation}", ""])

    lines.extend(
        [
            "## Paper Wording",
            "",
            "A population-level random-mixing baseline was added to separate cluster-size effects from network alignment.",
            "For each candidate taxonomy, the expected same-role transaction ratio under random population mixing is the sum of squared cluster shares.",
            "K4 shows the clearest network alignment, with an observed same-role ratio above both the population baseline and the edge-level shuffled-label null.",
            "K5 remains the preferred richer behavioural taxonomy, but its same-role transaction concentration is only slightly above the population baseline and is not above the edge-level shuffled-label null.",
            "Therefore, K5 should be described as feature-space and temporally supported, with mixed same-role network evidence.",
        ]
    )

    (OUT_DIR / "population_reshuffle_baseline_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    summary = build_summary()
    write_report(summary)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
