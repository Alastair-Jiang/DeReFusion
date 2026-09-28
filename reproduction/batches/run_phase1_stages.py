"""Shared, fail-closed launcher for Phase 1 stages B/C/D.

Dry-run is the default. Training requires an explicit, versioned authorization
record and a matching worker environment fingerprint. Attempts are immutable.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
PHASE = ROOT / "reproduction/results/phase1"
CONFIG = ROOT / "reproduction/configs/phase1_modern_baselines.json"
REGISTRY = ROOT / "reproduction/results/dataset_registry.csv"
CONTRACT = PHASE / "phase1_data_contract.csv"
SPLITS = PHASE / "phase1_split_manifest.csv"
KEYS = PHASE / "phase1_prediction_keys.csv.gz"
MANIFESTS = {
    "B_screen": PHASE / "B_screen.manifest.csv",
    "C_confirmation": PHASE / "C_confirmation.manifest.csv",
    "D_temporal_robustness": PHASE / "D_temporal_robustness.manifest.csv",
}
OUTPUT = PHASE / "attempts"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def logical_id(row: dict[str, str]) -> str:
    origin = f"_o{row['origin']}" if row["stage"] == "D_temporal_robustness" else ""
    return f"{row['stage']}_{row['asset']}_{row['model']}_h{row['horizon']}_s{row['seed']}{origin}"


def canonical_hash(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_preflight(selected: list[dict[str, str]]) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]], list[str]]:
    issues: list[str] = []
    registry = {r["asset"]: r for r in rows(REGISTRY)}
    contract = {r["series_group_id"]: r for r in rows(CONTRACT)}
    split_rows = rows(SPLITS)
    split_index = {(r["asset"], r["forecast_horizon"], r["split_mode"], r["train_end"], r["val_end"], r["test_end"]): r for r in split_rows}
    if len(split_index) != len(split_rows):
        issues.append("split manifest has duplicate split identities")
    data_ids: dict[str, dict[str, str]] = {}
    for asset in sorted({r["asset"] for r in selected}):
        reg = registry.get(asset)
        con = contract.get(asset)
        if not reg or not con:
            issues.append(f"{asset}: missing registry or data-contract record")
            continue
        data_path = ROOT / reg["file"]
        if not data_path.is_file() or sha256(data_path) != reg["sha256"] or con["sha256"] != reg["sha256"]:
            issues.append(f"{asset}: source bytes do not match both frozen registry and contract")
        if con["status"] != "eligible":
            issues.append(f"{asset}: data contract status is {con['status']}")
        data_ids[asset] = reg
    for row in selected:
        key = (row["asset"], row["horizon"], row["split_mode"], row["train_end"], row["val_end"], row["test_end"])
        split = split_index.get(key)
        if not split:
            issues.append(f"{logical_id(row)}: no exact split-manifest match")
            continue
        if row["stage"] not in split["stage_scope"].split(";"):
            issues.append(f"{logical_id(row)}: stage not included in split scope")
        if int(split["prediction_point_count"]) != int(split["window_count"]) * int(row["horizon"]):
            issues.append(f"{logical_id(row)}: prediction-key cardinality mismatch")
        if split["split_manifest_id"] not in {x["split_manifest_id"] for x in split_rows}:
            issues.append(f"{logical_id(row)}: unknown split id")
    if not KEYS.is_file():
        issues.append("precomputed prediction-key file is missing")
    elif not SPLITS.is_file() or not CONTRACT.is_file():
        issues.append("preflight artifacts are incomplete")
    else:
        needed = {v["split_manifest_id"]: v for v in split_index.values()
                  if any((r["asset"], r["horizon"], r["split_mode"], r["train_end"], r["val_end"], r["test_end"])
                         == (v["asset"], v["forecast_horizon"], v["split_mode"], v["train_end"], v["val_end"], v["test_end"])
                         for r in selected)}
        digests = {split_id: hashlib.sha256() for split_id in needed}
        counts = {split_id: 0 for split_id in needed}
        with gzip.open(KEYS, "rt", encoding="utf-8", newline="") as stream:
            for key in csv.DictReader(stream):
                split_id = key["split_manifest_id"]
                if split_id in needed:
                    digests[split_id].update((key["key_hash"] + "\n").encode("ascii"))
                    counts[split_id] += 1
        for split_id, split in needed.items():
            if counts[split_id] != int(split["prediction_point_count"]):
                issues.append(f"{split_id}: key row count differs from split manifest")
            if digests[split_id].hexdigest() != split["prediction_keys_sha256"]:
                issues.append(f"{split_id}: key hash differs from split manifest")
    return data_ids, split_index, issues


def build_command(row: dict[str, str], common: dict, registry_row: dict[str, str], attempt: int, device: str) -> list[str]:
    data = ROOT / registry_row["file"]
    model_id = f"{logical_id(row)}__attempt-{attempt:02d}"
    cmd = [sys.executable, "run.py", "--task_name", "long_term_forecast", "--is_training", "1",
           "--model_id", model_id, "--model", row["model"], "--data", "custom",
           "--root_path", data.parent.as_posix() + "/", "--data_path", data.name,
           "--features", "MS", "--target", "Close", "--freq", "b",
           "--seq_len", str(common["seq_len"]), "--label_len", str(common["label_len"]),
           "--pred_len", row["horizon"], "--enc_in", str(common["enc_in"]),
           "--dec_in", str(common["dec_in"]), "--c_out", str(common["c_out"]),
           "--d_model", str(common["d_model"]), "--n_heads", str(common["n_heads"]),
           "--e_layers", str(common["e_layers"]), "--d_layers", str(common["d_layers"]),
           "--d_ff", str(common["d_ff"]), "--moving_avg", str(common["moving_avg"]),
           "--factor", str(common["factor"]), "--dropout", str(common["dropout"]),
           "--embed", common["embed"], "--train_epochs", str(common["train_epochs"]),
           "--batch_size", str(common["batch_size"]), "--patience", str(common["patience"]),
           "--learning_rate", str(common["learning_rate"]), "--lradj", common["lradj"],
           "--rand_seed", row["seed"], "--num_workers", "0", "--des", "phase1_frozen",
           "--result_log", f"reproduction/logs/phase1/{row['stage']}.txt"]
    if row["split_mode"] == "dates":
        cmd += ["--split_mode", "dates", "--train_end", row["train_end"],
                "--val_end", row["val_end"], "--test_end", row["test_end"]]
    if common.get("deterministic"):
        cmd.append("--deterministic")
    if device == "cuda":
        cmd += ["--gpu_type", "cuda", "--gpu", "0"]
    else:
        cmd.append("--no_use_gpu")
    return cmd


def validate_authorization(path: Path, env_path: Path, stage_set: set[str], device: str) -> tuple[dict, str]:
    authorization = json.loads(path.read_text(encoding="utf-8"))
    fingerprint = json.loads(env_path.read_text(encoding="utf-8"))
    expected = {"authorization_version": "phase1-execution-auth/v1", "protocol_version": "phase1-v1.1-2026-09-19"}
    for key, value in expected.items():
        if authorization.get(key) != value:
            raise RuntimeError(f"authorization {key} must equal {value!r}")
    if not stage_set or stage_set - set(authorization.get("stages", [])):
        raise RuntimeError("authorization does not explicitly cover every selected stage")
    if authorization.get("execution_device") != device:
        raise RuntimeError("authorization execution_device does not match requested device")
    if not authorization.get("approved_by") or not authorization.get("approved_at_utc") or not authorization.get("decision_record"):
        raise RuntimeError("authorization must identify approver, time, and decision record")
    expected_commit = authorization.get("git_commit")
    actual_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if expected_commit != actual_commit:
        raise RuntimeError("authorization git_commit does not match current source")
    env_hash = sha256(env_path)
    if authorization.get("environment_fingerprint_sha256") != env_hash:
        raise RuntimeError("worker environment fingerprint does not match authorization")
    observed = fingerprint.get("observed", fingerprint)
    pinned = {"python": "3.11.15", "torch": "2.5.1+cu121", "torch_cuda": "12.1",
              "numpy": "2.1.2", "pandas": "2.3.3", "scikit_learn": "1.7.2"}
    if fingerprint.get("mismatches", {}) or any(observed.get(k) != v for k, v in pinned.items()):
        raise RuntimeError("worker environment does not match the frozen Python/PyTorch lock")
    if device == "cuda":
        if observed.get("cuda_available") is not True:
            raise RuntimeError("CUDA is not available in the environment fingerprint")
        if authorization.get("gpu_model") not in observed.get("gpu_names", []):
            raise RuntimeError("authorized GPU model does not match worker fingerprint")
    return authorization, env_hash


def split_for(row: dict[str, str]) -> dict[str, str]:
    for split in rows(SPLITS):
        if (split["asset"], split["forecast_horizon"], split["split_mode"], split["train_end"], split["val_end"], split["test_end"]) == (
            row["asset"], row["horizon"], row["split_mode"], row["train_end"], row["val_end"], row["test_end"]
        ):
            return split
    raise RuntimeError(f"no split record for {logical_id(row)}")


def expected_truth(row: dict[str, str], split: dict[str, str], common: dict, data_path: Path) -> np.ndarray:
    frame = pd.read_csv(data_path)
    dates = pd.to_datetime(frame["date"], errors="raise")
    if row["split_mode"] == "ratio":
        train_stop = int(len(frame) * 0.7)
        test_rows = int(len(frame) * 0.2)
        test_start, test_stop = len(frame) - test_rows, len(frame)
    else:
        train_stop = int(dates.searchsorted(pd.Timestamp(row["train_end"]), side="left"))
        test_start = int(dates.searchsorted(pd.Timestamp(row["val_end"]), side="left"))
        test_stop = int(dates.searchsorted(pd.Timestamp(row["test_end"]), side="left"))
    ordered = frame[["Open", "High", "Low", "Close"]].to_numpy(dtype=np.float64)
    scaler = StandardScaler().fit(ordered[:train_stop])
    scaled_close = scaler.transform(ordered)[:, -1]
    seq_len, horizon = int(common["seq_len"]), int(row["horizon"])
    first_target = test_start
    windows = test_stop - test_start - horizon + 1
    if windows != int(split["window_count"]):
        raise RuntimeError(f"window count mismatch for {logical_id(row)}")
    expected = np.stack([scaled_close[first_target + i:first_target + i + horizon] for i in range(windows)])
    return expected[..., None]


def package_attempt(row: dict[str, str], destination: Path, command: list[str], log_path: Path,
                    setting: str, auth: dict, env_hash: str, common: dict, registry_row: dict[str, str]) -> None:
    result_dir = ROOT / "results" / setting
    checkpoint = ROOT / "checkpoints" / setting / "checkpoint.pth"
    source = {"pred.npy": result_dir / "pred.npy", "true.npy": result_dir / "true.npy",
              "metrics.npy": result_dir / "metrics.npy", "checkpoint.pth": checkpoint, "run.log": log_path}
    missing = [str(p) for p in source.values() if not p.is_file()]
    if missing:
        raise RuntimeError("required output missing; attempt retained as incomplete: " + ", ".join(missing))
    if not destination.is_dir():
        raise RuntimeError(f"attempt directory is missing: {destination}")
    running_receipt = destination / "receipt.json"
    if not running_receipt.is_file() or json.loads(running_receipt.read_text(encoding="utf-8")).get("status") != "running":
        raise RuntimeError(f"attempt is not in the expected running state: {destination}")
    split = split_for(row)
    pred, true, metrics = (np.load(source[n], allow_pickle=False) for n in ("pred.npy", "true.npy", "metrics.npy"))
    wanted = expected_truth(row, split, common, ROOT / registry_row["file"])
    if pred.shape != wanted.shape or true.shape != wanted.shape:
        raise RuntimeError(f"prediction/target shape does not cover frozen key universe: {pred.shape}, {true.shape}, expected {wanted.shape}")
    if not np.isfinite(pred).all() or not np.isfinite(true).all() or not np.isfinite(metrics).all():
        raise RuntimeError("non-finite output; attempt retained and flagged")
    if not np.allclose(true, wanted, rtol=2e-5, atol=2e-6):
        raise RuntimeError("true.npy does not align with frozen test targets; attempt retained and flagged")
    destination.mkdir(parents=True)
    for name, path in source.items():
        (destination / name).write_bytes(path.read_bytes())
    hashes = {name: sha256(destination / name) for name in source}
    receipt = {"logical_run_id": logical_id(row), "attempt": 1, "attempt_id": destination.name,
               "protocol_version": row["protocol_version"], "stage": row["stage"], "status": "completed_unreviewed",
               "scientific_use": "not interpreted; pending intake and stage gate review",
               "authorization_record": auth.get("decision_record"), "authorization_commit": auth["git_commit"],
               "environment_fingerprint_sha256": env_hash, "dataset_sha256": registry_row["sha256"],
               "split_manifest_id": split["split_manifest_id"], "prediction_keys_sha256": split["prediction_keys_sha256"],
               "execution_device": command_device(command),
               "config_fingerprint": canonical_hash({"row": row, "common": common, "device": command_device(command)}),
               "command": subprocess.list2cmdline(command), "created_at_utc": datetime.now(timezone.utc).isoformat(),
               "shapes": {"pred.npy": list(pred.shape), "true.npy": list(true.shape), "metrics.npy": list(metrics.shape)},
               "sha256": hashes}
    running_receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def command_device(command: list[str]) -> str:
    return "cuda" if "--gpu_type" in command else "cpu"


def completed_attempt(path: Path, row: dict[str, str], split: dict[str, str], expected_config: str) -> bool:
    receipt_path = path / "receipt.json"
    if not receipt_path.is_file():
        raise RuntimeError(f"attempt exists without receipt; manual evidence review required: {path}")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("status") != "completed_unreviewed":
        raise RuntimeError(f"attempt is {receipt.get('status')!r}, not resumable: {path}")
    if receipt.get("logical_run_id") != logical_id(row) or receipt.get("protocol_version") != row["protocol_version"]:
        raise RuntimeError(f"attempt identity does not match the frozen manifest: {path}")
    if receipt.get("split_manifest_id") != split["split_manifest_id"] or receipt.get("config_fingerprint") != expected_config:
        raise RuntimeError(f"attempt split/config differs from current frozen inputs: {path}")
    for name, expected in receipt.get("sha256", {}).items():
        artifact = path / name
        if not artifact.is_file() or sha256(artifact) != expected:
            raise RuntimeError(f"completed attempt has missing or changed artifact: {artifact}")
    required = {"pred.npy", "true.npy", "metrics.npy", "checkpoint.pth", "run.log"}
    if set(receipt.get("sha256", {})) != required:
        raise RuntimeError(f"attempt artifact inventory is incomplete: {path}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", action="append", choices=list(MANIFESTS), required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--execute", action="store_true", help="training is blocked without a formal authorization")
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--environment-fingerprint", type=Path)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    selected = [r for stage in args.stage for r in rows(MANIFESTS[stage]) if r["status"] == "planned"]
    _, _, issues = validate_preflight(selected)
    if issues:
        for issue in issues:
            print("BLOCK:", issue)
        return 2
    if len({logical_id(r) for r in selected}) != len(selected):
        print("BLOCK: duplicate logical run IDs in selected manifests")
        return 2
    print(f"selected={len(selected)} stages={','.join(args.stage)} protocol={config['protocol_version']}")
    pending = []
    already_done = 0
    for row in selected:
        attempts = sorted(OUTPUT.glob(logical_id(row) + "__attempt-*")) if OUTPUT.exists() else []
        if len(attempts) > 1:
            print(f"BLOCK: {logical_id(row)} has multiple attempts; explicit reconciliation required")
            return 2
        if attempts:
            try:
                split = split_for(row)
                current_config = {"row": row, "common": config["common"], "device": args.device}
                completed_attempt(attempts[0], row, split, canonical_hash(current_config))
            except (RuntimeError, json.JSONDecodeError) as error:
                print(f"BLOCK: {error}")
                return 2
            already_done += 1
        else:
            pending.append(row)
    selected = pending
    if args.limit is not None:
        selected = selected[:args.limit]
    print(f"already completed and hash-verified={already_done}")
    for row in selected[:5]:
        print("DRY", logical_id(row), f"split={row['split_mode']} horizon={row['horizon']}")
    if len(selected) > 5:
        print(f"... {len(selected) - 5} additional fits validated")
    if not args.execute:
        print("dry-run only; no training launched. Stage B/C/D execution remains separately gated.")
        return 0
    if not args.authorization or not args.environment_fingerprint:
        raise RuntimeError("--execute requires --authorization and --environment-fingerprint")
    auth, env_hash = validate_authorization(args.authorization, args.environment_fingerprint, set(args.stage), args.device)
    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was authorized but torch.cuda.is_available() is false")
    registry = {r["asset"]: r for r in rows(REGISTRY)}
    OUTPUT.mkdir(parents=True, exist_ok=True)
    log_root = ROOT / "reproduction/logs/phase1"
    log_root.mkdir(parents=True, exist_ok=True)
    for row in selected:
        logical = logical_id(row)
        destination = OUTPUT / f"{logical}__attempt-01"
        if destination.exists():
            raise RuntimeError(f"refusing to overwrite attempt: {destination}")
        destination.mkdir(parents=True, exist_ok=False)
        run_started = datetime.now(timezone.utc).isoformat()
        (destination / "receipt.json").write_text(json.dumps({
            "logical_run_id": logical, "attempt": 1, "attempt_id": destination.name,
            "protocol_version": row["protocol_version"], "stage": row["stage"],
            "status": "running", "created_at_utc": run_started,
            "authorization_record": auth.get("decision_record"), "authorization_commit": auth["git_commit"],
            "environment_fingerprint_sha256": env_hash,
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        command = build_command(row, config["common"], registry[row["asset"]], 1, args.device)
        model_id = f"{logical}__attempt-01"
        log_path = destination / "run.log"
        env = dict(os.environ, PYTHONUNBUFFERED="1")
        with log_path.open("x", encoding="utf-8") as log:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            failed = {"logical_run_id": logical, "attempt": 1, "attempt_id": destination.name,
                      "protocol_version": row["protocol_version"], "stage": row["stage"],
                      "status": "failed", "failure_class": "nonzero_exit", "exit_code": result.returncode,
                      "created_at_utc": run_started, "finished_at_utc": datetime.now(timezone.utc).isoformat(),
                      "authorization_record": auth.get("decision_record"), "authorization_commit": auth["git_commit"],
                      "environment_fingerprint_sha256": env_hash, "sha256": {"run.log": sha256(log_path)}}
            (destination / "receipt.json").write_text(json.dumps(failed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            raise RuntimeError(f"{logical} failed with exit {result.returncode}; log and any partial artifacts retained")
        matches = [p for p in (ROOT / "results").glob(f"*{model_id}*") if p.is_dir()]
        if len(matches) != 1:
            raise RuntimeError(f"expected one result directory for {logical}; found {len(matches)}")
        try:
            package_attempt(row, destination, command, log_path, matches[0].name, auth, env_hash,
                            config["common"], registry[row["asset"]])
        except Exception as error:
            invalid = {"logical_run_id": logical, "attempt": 1, "attempt_id": destination.name,
                       "protocol_version": row["protocol_version"], "stage": row["stage"],
                       "status": "artifact_invalid", "reason": str(error),
                       "created_at_utc": run_started, "finished_at_utc": datetime.now(timezone.utc).isoformat(),
                       "authorization_record": auth.get("decision_record"), "authorization_commit": auth["git_commit"],
                       "environment_fingerprint_sha256": env_hash,
                       "sha256": {"run.log": sha256(log_path)}}
            (destination / "receipt.json").write_text(json.dumps(invalid, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            raise
        print("PACKAGED", destination)


if __name__ == "__main__":
    raise SystemExit(main())
