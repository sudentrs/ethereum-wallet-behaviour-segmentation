from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "results" / "academic_paper_pack"


EVENTS = pd.DataFrame(
    [
        {
            "event_month": "202205",
            "event_label": "Terra/UST-LUNA collapse",
            "scope": "market-wide crypto stress",
            "source": "Briola et al. 2022; Kim et al. 2022; Wired",
            "source_url": "https://arxiv.org/abs/2207.13914",
        },
        {
            "event_month": "202206",
            "event_label": "Celsius withdrawal halt / liquidity stress",
            "scope": "centralized-lending stress",
            "source": "crypto-market timelines and news reports",
            "source_url": "https://en.wikipedia.org/wiki/Cryptocurrency_bubble",
        },
        {
            "event_month": "202209",
            "event_label": "Ethereum Merge",
            "scope": "Ethereum protocol event",
            "source": "Kapengut and Mizrach 2022",
            "source_url": "https://arxiv.org/abs/2210.13655",
        },
        {
            "event_month": "202211",
            "event_label": "FTX collapse and bankruptcy",
            "scope": "market-wide exchange crisis",
            "source": "AP timeline; bankruptcy filings/news",
            "source_url": "https://apnews.com/article/c519d50b9059aa8bff0ce8b6cd26c40e",
        },
    ]
)


def k_dir(k: int) -> Path:
    return ROOT / "results" / f"eoa_only_kmeans{k}" / "temporal_validation"


def transition_dir(k: int) -> Path:
    return OUT_DIR / f"k{k}"


def load_monthly_summary(k: int) -> pd.DataFrame:
    return pd.read_csv(k_dir(k) / "monthly_behavior_state_summary.csv", dtype={"month": str})


def state_share_columns(df: pd.DataFrame) -> list[str]:
    return [col for col in df.columns if col.startswith("state_C") and col.endswith("_share")]


def transition_l1_changes(k: int) -> pd.DataFrame:
    monthly = load_monthly_summary(k)
    cols = state_share_columns(monthly)
    rows = []
    for i in range(len(monthly) - 1):
        current = monthly.loc[i, cols].to_numpy(dtype=float)
        nxt = monthly.loc[i + 1, cols].to_numpy(dtype=float)
        rows.append(
            {
                "k": k,
                "from_month": monthly.loc[i, "month"],
                "to_month": monthly.loc[i + 1, "month"],
                "composition_l1_change": float(np.abs(nxt - current).sum()),
                "composition_l2_change": float(np.sqrt(np.sum((nxt - current) ** 2))),
            }
        )
    out = pd.DataFrame(rows)
    out["to_month_is_event"] = out["to_month"].isin(EVENTS["event_month"])
    return out


def event_rank_tests(k: int) -> pd.DataFrame:
    transitions = pd.read_csv(k_dir(k) / "monthly_transition_summary.csv", dtype={"from_month": str, "to_month": str})
    changes = transition_l1_changes(k)
    merged = transitions.merge(changes, on=["from_month", "to_month"], how="inner")
    merged["to_month_is_event"] = merged["to_month"].isin(EVENTS["event_month"])

    rows = []
    metrics = [
        ("composition_l1_change", "higher"),
        ("self_transition_rate", "lower"),
        ("mean_row_entropy_bits", "higher"),
    ]
    for metric, direction in metrics:
        all_values = merged[metric].to_numpy(dtype=float)
        event_values = merged.loc[merged["to_month_is_event"], metric].to_numpy(dtype=float)
        non_event_values = merged.loc[~merged["to_month_is_event"], metric].to_numpy(dtype=float)
        for month, observed in merged.loc[merged["to_month_is_event"], ["to_month", metric]].itertuples(index=False):
            if direction == "higher":
                p_rank = (1 + np.sum(all_values >= observed)) / (len(all_values) + 1)
            else:
                p_rank = (1 + np.sum(all_values <= observed)) / (len(all_values) + 1)
            rows.append(
                {
                    "k": k,
                    "event_month": month,
                    "metric": metric,
                    "direction_tested": direction,
                    "observed": observed,
                    "all_month_pair_mean": float(np.mean(all_values)),
                    "non_event_mean": float(np.mean(non_event_values)) if len(non_event_values) else np.nan,
                    "event_mean": float(np.mean(event_values)) if len(event_values) else np.nan,
                    "rank_p_value": float(p_rank),
                }
            )
    return pd.DataFrame(rows)


