"""Run and package the frozen Phase 1 calibration grid.

The default is a dry run. Use ``--execute`` to train. Calibration metrics are
retained only to validate the execution chain and must not be used as research
evidence or for model selection.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
import torch


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "reproduction/configs/phase1_modern_baselines.json"
MANIFEST_PATH = ROOT / "reproduction/results/phase1/A_calibration.manifest.csv"
REGISTRY_PATH = ROOT / "reproduction/results/dataset_registry.csv"
PACKAGE_ROOT = ROOT / "reproduction/results/phase1/calibration"
LOG_ROOT = ROOT / "reproduction/logs/phase1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def run_id(index: int, row: dict[str, str]) -> str:
    return (
        f"A{index:02d}_{row['asset']}_{row['model']}_"
        f"h{row['horizon']}_s{row['seed']}"
    )


def build_command(row: dict[str, str], registry: dict[str, dict[str, str]], config: dict) -> list[str]:
    common = config["common"]
    data_file = Path(registry[row["asset"]]["file"])
    command = [
        sys.executable,
        "run.py",
        "--task_name", "long_term_forecast",
        "--is_training", "1",
        "--model_id", f"phase1A_{row['asset']}_h{row['horizon']}_s{row['seed']}",
        "--model", row["model"],
        "--data", "custom",
        "--root_path", str(data_file.parent).replace("\\", "/") + "/",
        "--data_path", data_file.name,
        "--features", "MS",
        "--target", "Close",
        "--freq", "b",
        "--seq_len", str(common["seq_len"]),
        "--label_len", str(common["label_len"]),
        "--pred_len", row["horizon"],
        "--enc_in", str(common["enc_in"]),
        "--dec_in", str(common["dec_in"]),
        "--c_out", str(common["c_out"]),
        "--d_model", str(common["d_model"]),
        "--n_heads", str(common["n_heads"]),
        "--e_layers", str(common["e_layers"]),
        "--d_layers", str(common["d_layers"]),
        "--d_ff", str(common["d_ff"]),
        "--moving_avg", str(common["moving_avg"]),
        "--factor", str(common["factor"]),
        "--dropout", str(common["dropout"]),
        "--embed", common["embed"],
        "--train_epochs", str(common["train_epochs"]),
        "--batch_size", str(common["batch_size"]),
        "--patience", str(common["patience"]),
        "--learning_rate", str(common["learning_rate"]),
        "--lradj", common["lradj"],
        "--rand_seed", row["seed"],
        "--num_workers", "0",
        "--no_use_gpu",
        "--des", "phase1A_calibration",
        "--result_log", "reproduction/logs/phase1/calibration_result_log.txt",
    ]
    if common.get("deterministic"):
        command.append("--deterministic")
    return command


def verify_existing_receipt(destination: Path) -> bool:
    receipt_path = destination / "receipt.json"
    if not receipt_path.is_file():
        return False
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    for name, expected in receipt["sha256"].items():
        path = destination / name
        if not path.is_file() or sha256(path) != expected:
            raise RuntimeError(f"existing receipt hash mismatch: {path}")
    return True


def find_setting(row: dict[str, str]) -> str:
    model_id = f"phase1A_{row['asset']}_h{row['horizon']}_s{row['seed']}"
    candidates = [
        path for path in (ROOT / "results").glob(f"*{model_id}*")
        if path.is_dir() and f"_{row['model']}_custom_" in path.name
    ]
    if len(candidates) != 1:
        raise RuntimeError(f"expected one result directory for {model_id}/{row['model']}, found {len(candidates)}")
    return candidates[0].name


def parse_diagnostics(log_text: str) -> dict[str, float | int | None]:
    lines = [line for line in log_text.splitlines() if line.startswith("mse:")]
    if not lines:
        raise RuntimeError("run log has no final metric line")
    line = lines[-1]

    def number(pattern: str, cast=float):
        match = re.search(pattern, line)
        return cast(match.group(1)) if match else None

    return {
        "train_time_seconds": number(r"train_time:([0-9.]+)s"),
        "inference_ms_per_sample": number(r"inference_time:([0-9.]+)ms/sample"),
        "parameter_count": number(r"params:([0-9]+)", int),
        "gpu_peak_memory_mb": number(r"gpu_mem_peak_mb:([0-9.]+)"),
    }


def package_run(
    index: int,
    row: dict[str, str],
    registry: dict[str, dict[str, str]],
    config: dict,
    command: list[str],
    log_path: Path,
    git_commit: str,
) -> Path:
    setting = find_setting(row)
    result_dir = ROOT / "results" / setting
    checkpoint = ROOT / "checkpoints" / setting / "checkpoint.pth"
    required = {
        "pred.npy": result_dir / "pred.npy",
        "true.npy": result_dir / "true.npy",
        "metrics.npy": result_dir / "metrics.npy",
        "checkpoint.pth": checkpoint,
        "run.log": log_path,
    }
    missing = [str(path) for path in required.values() if not path.is_file()]
    if missing:
        raise RuntimeError("missing run artifacts: " + ", ".join(missing))

    pred = np.load(required["pred.npy"])
    true = np.load(required["true.npy"])
    metrics = np.load(required["metrics.npy"])
    expected_shape = (pred.shape[0], int(row["horizon"]), 1)
    if pred.shape != expected_shape or true.shape != expected_shape:
        raise RuntimeError(f"unexpected pred/true shapes: {pred.shape} / {true.shape}")
    if metrics.shape != (6,):
        raise RuntimeError(f"unexpected metrics shape: {metrics.shape}")
    if not all(np.isfinite(array).all() for array in (pred, true, metrics)):
        raise RuntimeError("non-finite value in calibration arrays")

    destination = PACKAGE_ROOT / run_id(index, row)
    if destination.exists() and not verify_existing_receipt(destination):
        raise RuntimeError(f"refusing to overwrite incomplete destination: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    for name, source in required.items():
        shutil.copy2(source, destination / name)

    copied_hashes = {name: sha256(destination / name) for name in required}
    environment = {
        "python": ".".join(str(value) for value in sys.version_info[:3]),
        "torch": torch.__version__,
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
        "device": "cpu",
    }
    receipt = {
        "status": "calibration_pass",
        "scientific_use": "none; execution calibration only",
        "protocol_version": config["protocol_version"],
        "git_commit": git_commit,
        "asset": row["asset"],
        "dataset_sha256": registry[row["asset"]]["sha256"],
        "model": row["model"],
        "horizon": int(row["horizon"]),
        "seed": int(row["seed"]),
        "split_mode": row["split_mode"],
        "command": subprocess.list2cmdline(command),
        "environment": environment,
        "shapes": {
            "pred.npy": list(pred.shape),
            "true.npy": list(true.shape),
            "metrics.npy": list(metrics.shape),
        },
        "all_arrays_finite": True,
        "sha256": copied_hashes,
        "diagnostics": parse_diagnostics(log_path.read_text(encoding="utf-8", errors="replace")),
    }
    (destination / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return destination


def validate_source_state() -> str:
    tracked = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if tracked:
        raise RuntimeError("tracked worktree changes must be committed before calibration")
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="run training; default is dry-run")
    parser.add_argument("--limit", type=int, default=None, help="maximum number of missing fits to run")
    parser.add_argument("--only-asset", choices=["BOND10Y", "BONDETF", "CITICSEC"])
    parser.add_argument("--only-model")
    args = parser.parse_args()

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    rows = load_csv(MANIFEST_PATH)
    registry = {row["asset"]: row for row in load_csv(REGISTRY_PATH)}
    if len(rows) != 15:
        raise RuntimeError(f"expected 15 calibration rows, found {len(rows)}")

    selected: list[tuple[int, dict[str, str], Path]] = []
    for index, row in enumerate(rows, start=1):
        if args.only_asset and row["asset"] != args.only_asset:
            continue
        if args.only_model and row["model"] != args.only_model:
            continue
        data_path = ROOT / registry[row["asset"]]["file"]
        if sha256(data_path) != registry[row["asset"]]["sha256"]:
            raise RuntimeError(f"dataset hash mismatch: {row['asset']}")
        destination = PACKAGE_ROOT / run_id(index, row)
        if verify_existing_receipt(destination):
            print(f"SKIP verified {destination.name}")
            continue
        selected.append((index, row, destination))

    if args.limit is not None:
        selected = selected[:args.limit]
    print(f"missing calibration fits selected: {len(selected)}")
    for index, row, _ in selected:
        print("DRY" if not args.execute else "RUN", run_id(index, row))
    if not args.execute:
        return 0

    git_commit = validate_source_state()
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    for index, row, _ in selected:
        identifier = run_id(index, row)
        command = build_command(row, registry, config)
        log_path = LOG_ROOT / f"{identifier}.log"
        print(f"START {identifier}")
        started = time.time()
        environment = dict(os.environ)
        environment["PYTHONUNBUFFERED"] = "1"
        with log_path.open("w", encoding="utf-8", newline="") as log:
            completed = subprocess.run(
                command,
                cwd=ROOT,
                env=environment,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
            )
        if completed.returncode != 0:
            raise RuntimeError(f"{identifier} failed with exit code {completed.returncode}; see {log_path}")
        destination = package_run(index, row, registry, config, command, log_path, git_commit)
        print(f"PASS {identifier} elapsed={time.time() - started:.1f}s package={destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
