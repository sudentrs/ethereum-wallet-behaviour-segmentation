"""Apply Holm correction to a completed monthly network-null summary."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def holm(p_values: np.ndarray) -> np.ndarray:
    order = np.argsort(p_values)
    adjusted = np.empty(len(p_values), dtype=float)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, (len(p_values) - rank) * p_values[index])
        adjusted[index] = min(1.0, running)
    return adjusted


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    summary = pd.read_csv(args.summary)
    summary["p_value_upper_holm_12"] = holm(summary["p_value_upper"].to_numpy(float))
    summary.to_csv(args.summary, index=False)
    significant = int((summary["p_value_upper_holm_12"] < 0.05).sum())
    (args.summary.parent / "multiple_testing_note.md").write_text(
        "# Multiple-Testing Correction\n\n"
        "The twelve monthly upper-tail network-null p-values were corrected with the Holm procedure.\n\n"
        f"- Months with Holm-adjusted p-value below 0.05: `{significant}/12`.\n"
        f"- Range of adjusted p-values: `{summary['p_value_upper_holm_12'].min():.4f}`--`{summary['p_value_upper_holm_12'].max():.4f}`.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
