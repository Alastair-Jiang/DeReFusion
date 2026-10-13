"""Synthetic-only process-isolated R1 lifecycle probe for the approved model bundle."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset


ROOT = Path(__file__).resolve().parents[4] / "research_work/forward_increment/lead_design_2026_10_07"
BUNDLE = ROOT / "adapter_candidate_2026_10_07/integration_candidate_v1/model_bundle_v3/source"
MODEL_F = BUNDLE / "models/derefusion/DeReFusion.py"
MODEL_B = BUNDLE / "models/derefusion/ablation_variant/DeReFusion-woDy.py"
SOURCE_PINS = {
    "models/derefusion/DeReFusion.py": "468a861d4e616a414ec603df87128ebe55bafe5f296502b54aef8aed23e5b091",
    "models/derefusion/ablation_variant/DeReFusion-woDy.py": "b231a3d0d4bf0effe6a8348a42e489f2baa957ab6698b1be46f8d7a6f9972eb2",
    "layers/derefusion_components.py": "91ae3bce16f8d758be71987672144fe400dd5f6a65352bf040c90c678ccd0a33",
    "layers/RevIN.py": "a7dc201d7ce2604bbdc19262d7c9ba8073a665e70f7cb734543d640c63bcf5cc",
}
CONFIG = SimpleNamespace(seq_len=96, pred_len=1, enc_in=4, d_model=32,
                         moving_avg=25, n_heads=4, e_layers=1, d_ff=128, dropout=0.3)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_model(path: Path):
    sys.path.insert(0, str(BUNDLE))
    name = "r1_synthetic_" + path.stem.replace("-", "_")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.Model(CONFIG).float()


def deterministic():
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(1701)
    np.random.seed(1701)


def read_role(path: Path, expected: str, manifest_path: Path):
    with np.load(path, allow_pickle=False) as z:
        role = str(z["role"].item())
        x = z["x"].astype(np.float32, copy=True)
        y = z["y"].astype(np.float32, copy=True)
        keys = z["keys"].astype("U64", copy=True)
    if role != expected:
        raise ValueError(f"role mismatch: expected {expected}, got {role}")
    if x.ndim != 3 or x.shape[1:] != (96, 4) or y.shape != (len(x), 1, 4):
        raise ValueError("payload shape violates R1 synthetic contract")
    if len(keys) != len(x) or len(set(keys.tolist())) != len(keys):
        raise ValueError("key cardinality/uniqueness failure")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_keys = manifest.get("expected_keys")
    if not isinstance(expected_keys, list) or keys.tolist() != expected_keys:
        raise ValueError("payload keys do not exactly match frozen expected-key manifest")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("non-finite payload")
    return x, y, keys


def key_weighted_mse(model, x, y, keys):
    model.eval()
    errors_by_key = {}
    seen = []
    with torch.no_grad():
        for ids in DataLoader(TensorDataset(torch.from_numpy(x), torch.from_numpy(y),
                                             torch.arange(len(x))), batch_size=3,
                              shuffle=False, drop_last=False):
            xb, yb, ix = ids
            pred = model(xb, None, None, None)
            if tuple(pred.shape) != (len(ix), 1, 4):
                raise ValueError("model output shape mismatch")
            err = pred[:, 0, 3].double() - yb[:, 0, 3].double()
            squared = (err * err).tolist()
            for index, value in zip(ix.tolist(), squared):
                key = str(keys[index])
                if key in errors_by_key or not math.isfinite(float(value)):
                    raise ValueError("duplicate key or non-finite keyed error")
                errors_by_key[key] = float(value)
                seen.append(index)
    if seen != list(range(len(keys))):
        raise ValueError("validation keys missing or reordered")
    if len(errors_by_key) != len(keys):
        raise ValueError("validation key coverage mismatch")
    return math.fsum(errors_by_key[k] for k in keys.tolist()) / len(keys)


def tensor_state_digest(model):
    h = hashlib.sha256()
    for name, tensor in sorted(model.state_dict().items()):
        h.update(name.encode())
        h.update(str(tuple(tensor.shape)).encode())
        h.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def checkpoint_transition(best_loss, best_epoch, candidate_loss, candidate_epoch):
    """Return the checkpoint state after the protocol's strict-improvement rule."""
    if candidate_loss < best_loss:
        return candidate_loss, candidate_epoch, True
    return best_loss, best_epoch, False


