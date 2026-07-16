from pathlib import Path

import pandas as pd


def top_event_summary(event_tests: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "event_month",
        "metric",
        "observed",
        "non_event_mean",
        "event_mean",
        "rank_p_value",
    ]
    return event_tests[cols].sort_values(["metric", "rank_p_value"]).reset_index(drop=True)


def main() -> None:
    signal_dir = Path("results/temporal_signal_analysis_edge_sample_10k")
    k_compare_dir = Path("results/temporal_signal_k_taxonomy_comparison")
    paper_pack_dir = Path("results/academic_paper_pack/k5")
    out_path = k_compare_dir / "paper_ready_temporal_signal_section.md"
    k_compare_dir.mkdir(parents=True, exist_ok=True)

    correspondence = pd.read_csv(k_compare_dir / "k_taxonomy_signal_correspondence.csv")
    signal_validation = pd.read_csv(signal_dir / "signal_cluster_validation_summary.csv")
    signal_network = pd.read_csv(signal_dir / "network_signal_cluster_null_tests.csv")
    k_network = pd.read_csv(k_compare_dir / "k_taxonomy_signal_network_null_tests.csv")
    wavelength_labels = pd.read_csv(signal_dir / "wavelength_cluster_interpretive_labels.csv")
    time_labels = pd.read_csv(signal_dir / "time_domain_cluster_interpretive_labels.csv")
    event_tests = pd.read_csv(paper_pack_dir / "k5_event_adjacent_rank_tests.csv")
    two_step = pd.read_csv(paper_pack_dir / "k5_two_step_return_null_tests.csv")

    lines = [
        "# Paper-Ready Temporal Signal Extension",
        "",
        "## Research Question",
        "",
        "After removing contract addresses and selecting K5 as the main EOA behavioural taxonomy, the next question is whether wallet roles are also visible in temporal activity signals.",
        "",
        "The signal-extension question is:",
        "",
        "> Do Ethereum EOA wallets exhibit temporal activity rhythms and time-domain behavioural states that provide evidence beyond the static K4/K5/K6 aggregate feature taxonomies?",
        "",
        "## Method",
        "",
        "We used an edge-aware sample of 10,000 EOA wallets. Wallets were selected from sampled transaction-edge endpoints so that the later network-science validation would have enough sample-internal edges.",
        "",
        "For each wallet, we reconstructed daily 2022 transaction-count, total-flow, and net-flow signals from the monthly wallet-daily files.",
        "",
        "We extracted two temporal representations:",
        "",
        "1. Frequency-domain features from FFT spectra of daily transaction-count and value-flow signals.",
        "2. Time-domain features describing active days, inactive gaps, active streaks, burstiness, switching, direction bias, and weekly change intensity.",
        "",
        "We clustered each representation into five signal clusters and compared them with K4, K5, and K6 static taxonomies.",
        "",
        "## Signal Cluster Validation",
        "",
        signal_validation.to_markdown(index=False),
        "",
        "Both signal representations have positive observed silhouette values and shuffled-label p-values of approximately 0.0099. This supports the limited claim that the signal clusters have measurable feature-space structure in the sampled data.",
        "",
        "Seed-stability is moderate rather than perfect. This means the signal clusters are structured, but they should be treated as exploratory temporal states rather than fixed identity classes.",
        "",
        "## Temporal Cluster Interpretations",
        "",
        "Wavelength cluster labels:",
        "",
        wavelength_labels.to_markdown(index=False),
        "",
        "Time-domain cluster labels:",
        "",
        time_labels.to_markdown(index=False),
        "",
        "These labels are profile-based interpretations. They should be used as descriptive shorthand, not as ground-truth wallet identities.",
        "",
        "## Relationship To K4, K5, And K6",
        "",
        correspondence.to_markdown(index=False),
        "",
        "The temporal signal clusters do not strongly reproduce K4, K5, or K6. K5 has the highest ARI for both wavelength and time-domain comparisons, but the values remain low to moderate.",
        "",
        "This is important academically because it suggests that temporal signal analysis is not merely duplicating the static clustering result. It adds a separate behavioural layer.",
        "",
        "## Network-Science Validation",
        "",
        signal_network.to_markdown(index=False),
        "",
        "The 10,000-wallet edge-aware sample produced 46,771 usable sampled transaction edges.",
        "",
        "The wavelength clusters show same-cluster transaction concentration above the shuffled-label null model. This supports a sample-based network-alignment claim for frequency-domain wallet rhythms.",
        "",
        "The time-domain clusters do not show same-cluster transaction concentration above the null model in the 10k run. This weakens any claim that burst/gap/streak states are assortative in the sampled transaction network.",
        "",
        "K-taxonomy network comparison:",
        "",
        k_network.to_markdown(index=False),
        "",
        "K4, K5, and K6 all show strong same-cluster transaction concentration compared with shuffled labels. This confirms that the static aggregate taxonomies remain more directly aligned with transaction-network homophily than the time-domain signal states.",
        "",
        "## Event-Adjacent Temporal Checks",
        "",
        top_event_summary(event_tests).to_markdown(index=False),
        "",
        "The event-adjacent tests should be treated as contextual checks, not causal evidence. Some event-adjacent month pairs show larger composition changes or lower self-transition rates, but the rank tests do not by themselves prove that external market events caused wallet-state movement.",
        "",
        "## Two-Step Return Behaviour",
        "",
        two_step.to_markdown(index=False),
        "",
        "Across monthly triples, wallets that left their original K5 state often returned two months later more frequently than expected under the null model. This supports a cautious claim of behavioural mean reversion or temporary state excursions, not a claim about user intent.",
        "",
        "## Contribution",
        "",
        "The contribution is a layered validation framework for Ethereum EOA wallet behaviour:",
        "",
        "1. Static aggregate roles from K4/K5/K6 clustering.",
        "2. Frequency-domain temporal rhythms from daily wallet signals.",
        "3. Time-domain activity states from burst, gap, and persistence features.",
        "4. Network-science validation through shuffled-label edge null tests.",
        "5. Temporal stability checks through transition and two-step return analyses.",
        "",
        "The strongest paper claim is not that one K value or one signal model is universally correct. The stronger claim is that wallet behaviour can be studied as multiple related layers: aggregate role, temporal rhythm, time-domain activity state, and network position.",
    ]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved paper-ready temporal signal section to {out_path.resolve()}")


if __name__ == "__main__":
    main()
