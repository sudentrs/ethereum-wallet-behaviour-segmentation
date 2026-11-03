"""Write a provenance manifest by auditing already-fitted annual model artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fit-dir", type=Path, required=True)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--wallet-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    feature_columns = [c for c in pd.read_csv(args.wallet_source, nrows=0).columns if c not in {"wallet", "cluster"}]
    wallet_count = sum(len(chunk) for chunk in pd.read_csv(args.wallet_source, usecols=["wallet"], chunksize=200_000))
    labels = sorted(args.fit_dir.glob("k*_seed*_labels.npy"))
    runs = []
    for path in labels:
        stem = path.stem.replace("_labels", "")
        k_part, seed_part = stem.split("_seed")
        k, seed = int(k_part[1:]), int(seed_part)
        vector = np.load(path, mmap_mode="r")
        if vector.shape != (wallet_count,) or not np.isin(vector, np.arange(k)).all():
            raise ValueError(f"Invalid label artifact: {path}")
        runs.append({"k": k, "seed": seed, "labels_file": path.name, "labels_sha256": sha256(path)})
    if not runs:
        raise ValueError("No annual label artifacts found")
    fit_path = args.fit_dir / 'fit_manifest.json'
    fit_settings = json.loads(fit_path.read_text()) if fit_path.exists() else None
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({
        "purpose": "audited provenance for the annual K2--K6 count/activity models",
        "matrix_file": str(args.matrix), "matrix_sha256": sha256(args.matrix),
        "wallet_source": str(args.wallet_source), "wallet_source_sha256": sha256(args.wallet_source),
        "wallet_count": wallet_count, "feature_columns": feature_columns,
        "runs": runs, "scikit_learn": sklearn.__version__, "python": platform.python_version(),
        "fit_settings": fit_settings,
        "fit_manifest_sha256": sha256(fit_path) if fit_path.exists() else None,
        "note": "Audited label files, feature order and input hashes. Full estimator settings are embedded when a fit manifest is available."
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