def train_worker(arm: str, train_path: Path, val_path: Path, train_manifest: Path,
                 val_manifest: Path, out_path: Path, seed: int):
    deterministic()
    torch.manual_seed(seed)
    np.random.seed(seed)
    xt, yt, kt = read_role(train_path, "train", train_manifest)
    xv, yv, kv = read_role(val_path, "validation", val_manifest)
    model = load_model(MODEL_F if arm == "F" else MODEL_B)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001, betas=(0.9, 0.999),
                                 eps=1e-8, weight_decay=0.0)
    generator = torch.Generator().manual_seed(seed)
    train_loader = DataLoader(TensorDataset(torch.from_numpy(xt), torch.from_numpy(yt)),
                              batch_size=32, shuffle=True, drop_last=False, generator=generator)
    best = float("inf")
    best_epoch = None
    history = []
    best_state = None
    stale = 0
    optimizer_steps = 0
    for epoch in range(50):
        model.train()
        for xb, yb in train_loader:
            optimizer.zero_grad(set_to_none=True)
            pred = model(xb, None, None, None)
            loss = torch.mean((pred[:, 0, 3] - yb[:, 0, 3]) ** 2)
            if not torch.isfinite(loss):
                raise ValueError("non-finite train loss")
            loss.backward()
            optimizer.step()
            optimizer_steps += 1
        val_loss = key_weighted_mse(model, xv, yv, kv)
        # Strict improvement means exact ties preserve the earlier checkpoint.
        best, best_epoch, improved = checkpoint_transition(best, best_epoch, val_loss, epoch + 1)
        if improved:
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            stale = 0
        else:
            stale += 1
        history.append({"epoch": epoch + 1, "validation_key_mse": val_loss,
                        "strict_improvement": improved})
        if stale >= 10:
            break
    if best_state is None:
        raise RuntimeError("no finite validation checkpoint")
    model.load_state_dict(best_state)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"arm": arm, "state_dict": best_state, "best_epoch": best_epoch,
                "best_validation_key_mse": best, "validation_key_count": len(kv),
                "validation_keys_sha256": sha("\n".join(kv.tolist()).encode()),
                "train_key_count": len(kt), "history": history}, out_path)
    # A second independently constructed model verifies ordinary state-dict restore.
    restored = load_model(MODEL_F if arm == "F" else MODEL_B)
    restored.load_state_dict(torch.load(out_path, map_location="cpu", weights_only=True)["state_dict"])
    result = {"arm": arm, "best_epoch": best_epoch, "best_validation_key_mse": best,
              "validation_key_count": len(kv), "train_key_count": len(kt),
              "state_tensor_sha256": tensor_state_digest(restored),
              "history": history, "optimizer_steps": optimizer_steps,
              "test_payload_argument_present": False}
    print(json.dumps(result, sort_keys=True))


def eval_worker(checkpoint: Path, test_path: Path, test_manifest: Path, out_path: Path):
    deterministic()
    xt, yt, keys = read_role(test_path, "test", test_manifest)
    saved = torch.load(checkpoint, map_location="cpu", weights_only=True)
    arm = saved["arm"]
    model = load_model(MODEL_F if arm == "F" else MODEL_B)
    model.load_state_dict(saved["state_dict"])
    mse = key_weighted_mse(model, xt, yt, keys)
    payload = {"arm": arm, "test_key_count": len(keys), "test_key_mse": mse,
               "test_keys_sha256": sha("\n".join(keys.tolist()).encode()),
               "checkpoint_best_epoch": saved["best_epoch"]}
    out_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))


def run_child(*args):
    p = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()), *map(str, args)],
                       check=False, capture_output=True, text=True, timeout=180)
    if p.returncode:
        raise RuntimeError(f"child failed rc={p.returncode}: {p.stderr[-3000:]}")
    return json.loads(p.stdout.strip().splitlines()[-1])


def make_payload(path: Path, role: str, seed: int, n: int, test_shift: float = 0.0):
    rng = np.random.default_rng(seed)
    x = rng.normal(100.0, 3.0, size=(n, 96, 4)).astype(np.float32)
    # Synthetic deterministic next-row relation; no real observations.
    y = np.zeros((n, 1, 4), np.float32)
    y[:, 0, 3] = x[:, -1, 3] + 0.15 * (x[:, -1, 0] - x[:, -2, 0])
    y[:, 0, 3] += test_shift
    keys = np.array([f"SYN-{role}-{i:04d}" for i in range(n)])
    np.savez(path, role=np.array(role), x=x, y=y, keys=keys)
    path.with_suffix(".keys.json").write_text(json.dumps({"expected_keys": keys.tolist()}, indent=2) + "\n", encoding="utf-8")