def state_share_zscores(k: int) -> pd.DataFrame:
    monthly = load_monthly_summary(k)
    cols = state_share_columns(monthly)
    rows = []
    for col in cols:
        values = monthly[col].to_numpy(dtype=float)
        sd = values.std(ddof=1)
        for month, value in zip(monthly["month"], values):
            rows.append(
                {
                    "k": k,
                    "month": month,
                    "state": col.replace("state_", "").replace("_share", ""),
                    "share": value,
                    "z_score_vs_months": (value - values.mean()) / sd if sd else np.nan,
                    "is_event_month": month in set(EVENTS["event_month"]),
                }
            )
    return pd.DataFrame(rows)


def transition_residuals(k: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    counts = pd.read_csv(k_dir(k) / "overall_transition_count_matrix.csv", index_col=0)
    counts.index = counts.index.astype(int)
    counts.columns = counts.columns.astype(int)
    obs = counts.to_numpy(dtype=float)
    total = obs.sum()
    row_totals = obs.sum(axis=1, keepdims=True)
    col_totals = obs.sum(axis=0, keepdims=True)
    expected = row_totals @ col_totals / total
    residual = (obs - expected) / np.sqrt(np.where(expected == 0, np.nan, expected))
    residual_df = pd.DataFrame(residual, index=counts.index, columns=counts.columns)
    expected_df = pd.DataFrame(expected, index=counts.index, columns=counts.columns)
    return residual_df, expected_df


def two_step_null_test(k: int, permutations: int = 500, random_state: int = 492) -> pd.DataFrame:
    path = k_dir(k) / "wallet_monthly_behavior_states.csv"
    assignments = pd.read_csv(path, usecols=["wallet", "month", "monthly_state"], dtype={"wallet": str, "month": str})
    months = sorted(assignments["month"].unique())
    rng = np.random.default_rng(random_state + k)
    rows = []

    for m0, m1, m2 in zip(months[:-2], months[1:-1], months[2:]):
        a = assignments[assignments["month"] == m0][["wallet", "monthly_state"]].rename(columns={"monthly_state": "state_t"})
        b = assignments[assignments["month"] == m1][["wallet", "monthly_state"]].rename(columns={"monthly_state": "state_t1"})
        c = assignments[assignments["month"] == m2][["wallet", "monthly_state"]].rename(columns={"monthly_state": "state_t2"})
        merged = a.merge(b, on="wallet", how="inner").merge(c, on="wallet", how="inner")
        left = merged[merged["state_t"] != merged["state_t1"]].copy()
        if left.empty:
            continue

        state_t = left["state_t"].to_numpy(dtype=int)
        state_t2 = left["state_t2"].to_numpy(dtype=int)
        observed = float(np.mean(state_t == state_t2))
        null_rates = np.empty(permutations, dtype=float)
        for i in range(permutations):
            shuffled = rng.permutation(state_t2)
            null_rates[i] = np.mean(state_t == shuffled)
        p_upper = (1 + np.sum(null_rates >= observed)) / (permutations + 1)
        rows.append(
            {
                "k": k,
                "month_t": m0,
                "month_t1": m1,
                "month_t2": m2,
                "left_original_state_count": len(left),
                "observed_two_step_return_rate": observed,
                "null_mean": float(null_rates.mean()),
                "null_std": float(null_rates.std(ddof=1)),
                "p_value_upper": float(p_upper),
                "observed_minus_null": observed - float(null_rates.mean()),
            }
        )
    return pd.DataFrame(rows)


def top_transition_pathways(k: int, top_n: int = 12) -> pd.DataFrame:
    probs = pd.read_csv(k_dir(k) / "overall_transition_probability_matrix.csv", index_col=0)
    rows = []
    for src in probs.index:
        for dst in probs.columns:
            src_int = int(src)
            dst_int = int(dst)
            if src_int == dst_int:
                continue
            rows.append({"k": k, "from_state": src_int, "to_state": dst_int, "probability": probs.loc[src, dst]})
    return pd.DataFrame(rows).sort_values("probability", ascending=False).head(top_n)


def plot_state_shares(k: int, out_dir: Path) -> None:
    monthly = load_monthly_summary(k)
    cols = state_share_columns(monthly)
    fig, ax = plt.subplots(figsize=(10.5, 5.4))
    x = np.arange(len(monthly))
    for col in cols:
        ax.plot(x, monthly[col], marker="o", linewidth=1.8, label=col.replace("state_", "").replace("_share", ""))
    for event_month in EVENTS["event_month"]:
        if event_month in monthly["month"].values:
            pos = int(monthly.index[monthly["month"] == event_month][0])
            ax.axvline(pos, color="black", linestyle="--", linewidth=1, alpha=0.55)
    ax.set_xticks(x)
    ax.set_xticklabels(monthly["month"], rotation=45, ha="right")
    ax.set_ylabel("Share of active wallets")
    ax.set_title(f"EOA K{k} Monthly State Shares With Event Months")
    ax.legend(ncol=3)
    fig.tight_layout()
    fig.savefig(out_dir / f"k{k}_monthly_state_shares_events.png", dpi=220)
    plt.close(fig)


def plot_self_transition(k: int, out_dir: Path) -> None:
    transition = pd.read_csv(k_dir(k) / "monthly_transition_summary.csv", dtype={"from_month": str, "to_month": str})
    transition["to_month_is_event"] = transition["to_month"].isin(EVENTS["event_month"])
    labels = transition["from_month"] + "->" + transition["to_month"]
    colors = np.where(transition["to_month_is_event"], "#c43c00", "#1f77b4")
    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    ax.bar(np.arange(len(transition)), transition["self_transition_rate"], color=colors)
    ax.axhline(transition["self_transition_rate"].mean(), color="black", linestyle="--", linewidth=1, label="mean")
    ax.set_xticks(np.arange(len(transition)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_ylabel("Self-transition rate")
    ax.set_title(f"EOA K{k} Monthly Persistence; Event-Adjacent Pairs Highlighted")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / f"k{k}_self_transition_event_pairs.png", dpi=220)
    plt.close(fig)


def plot_residual_heatmap(k: int, residuals: pd.DataFrame, out_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 5.8))
    data = residuals.to_numpy(dtype=float)
    vmax = np.nanmax(np.abs(data))
    im = ax.imshow(data, cmap="coolwarm", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(np.arange(len(residuals.columns)))
    ax.set_xticklabels([f"C{c}" for c in residuals.columns])
    ax.set_yticks(np.arange(len(residuals.index)))
    ax.set_yticklabels([f"C{c}" for c in residuals.index])
    ax.set_xlabel("To state")
    ax.set_ylabel("From state")
    ax.set_title(f"EOA K{k} Transition Residuals vs Independence")
    fig.colorbar(im, ax=ax, label="Pearson residual")
    fig.tight_layout()
    fig.savefig(out_dir / f"k{k}_transition_residual_heatmap.png", dpi=220)
    plt.close(fig)


def write_report(
    all_event_tests: pd.DataFrame,
    all_zscores: pd.DataFrame,
    all_two_step: pd.DataFrame,
    all_top_paths: pd.DataFrame,
) -> None:
    lines = [
        "# Academic Temporal Validation Pack",
        "",
        "## Purpose",
        "",
        "This package reformats the temporal analysis into paper-ready tests and visuals. It follows the same logic as the earlier six-cluster work: transition matrices, state stability, monthly composition shifts, and statistical checks against null or baseline behaviour.",
        "",
        "The report does not claim that external events caused wallet-state transitions. It tests whether event-adjacent months coincide with unusual transition behaviour, then reports the evidence cautiously.",
        "",
        "## Event Months Used As Candidate Explanatory Windows",
        "",
        EVENTS.to_markdown(index=False),
        "",
        "## Event-Adjacent Transition Tests",
        "",
        "Rank p-values compare an event-adjacent month pair with all 11 month pairs in 2022. Small values mean that the event-adjacent pair is unusually high or low relative to the observed year. This is a descriptive nonparametric test because the number of monthly pairs is small.",
        "",
        all_event_tests.to_markdown(index=False),
        "",
        "## Largest Monthly State-Share Z-Scores",
        "",
        all_zscores.reindex(all_zscores["z_score_vs_months"].abs().sort_values(ascending=False).index)
        .head(30)
        .to_markdown(index=False),
        "",
        "## Two-Step Return Null Tests",
        "",
        "The two-step test checks whether wallets that leave a state at month t+1 return to their original month-t state at month t+2 more often than expected after shuffling the t+2 states among wallets that left. This tests the temporary-deviation interpretation directly.",
        "",
        all_two_step.to_markdown(index=False),
        "",
        "## Strongest Off-Diagonal Transition Pathways",
        "",
        all_top_paths.to_markdown(index=False),
        "",
        "## Interpretation",
        "",
        "Across K4, K5, and K6, monthly wallet behaviour is neither fixed nor random. The transition matrices show moderate persistence, while the two-step return tests show that many wallets temporarily leave a behavioural state and then return more often than expected under shuffled future states.",
        "",
        "External events should be treated as candidate explanations, not causal conclusions. For example, May and June 2022 correspond to broad crypto-market stress around Terra and Celsius, September 2022 corresponds to the Ethereum Merge, and November 2022 corresponds to the FTX crisis. The correct paper wording is that these months provide plausible contextual windows for observed state-share and persistence changes, but causal attribution would require an explicit event-study design or control series.",
    ]
    (OUT_DIR / "academic_temporal_validation_pack.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    EVENTS.to_csv(OUT_DIR / "event_month_annotations.csv", index=False)
    event_tests = []
    zscores = []
    two_step_tests = []
    top_paths = []

    for k in [4, 5, 6]:
        out_dir = transition_dir(k)
        out_dir.mkdir(parents=True, exist_ok=True)

        l1 = transition_l1_changes(k)
        l1.to_csv(out_dir / f"k{k}_monthly_composition_change.csv", index=False)
        test = event_rank_tests(k)
        test.to_csv(out_dir / f"k{k}_event_adjacent_rank_tests.csv", index=False)
        event_tests.append(test)

        z = state_share_zscores(k)
        z.to_csv(out_dir / f"k{k}_state_share_zscores.csv", index=False)
        zscores.append(z)

        residual, expected = transition_residuals(k)
        residual.to_csv(out_dir / f"k{k}_transition_independence_residuals.csv")
        expected.to_csv(out_dir / f"k{k}_transition_independence_expected_counts.csv")

        two = two_step_null_test(k)
        two.to_csv(out_dir / f"k{k}_two_step_return_null_tests.csv", index=False)
        two_step_tests.append(two)

        paths = top_transition_pathways(k)
        paths.to_csv(out_dir / f"k{k}_top_off_diagonal_transition_pathways.csv", index=False)
        top_paths.append(paths)

        plot_state_shares(k, out_dir)
        plot_self_transition(k, out_dir)
        plot_residual_heatmap(k, residual, out_dir)

    all_event_tests = pd.concat(event_tests, ignore_index=True)
    all_zscores = pd.concat(zscores, ignore_index=True)
    all_two_step = pd.concat(two_step_tests, ignore_index=True)
    all_top_paths = pd.concat(top_paths, ignore_index=True)
    all_event_tests.to_csv(OUT_DIR / "event_adjacent_rank_tests_all_k.csv", index=False)
    all_zscores.to_csv(OUT_DIR / "state_share_zscores_all_k.csv", index=False)
    all_two_step.to_csv(OUT_DIR / "two_step_return_null_tests_all_k.csv", index=False)
    all_top_paths.to_csv(OUT_DIR / "top_off_diagonal_transition_pathways_all_k.csv", index=False)
    write_report(all_event_tests, all_zscores, all_two_step, all_top_paths)
    print(f"Saved academic temporal pack to: {OUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
