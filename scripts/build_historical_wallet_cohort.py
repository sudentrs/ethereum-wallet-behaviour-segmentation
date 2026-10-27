"""Versioned, budget-limited historical cohort builder; never overwrites baseline.

The cohort requires empty code at every pinned 2022 month-end snapshot.
Origination evidence is stored separately. Offline preparation is the default.
"""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.prepare_historical_exclusion_audit import addresses, sha256
from scripts.run_historical_exclusion_sample import parse_code
from src.validation.historical_monthly_code_check import RPC, rpc_url

FULL = (1 << 12) - 1
DEFINITION = "empty_code_at_all_12_pinned_2022_month_ends_v1"


def connect(path):
    db = sqlite3.connect(path)
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
      CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS population(
        address TEXT PRIMARY KEY, baseline_retained INTEGER NOT NULL,
        total_tx REAL NOT NULL, checked_mask INTEGER NOT NULL DEFAULT 0,
        code_mask INTEGER NOT NULL DEFAULT 0);
      CREATE TABLE IF NOT EXISTS observations(
        address TEXT NOT NULL REFERENCES population(address), month INTEGER NOT NULL,
        code_bytes INTEGER NOT NULL CHECK(code_bytes>=0), source TEXT NOT NULL,
        PRIMARY KEY(address,month), CHECK(month BETWEEN 1 AND 12));
      CREATE TABLE IF NOT EXISTS origination(
        address TEXT PRIMARY KEY REFERENCES population(address),
        transaction_hash TEXT NOT NULL, block_number INTEGER NOT NULL,
        timestamp_utc TEXT NOT NULL, source TEXT NOT NULL);
    """)
    return db


def record(db, address, month, size, source):
    if month not in range(1, 13) or size < 0 or int(size) != size:
        raise ValueError("Invalid historical code observation")
    old = db.execute("SELECT code_bytes FROM observations WHERE address=? AND month=?",
                     (address, month)).fetchone()
    if old:
        if old[0] != size:
            raise ValueError("Conflicting historical code evidence")
        return
    db.execute("INSERT INTO observations VALUES(?,?,?,?)", (address, month, size, source))
    bit = 1 << (month - 1)
    db.execute("UPDATE population SET checked_mask=checked_mask|?,code_mask=code_mask|? WHERE address=?",
               (bit, bit if size else 0, address))


def counts(db):
    row = db.execute("""SELECT count(*),sum(baseline_retained),
      sum(code_mask>0),sum(code_mask=0 AND checked_mask=?),
      sum(code_mask=0 AND checked_mask<>?) FROM population""", (FULL, FULL)).fetchone()
    return dict(zip(["raw_population", "baseline_retained", "snapshot_excluded",
                     "snapshot_included", "snapshot_unresolved"], map(lambda v: int(v or 0), row)))


def initialize(db, design, design_path):
    marker = db.execute("SELECT value FROM metadata WHERE key='population_ready'").fetchone()
    identity = {"definition": DEFINITION, "design_sha256": sha256(design_path)}
    old = db.execute("SELECT value FROM metadata WHERE key='identity'").fetchone()
    if old and json.loads(old[0]) != identity:
        raise ValueError("Cohort identity changed; use a new version directory")
    if marker:
        return
    if db.execute("SELECT count(*) FROM population").fetchone()[0]:
        raise ValueError("Incomplete population setup; use a fresh version directory")
    inputs = design["inputs_sha256"]
    raw_path = ROOT / "data/processed/wallet_kmeans6_expanded_daily_features.csv"
    paths = [raw_path] + [ROOT / f"results/eoa_only_kmeans{k}/wallet_eoa_only_kmeans_clusters.csv" for k in (4, 5, 6)]
    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        expected = next((v for k, v in inputs.items() if k.replace("\\", "/") == relative), None)
        if not expected or sha256(path) != expected:
            raise ValueError(f"Input differs from validated audit frame: {path.name}")
    retained = set(addresses(pd.read_csv(paths[1], usecols=["wallet"], dtype=str).wallet))
    if len(retained) != design["retained_addresses"]:
        raise ValueError("Retained size mismatch")
    print("Building versioned full-population registry...", flush=True)
    with db:
        db.execute("INSERT OR REPLACE INTO metadata VALUES('identity',?)", (json.dumps(identity),))
        for chunk in pd.read_csv(raw_path, usecols=["wallet", "total_tx"], dtype={"wallet": str}, chunksize=100000):
            normalized = addresses(chunk.wallet)
            rows = [(a, int(a in retained), float(n)) for a, n in zip(normalized, chunk.total_tx)]
            if any(not pd.notna(n) or n < 0 or n == float('inf') for _, _, n in rows):
                raise ValueError("Invalid activity count")
            db.executemany("INSERT INTO population(address,baseline_retained,total_tx) VALUES(?,?,?)", rows)
        result = counts(db)
        if result["raw_population"] != design["raw_addresses"] or result["baseline_retained"] != len(retained):
            raise ValueError("Population reconstruction mismatch")
        db.execute("CREATE INDEX IF NOT EXISTS queue_order ON population(baseline_retained,address)")
        db.execute("INSERT INTO metadata VALUES('population_ready','true')")


def import_evidence(db, pins):
    cache_path = ROOT / "results_v3/historical_exclusion_audit_results/address_month_cache.csv"
    with db:
        for item in pd.read_csv(cache_path).itertuples(index=False):
            month = int(item.month.split("-")[1])
            pin = pins.loc[pins.month.eq(item.month)].iloc[0]
            if int(item.block_number) != int(pin.block_number) or item.block_hash != pin.block_hash:
                raise ValueError("Cached observation has inconsistent pinned block")
            record(db, item.address, month, int(item.code_bytes), str(cache_path.relative_to(ROOT)))
        paths = [ROOT / "data/interim/excluded_code_type_audit/historical_origination_audit.csv",
                 ROOT / "data/interim/historical_exclusion_probability_origination/historical_origination_audit.csv"]
        for path in paths:
            frame = pd.read_csv(path)
            for item in frame.loc[frame.status.eq("verified_top_level_sender_in_2022")].itertuples(index=False):
                # Preserve transaction-time evidence separately; do not invent month-end checks.
                old = db.execute("SELECT transaction_hash FROM origination WHERE address=?", (item.address,)).fetchone()
                if old:
                    continue
                db.execute("INSERT INTO origination VALUES(?,?,?,?,?)", (
                    item.address, item.transaction_hash, int(item.block_number), item.timestamp_utc,
                    str(path.relative_to(ROOT))))


def export_status(db, version, report, pin_path, rpc_queries):
    report.mkdir(parents=True, exist_ok=True)
    result = counts(db)
    result.update(definition=DEFINITION, new_code_queries_this_run=rpc_queries,
                  verified_origination_addresses=db.execute("SELECT count(*) FROM origination").fetchone()[0],
                  complete=result["snapshot_unresolved"] == 0,
                  pins_sha256=sha256(pin_path),
                  note="Partial evidence registry, not a corrected full EOA cohort, until complete.")
    result["builder_sha256"] = sha256(Path(__file__).resolve())
    result["maximum_remaining_address_month_checks"] = db.execute(
        "SELECT sum(12-((checked_mask&1)>0)-((checked_mask&2)>0)-((checked_mask&4)>0)-((checked_mask&8)>0)-((checked_mask&16)>0)-((checked_mask&32)>0)-((checked_mask&64)>0)-((checked_mask&128)>0)-((checked_mask&256)>0)-((checked_mask&512)>0)-((checked_mask&1024)>0)-((checked_mask&2048)>0)) FROM population WHERE code_mask=0 AND checked_mask<>?", (FULL,)).fetchone()[0] or 0
    for name, query in [
        ("verified_snapshot_subset.csv", f"SELECT address,baseline_retained,total_tx FROM population WHERE code_mask=0 AND checked_mask={FULL} ORDER BY address"),
        ("transaction_origination_evidence.csv", "SELECT * FROM origination ORDER BY address")]:
        pd.read_sql_query(query, db).to_csv(report / name, index=False)
    (report / "cohort_status.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    lines = ["# Historical cohort v1: partial evidence registry", "",
             f"Original addresses: {result['raw_population']:,}.",
             f"Confirmed snapshot inclusions: {result['snapshot_included']:,}.",
             f"Confirmed snapshot exclusions: {result['snapshot_excluded']:,}.",
             f"Unresolved addresses: {result['snapshot_unresolved']:,}.",
             f"Transaction-origination positives (separate outcome): {result['verified_origination_addresses']:,}.", "",
             "The origination inventory combines 33 earlier cases with 67 probability-sample cases. Transaction-time evidence does not invent missing monthly observations.", "",
             "verified_snapshot_subset.csv is NOT a corrected full cohort or a suitable substitute for a full-population rerun. No annual/temporal/network results have been recomputed on a completed historical cohort.", "",
             "See docs/HISTORICAL_COHORT_REBUILD.md for resume commands, query limits and completion criteria."]
    (report / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if result["complete"]:
        target = version / "cohort_members.csv"
        with target.open("w", newline="", encoding="ascii") as stream:
            writer = csv.writer(stream)
            writer.writerow(["wallet"])
            writer.writerows((a[2:],) for (a,) in db.execute(
                "SELECT address FROM population WHERE code_mask=0 ORDER BY address"))
        ready = dict(result, cohort_file=str(target), cohort_sha256=sha256(target))
        (version / "COHORT_READY.json").write_text(json.dumps(ready, indent=2))
    print(json.dumps(result, indent=2), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version-dir", default="data/interim/historical_wallet_cohort_v1")
    parser.add_argument("--report-dir", default="results_v3/historical_wallet_cohort_v1")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--max-code-queries", type=int, default=1000)
    parser.add_argument("--env-file", type=Path)
    args = parser.parse_args()
    if args.max_code_queries < 1:
        parser.error("max-code-queries must be positive")
    version, report = ROOT / args.version_dir, ROOT / args.report_dir
    version.mkdir(parents=True, exist_ok=True)
    design_path = ROOT / "results_v3/historical_exclusion_audit_design/design.json"
    pin_path = ROOT / "results_v3/historical_exclusion_audit_results/month_end_blocks.csv"
    pins = pd.read_csv(pin_path)
    if pins.month.tolist() != [f"2022-{m:02d}" for m in range(1, 13)]:
        raise ValueError("Invalid pinned months")
    with connect(version / "registry.sqlite") as db:
        initialize(db, json.loads(design_path.read_text()), design_path)
        pin_hash = sha256(pin_path)
        old = db.execute("SELECT value FROM metadata WHERE key='pins_sha256'").fetchone()
        if old and old[0] != pin_hash:
            raise ValueError("Pinned blocks changed; use a new version directory")
        db.execute("INSERT OR REPLACE INTO metadata VALUES('pins_sha256',?)", (pin_hash,))
        db.commit()
        import_evidence(db, pins)
        used = 0
        try:
            if args.execute:
                if args.env_file:
                    for line in args.env_file.read_text(encoding="utf-8-sig").splitlines():
                        key, sep, value = line.strip().removeprefix("export ").partition("=")
                        if sep and key.strip() == "ETH_RPC_URL":
                            os.environ["ETH_RPC_URL"] = value.strip().strip("\"'")
                rpc = RPC(rpc_url(), 0.3)
                if rpc.call("eth_chainId", []) != "0x1":
                    raise ValueError("Expected Ethereum Mainnet")
                for pin in pins.itertuples(index=False):
                    if rpc.call("eth_getBlockByNumber", [hex(pin.block_number), False])["hash"] != pin.block_hash:
                        raise ValueError("Pinned block hash mismatch")
                # Newest snapshots first; one nonempty observation is enough to
                # reject the ALL-empty definition without querying other months.
                for pin in pins.iloc[::-1].itertuples(index=False):
                    month = int(pin.month.split("-")[1])
                    bit = 1 << (month - 1)
                    cursor = db.execute("SELECT address FROM population WHERE code_mask=0 AND (checked_mask&?)=0 ORDER BY baseline_retained,address", (bit,))
                    while used < args.max_code_queries:
                        batch = [r[0] for r in cursor.fetchmany(min(20, args.max_code_queries-used))]
                        if not batch:
                            break
                        values = rpc.batch([("eth_getCode", [a, hex(pin.block_number)]) for a in batch])
                        sizes = [parse_code(code) for code in values]
                        with db:
                            for address, size in zip(batch, sizes):
                                record(db, address, month, size, "rpc_pinned_month_end")
                        used += len(batch)
                        print(f"Budget {used}/{args.max_code_queries}; month {pin.month}", flush=True)
                    cursor.close()
                    if used >= args.max_code_queries:
                        break
        finally:
            export_status(db, version, report, pin_path, used)


if __name__ == "__main__":
    main()