def make_variant(source: Path, target: Path, *, role=None, duplicate_key=False, nonfinite=False):
    with np.load(source, allow_pickle=False) as z:
        r = str(z["role"].item()) if role is None else role
        x, y, keys = z["x"].copy(), z["y"].copy(), z["keys"].copy()
    if duplicate_key:
        keys[-1] = keys[0]
    if nonfinite:
        x[0, 0, 0] = np.nan
    np.savez(target, role=np.array(r), x=x, y=y, keys=keys)


def assert_rejected_worker(train_path, val_path, train_manifest, val_manifest, out_path):
    p = subprocess.run(
        [sys.executable, "-B", str(Path(__file__).resolve()), "--worker", "train",
         "--arm", "B", "--train", str(train_path), "--val", str(val_path),
         "--train-manifest", str(train_manifest), "--val-manifest", str(val_manifest),
         "--out", str(out_path), "--seed", "17"],
        capture_output=True, text=True, timeout=30)
    assert p.returncode == 2 and "Traceback" not in p.stderr, (p.returncode, p.stderr[-1000:])
    assert not out_path.exists()
    return p.stderr.strip().splitlines()[-1]


def parent():
    measured_pins = {p: sha((BUNDLE / p).read_bytes()) for p in SOURCE_PINS}
    if measured_pins != SOURCE_PINS:
        raise RuntimeError(f"model source pin mismatch: {measured_pins}")
    with tempfile.TemporaryDirectory(prefix="derefusion_r1_lifecycle_synth_") as td:
        root = Path(td)
        train, val, test = root / "train.npz", root / "val.npz", root / "test.npz"
        make_payload(train, "train", 11, 13)
        make_payload(val, "validation", 12, 7)
        make_payload(test, "test", 13, 5)
        test_before = sha(test.read_bytes())
        outputs = {}
        for arm in ("F", "B"):
            ckpt, ev = root / f"{arm}.pt", root / f"{arm}.eval.json"
            base = run_child("--worker", "train", "--arm", arm, "--train", train,
                             "--val", val, "--train-manifest", train.with_suffix(".keys.json"),
                             "--val-manifest", val.with_suffix(".keys.json"), "--out", ckpt, "--seed", 17)
            evaluation = run_child("--worker", "eval", "--checkpoint", ckpt,
                                   "--test", test, "--test-manifest", test.with_suffix(".keys.json"), "--out", ev)
            outputs[arm] = {"train": base, "evaluation": evaluation,
                            "checkpoint_sha256": sha(ckpt.read_bytes())}
        # Sentinel: changing only synthetic test labels must not change any fit artifact.
        make_payload(test, "test", 13, 5, test_shift=1000.0)
        changed_test_sha = sha(test.read_bytes())
        sentinel = {}
        for arm in ("F", "B"):
            ckpt = root / f"{arm}_sentinel.pt"
            rerun = run_child("--worker", "train", "--arm", arm, "--train", train,
                              "--val", val, "--train-manifest", train.with_suffix(".keys.json"),
                              "--val-manifest", val.with_suffix(".keys.json"), "--out", ckpt, "--seed", 17)
            sentinel[arm] = {"train_result_identical": rerun == outputs[arm]["train"],
                             "state_tensor_identical": rerun["state_tensor_sha256"] == outputs[arm]["train"]["state_tensor_sha256"]}
        assert sha(test.read_bytes()) == changed_test_sha and changed_test_sha != test_before
        assert all(v["train_result_identical"] and v["state_tensor_identical"] for v in sentinel.values())
        assert all(v["evaluation"]["test_key_count"] == 5 for v in outputs.values())
        assert all(sum(h["strict_improvement"] for h in v["train"]["history"]) >= 1 for v in outputs.values())
        # The train worker's CLI must reject any attempt to provide a test package.
        unknown_test_arg = subprocess.run(
            [sys.executable, "-B", str(Path(__file__).resolve()), "--worker", "train",
             "--arm", "B", "--train", str(train), "--val", str(val),
             "--train-manifest", str(train.with_suffix(".keys.json")),
             "--val-manifest", str(val.with_suffix(".keys.json")),
             "--out", str(root / "should_not_exist.pt"), "--seed", "17", "--test", str(test)],
            capture_output=True, text=True, timeout=30)
        assert unknown_test_arg.returncode != 0 and "must not receive test" in unknown_test_arg.stderr
        assert not (root / "should_not_exist.pt").exists()
        rejected_cases = {}
        missing_manifest = root / "val_missing_manifest.json"
        manifest_value = json.loads(val.with_suffix(".keys.json").read_text(encoding="utf-8"))
        missing_manifest.write_text(json.dumps({"expected_keys": manifest_value["expected_keys"][:-1]}), encoding="utf-8")
        rejected_cases["missing_expected_key"] = assert_rejected_worker(
            train, val, train.with_suffix(".keys.json"), missing_manifest, root / "reject_missing.pt")
        duplicate_val = root / "val_duplicate.npz"
        make_variant(val, duplicate_val, duplicate_key=True)
        rejected_cases["duplicate_key"] = assert_rejected_worker(
            train, duplicate_val, train.with_suffix(".keys.json"), val.with_suffix(".keys.json"), root / "reject_duplicate.pt")
        wrong_role_val = root / "val_wrong_role.npz"
        make_variant(val, wrong_role_val, role="test")
        rejected_cases["wrong_role"] = assert_rejected_worker(
            train, wrong_role_val, train.with_suffix(".keys.json"), val.with_suffix(".keys.json"), root / "reject_role.pt")
        nonfinite_val = root / "val_nonfinite.npz"
        make_variant(val, nonfinite_val, nonfinite=True)
        rejected_cases["nonfinite_input"] = assert_rejected_worker(
            train, nonfinite_val, train.with_suffix(".keys.json"), val.with_suffix(".keys.json"), root / "reject_nonfinite.pt")
        tied_loss_state = checkpoint_transition(1.0, 4, 1.0, 5)
        assert tied_loss_state == (1.0, 4, False)
        result = {"result": "PASS", "scope": "synthetic-only; actual patched F/B model, optimizer steps, key-weighted validation, checkpoint restore, separate evaluator process",
                  "source_sha256": measured_pins,
                  "torch": torch.__version__, "test_payload_hash_before": test_before,
                  "test_payload_hash_after_sentinel": changed_test_sha,
                  "sentinel_train_artifacts_unchanged": sentinel,
                  "rejected_synthetic_cases": rejected_cases,
                  "arms": outputs,
                  "checks": {"train_worker_has_no_test_argument": True,
                             "train_test_sentinel": all(v["train_result_identical"] for v in sentinel.values()),
                             "validation_tail_key_included": all(v["train"]["validation_key_count"] == 7 for v in outputs.values()),
                             "test_argument_rejected_by_train_worker": True,
                             "checkpoint_restore": True,
                             "strict_tie_keeps_earlier": tied_loss_state == (1.0, 4, False),
                             "real_data_access": False}}
        result_path = Path(__file__).resolve().parent / "SYNTHETIC_LIFECYCLE_RESULTS.json"
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", choices=("train", "eval"))
    ap.add_argument("--arm", choices=("F", "B"))
    ap.add_argument("--train", type=Path)
    ap.add_argument("--val", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--checkpoint", type=Path)
    ap.add_argument("--test", type=Path)
    ap.add_argument("--train-manifest", type=Path)
    ap.add_argument("--val-manifest", type=Path)
    ap.add_argument("--test-manifest", type=Path)
    ap.add_argument("--seed", type=int, choices=(17, 29, 43))
    a = ap.parse_args()
    if not a.worker:
        parent()
    elif a.worker == "train":
        try:
            if a.test is not None or a.checkpoint is not None:
                ap.error("train worker must not receive test or checkpoint-evaluation inputs")
            if not all((a.arm, a.train, a.val, a.train_manifest, a.val_manifest, a.out, a.seed)):
                ap.error("train requires arm/train/val/manifests/out/seed")
            train_worker(a.arm, a.train, a.val, a.train_manifest, a.val_manifest, a.out, a.seed)
        except (ValueError, RuntimeError, OSError) as exc:
            print(json.dumps({"worker_result": "REJECTED", "reason": str(exc)}, sort_keys=True), file=sys.stderr)
            raise SystemExit(2)
    else:
        if not all((a.checkpoint, a.test, a.test_manifest, a.out)):
            ap.error("eval requires checkpoint/test/manifest/out")
        eval_worker(a.checkpoint, a.test, a.test_manifest, a.out)


if __name__ == "__main__":
    main()
