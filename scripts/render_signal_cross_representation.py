"""Render the manuscript's vector heatmaps from the frozen overlap table."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def main():
    source = ROOT / "results_v3/year_end_2022_count_cohort/signals/annual_signal_overlap.csv"
    overlap = pd.read_csv(source)
    plt.rcParams.update({"font.family": "serif", "font.size": 10, "pdf.fonttype": 42})
    figure, axes = plt.subplots(1, 2, figsize=(7.16, 2.55))
    boundaries = np.arange(4) - 0.5
    for axis, representation in zip(axes, ("time", "frequency")):
        selected = overlap[
            overlap.annual_k.eq(3)
            & overlap.signal_k.eq(3)
            & overlap.representation.eq(representation)
        ]
        matrix = selected.pivot(
            index="annual_cluster", columns="signal_cluster", values="row_share"
        ).reindex(index=range(3), columns=range(3))
        assert matrix.shape == (3, 3) and not matrix.isna().any().any()
        np.testing.assert_allclose(matrix.sum(axis=1), 1)
        axis.pcolormesh(
            boundaries, boundaries, matrix.to_numpy(),
            vmin=0, vmax=1, cmap="Blues", shading="flat", rasterized=False,
        )
        for (row, column), value in np.ndenumerate(matrix.to_numpy()):
            axis.text(
                column, row, f"{value:.2f}", ha="center", va="center",
                color="white" if value > 0.6 else "black",
            )
        axis.set(
            title=f"Annual K3 vs {representation} K3",
            xlabel="Signal cluster", ylabel="Annual cluster",
            xticks=range(3), yticks=range(3),
            xlim=(-0.5, 2.5), ylim=(2.5, -0.5),
        )
    figure.tight_layout(pad=0.6, w_pad=1.4)
    destination = ROOT / "overleaf/figures_current/signal_cross_representation.pdf"
    figure.savefig(destination, metadata={"CreationDate": None, "ModDate": None})
    plt.close(figure)
    print(destination)


if __name__ == "__main__":
    main()
