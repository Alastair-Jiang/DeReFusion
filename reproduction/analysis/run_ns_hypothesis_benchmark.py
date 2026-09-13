#!/usr/bin/env python
"""Locked-protocol benchmark for a temporal NS-inspired nonlinear operator.

This runner is deliberately separate from DeReFusion.  It evaluates a single
parameter-tied local flux/curvature proxy against the required ordinary model
families: MLP, causal temporal convolution, and a non-selective diagonal SSM.

It has no router, adaptive gate, MoE, attention, pressure term, or learned
sample-level coefficient.  A manifest is the experiment's pre-registration:
the script will only execute a locked manifest that names the eligibility
evidence, every asset, and every input-file hash.  The default action is a
read-only preflight; ``--execute`` is required to train anything.

This code supplies an experimental instrument.  It is not evidence that an
NS-inspired structure is useful.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F


ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "dataset"
DEFAULT_RESULTS_ROOT = ROOT / "reproduction" / "results" / "ns_hypothesis_benchmark"

# Frozen task settings.  A new benchmark must not silently alter these.
SEQ_LEN = 96
PRED_LEN = 24
TRAIN_RATIO = 0.70
TEST_RATIO = 0.20
SEEDS = (2021, 2022, 2023)
EPOCHS = 30
BATCH = 32
LR = 1e-4
PATIENCE = 5
BOOTSTRAP_RESAMPLES = 4000
CAPACITIES = {"w23": 23, "w64": 64, "w128": 128}
MODEL_ORDER = ("mlp", "causal_conv", "ssm", "temporal_ns")
FEATURE_VIEWS = {"raw", "multiscale", "state", "multiscale_state"}
TIME_COORDINATES = {"none", "lag_linear", "lag_sqrt"}


class ManifestError(ValueError):
    """Raised when a manifest would make the result non-auditable."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    if not isinstance(manifest, dict):
        raise ManifestError("Manifest root must be a JSON object.")
    return manifest


def require(value: Any, message: str) -> Any:
    if not value:
        raise ManifestError(message)
    return value


def validate_manifest(manifest: dict[str, Any], execute: bool) -> None:
    require(manifest.get("protocol_id"), "protocol_id is required.")
    assets = require(manifest.get("assets"), "assets must name the full pre-registered cohort.")
    if not isinstance(assets, list) or not all(isinstance(asset, str) and asset for asset in assets):
        raise ManifestError("assets must be a non-empty list of asset tags.")
    if len(assets) != len(set(assets)):
        raise ManifestError("assets contains duplicates; asset selection must be fixed before execution.")

    fixed = manifest.get("frozen_protocol", {})
    expected = {
        "seq_len": SEQ_LEN,
        "pred_len": PRED_LEN,
        "train_ratio": TRAIN_RATIO,
        "test_ratio": TEST_RATIO,
        "seeds": list(SEEDS),
        "epochs": EPOCHS,
        "batch_size": BATCH,
        "learning_rate": LR,
        "patience": PATIENCE,
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
    }
    for key, value in expected.items():
        if fixed.get(key) != value:
            raise ManifestError(f"frozen_protocol.{key} must equal {value!r}.")

    if manifest.get("capacity_labels") != list(CAPACITIES):
        raise ManifestError(f"capacity_labels must be exactly {list(CAPACITIES)!r}.")
    if manifest.get("models") != list(MODEL_ORDER):
        raise ManifestError(f"models must be exactly {list(MODEL_ORDER)!r}.")
    if manifest.get("feature_view") not in FEATURE_VIEWS:
        raise ManifestError(f"feature_view must be one of {sorted(FEATURE_VIEWS)!r}.")
    if manifest.get("time_coordinate") not in TIME_COORDINATES:
        raise ManifestError(f"time_coordinate must be one of {sorted(TIME_COORDINATES)!r}.")
    if manifest.get("fusion_mode", "none") != "none":
        raise ManifestError(
            "Fusion is excluded: static fusion is absorbed by an ordinary readout and "
            "input-dependent fusion is prohibited adaptive gating."
        )
    regularizer = manifest.get("regularizer", {})
    weight = regularizer.get("prediction_curvature_weight", 0.0)
    if not isinstance(weight, (int, float)) or weight < 0:
        raise ManifestError("regularizer.prediction_curvature_weight must be a non-negative number.")
    require(manifest.get("falsification"), "A pre-written falsification statement is required.")

    if not execute:
        return

    if manifest.get("status") != "LOCKED":
        raise ManifestError("Execution requires status = LOCKED.")
    if manifest.get("eligibility_evidence") != "C1_REPLICATED":
        raise ManifestError("Execution requires eligibility_evidence = C1_REPLICATED.")
    report = require(manifest.get("eligibility_report"), "eligibility_report is required for execution.")
    if not (ROOT / report).is_file():
        raise ManifestError(f"Eligibility report is missing: {report}")
    hashes = require(manifest.get("asset_sha256"), "asset_sha256 is required for execution.")
    if set(hashes) != set(assets):
        raise ManifestError("asset_sha256 must contain exactly one hash for every asset.")
    for asset in assets:
        csv_path = DATASET / f"{asset}-2016-2025.csv"
        if not csv_path.is_file():
            raise ManifestError(f"Missing dataset for asset {asset}: {csv_path}")
        actual = sha256_file(csv_path)
        if hashes[asset].lower() != actual:
            raise ManifestError(f"Dataset hash changed for {asset}; create and lock a new manifest.")


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)


def count_parameters(model: nn.Module) -> int:
    return sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)


def shift_right(values: torch.Tensor, amount: int = 1) -> torch.Tensor:
    """Causal shift with a zero history before the observed window."""
    result = torch.zeros_like(values)
    if amount < values.shape[1]:
        result[:, amount:] = values[:, :-amount]
    return result


class MLPForecaster(nn.Module):
    def __init__(self, channels: int, hidden: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Flatten(),
            nn.Linear(SEQ_LEN * channels, hidden),
            nn.ReLU(),
            nn.Linear(hidden, PRED_LEN),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class CausalConvForecaster(nn.Module):
    """Ordinary causal convolution baseline; it receives exactly the common input view."""
    def __init__(self, channels: int, hidden: int) -> None:
        super().__init__()
        self.in_proj = nn.Conv1d(channels, hidden, kernel_size=1)
        self.conv1 = nn.Conv1d(hidden, hidden, kernel_size=3)
        self.conv2 = nn.Conv1d(hidden, hidden, kernel_size=3)
        self.head = nn.Linear(hidden, PRED_LEN)

    @staticmethod
    def causal_conv(layer: nn.Conv1d, x: torch.Tensor) -> torch.Tensor:
        return layer(F.pad(x, (layer.kernel_size[0] - 1, 0)))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = x.transpose(1, 2)
        z = torch.tanh(self.in_proj(z))
        z = torch.tanh(self.causal_conv(self.conv1, z))
        z = torch.tanh(self.causal_conv(self.conv2, z))
        return self.head(z[:, :, -1])


class DiagonalSSMForecaster(nn.Module):
    """A stationary, non-selective diagonal state-space baseline.

    The transition coefficients are global learned parameters, shared across all samples and
    time steps.  No sample-level selection or input-dependent transition is present.
    """
    def __init__(self, channels: int, hidden: int) -> None:
        super().__init__()
        self.input_proj = nn.Linear(channels, hidden)
        self.logit_decay = nn.Parameter(torch.zeros(hidden))
        self.bias = nn.Parameter(torch.zeros(hidden))
        self.head = nn.Linear(hidden, PRED_LEN)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        drive = torch.tanh(self.input_proj(x))
        decay = torch.sigmoid(self.logit_decay).unsqueeze(0)
        state = torch.zeros(x.shape[0], drive.shape[-1], device=x.device, dtype=x.dtype)
        for step in range(x.shape[1]):
            state = decay * state + (1.0 - decay) * drive[:, step] + self.bias
        return self.head(torch.tanh(state))


class TemporalNSInspiredForecaster(nn.Module):
    """A small local flux/curvature proxy, used only in this standalone benchmark.

    It has a backward flux difference and backward second difference on the observed history
    grid.  The coefficients are global scalars.  The module makes no energy, conservation,
    PDE, or numerical-stability claim.
    """
    def __init__(self, channels: int, hidden: int, steps: int = 2) -> None:
        super().__init__()
        self.input_proj = nn.Linear(channels, hidden)
        self.flux_scale = nn.Parameter(torch.tensor(0.01))
        self.curvature_scale = nn.Parameter(torch.tensor(0.01))
        self.steps = steps
        self.head = nn.Linear(hidden, PRED_LEN)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = torch.tanh(self.input_proj(x))
        for _ in range(self.steps):
            flux = 0.5 * z.square()
            flux_difference = flux - shift_right(flux)
            first = z - shift_right(z)
            curvature = first - shift_right(first)
            z = z - self.flux_scale * flux_difference + self.curvature_scale * curvature
        return self.head(z[:, -1])


ModelFactory = Callable[[int, int], nn.Module]


def factory_for(name: str, channels: int) -> ModelFactory:
    if name == "mlp":
        return lambda hidden, _: MLPForecaster(channels, hidden)
    if name == "causal_conv":
        return lambda hidden, _: CausalConvForecaster(channels, hidden)
    if name == "ssm":
        return lambda hidden, _: DiagonalSSMForecaster(channels, hidden)
    if name == "temporal_ns":
        return lambda hidden, _: TemporalNSInspiredForecaster(channels, hidden)
    raise ValueError(f"Unknown model family: {name}")


def closest_budget_model(name: str, channels: int, target_params: int) -> tuple[nn.Module, int]:
    """Choose the closest parameter count before outcomes are observed.

    Every non-MLP family uses a monotone hidden-width search.  The exact count is recorded
    for review; this function never chooses architecture from validation or test performance.
    """
    factory = factory_for(name, channels)
    lo, hi = 2, 4096
    candidates: list[tuple[int, nn.Module]] = []
    while lo <= hi:
        mid = (lo + hi) // 2
        model = factory(mid, PRED_LEN)
        params = count_parameters(model)
        candidates.append((params, model))
        if params < target_params:
            lo = mid + 1
        elif params > target_params:
            hi = mid - 1
        else:
            break
    # Include immediate neighbours because integer architectures need not hit the budget exactly.
    for width in {max(2, lo - 1), lo, max(2, hi), hi + 1}:
        if 2 <= width <= 4096:
            model = factory(width, PRED_LEN)
            candidates.append((count_parameters(model), model))
    params, model = min(candidates, key=lambda item: (abs(item[0] - target_params), item[0]))
    return model, params


def causal_average(values: np.ndarray, window: int = 25) -> np.ndarray:
    """Causal local average with left-edge truncation; uses no data after each position."""
    total = np.cumsum(values, axis=1, dtype=np.float64)
    total = np.concatenate([np.zeros_like(total[:, :1]), total], axis=1)
    steps = np.arange(values.shape[1])
    start = np.maximum(0, steps - window + 1)
    numerator = total[:, steps + 1] - total[:, start]
    denominator = (steps - start + 1).astype(np.float64)
    return (numerator / denominator[None, :]).astype(np.float32)


def raw_derived_channels(close: np.ndarray) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Derive history-only channels from raw positive Close prices."""
    close = np.maximum(close, 1e-8)
    returns = np.diff(np.log(close), axis=1, prepend=np.log(close[:, :1]))
    trend = causal_average(close)
    residual = close - trend
    closure_q = causal_average(returns ** 2) - causal_average(returns) ** 2
    closure_q = np.maximum(closure_q, 0.0)
    first = np.diff(returns, axis=1, prepend=returns[:, :1])
    second = np.diff(first, axis=1, prepend=first[:, :1])
    return {
        "trend": trend,
        "residual": residual,
        "closure_q": closure_q,
        "returns": returns,
        "first_difference": first,
        "second_difference": second,
    }, closure_q.mean(axis=1).astype(np.float32)


def view_extras(derived: dict[str, np.ndarray], feature_view: str) -> list[np.ndarray]:
    extras: list[np.ndarray] = []
    if feature_view in {"multiscale", "multiscale_state"}:
        extras.extend([derived["trend"], derived["residual"], derived["closure_q"]])
    if feature_view in {"state", "multiscale_state"}:
        extras.extend([derived["returns"], derived["first_difference"], derived["second_difference"]])
    return extras


def build_input_views(
    x_train: np.ndarray,
    x_val: np.ndarray,
    x_test: np.ndarray,
    close_train: np.ndarray,
    close_val: np.ndarray,
    close_test: np.ndarray,
    feature_view: str,
    time_coordinate: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Build common history-only inputs, standardising extras from train data only.

    ``closure_q`` is C(r²) - C(r)² for returns r, which is a local variance statistic.
    It is a detector and common feature only; it never selects a model, asset, or sample.
    """
    if x_train.ndim != 3 or x_train.shape[1] != SEQ_LEN or x_train.shape[2] < 4:
        raise ValueError("Expected [samples, 96, OHLC channels] input windows.")
    derived_train, _ = raw_derived_channels(close_train)
    derived_val, _ = raw_derived_channels(close_val)
    derived_test, detector_test = raw_derived_channels(close_test)
    extra_train = view_extras(derived_train, feature_view)
    extra_val = view_extras(derived_val, feature_view)
    extra_test = view_extras(derived_test, feature_view)
    if extra_train:
        train_stack = np.stack(extra_train, axis=2)
        val_stack = np.stack(extra_val, axis=2)
        test_stack = np.stack(extra_test, axis=2)
        mean = train_stack.mean(axis=(0, 1), keepdims=True)
        std = train_stack.std(axis=(0, 1), keepdims=True)
        std = np.where(std < 1e-12, 1.0, std)
        train_stack = (train_stack - mean) / std
        val_stack = (val_stack - mean) / std
        test_stack = (test_stack - mean) / std
    else:
        train_stack = np.empty((*x_train.shape[:2], 0), dtype=np.float32)
        val_stack = np.empty((*x_val.shape[:2], 0), dtype=np.float32)
        test_stack = np.empty((*x_test.shape[:2], 0), dtype=np.float32)

    def append_coordinate(base: np.ndarray, extras: np.ndarray) -> np.ndarray:
        pieces = [base, extras]
        if time_coordinate == "none":
            return np.concatenate(pieces, axis=2).astype(np.float32)
        lag = np.linspace(-1.0, 0.0, SEQ_LEN, dtype=np.float32)
        if time_coordinate == "lag_sqrt":
            lag = -np.sqrt(np.abs(lag))
        coordinate = np.broadcast_to(lag[None, :, None], (base.shape[0], SEQ_LEN, 1))
        return np.concatenate([*pieces, coordinate], axis=2).astype(np.float32)

    return (
        append_coordinate(x_train, train_stack),
        append_coordinate(x_val, val_stack),
        append_coordinate(x_test, test_stack),
        detector_test,
    )


@dataclass
class AssetData:
    x_train: np.ndarray
    y_train: np.ndarray
    x_val: np.ndarray
    y_val: np.ndarray
    x_test: np.ndarray
    y_test: np.ndarray
    detector_test: np.ndarray


def make_windows(scaled: np.ndarray, start: int, count: int) -> tuple[np.ndarray, np.ndarray]:
    x_rows, y_rows = [], []
    for offset in range(count):
        index = start + offset
        x_rows.append(scaled[index:index + SEQ_LEN])
        y_rows.append(scaled[index + SEQ_LEN:index + SEQ_LEN + PRED_LEN, 3])
    return np.asarray(x_rows, dtype=np.float32), np.asarray(y_rows, dtype=np.float32)


def make_close_windows(close: np.ndarray, start: int, count: int) -> np.ndarray:
    return np.asarray([close[start + offset:start + offset + SEQ_LEN] for offset in range(count)], dtype=np.float32)


def load_asset(asset: str, feature_view: str, time_coordinate: str) -> AssetData:
    path = DATASET / f"{asset}-2016-2025.csv"
    table = pd.read_csv(path)
    required = ["Open", "High", "Low", "Close"]
    if any(column not in table.columns for column in required):
        raise ValueError(f"{path} must contain {required}.")
    raw = table[required].to_numpy(dtype=np.float32)
    n_rows = len(raw)
    n_train = int(n_rows * TRAIN_RATIO)
    test_start = n_rows - int(n_rows * TEST_RATIO) - SEQ_LEN
    n_train_windows = n_train - SEQ_LEN - PRED_LEN + 1
    val_start = n_train - SEQ_LEN
    n_val_windows = (n_rows - int(n_rows * TEST_RATIO)) - val_start - SEQ_LEN - PRED_LEN + 1
    n_test_windows = n_rows - test_start - SEQ_LEN - PRED_LEN + 1
    if min(n_train_windows, n_val_windows, n_test_windows) <= 0:
        raise ValueError(f"{asset} does not provide enough rows for the frozen split.")
    mean = raw[:n_train].mean(axis=0, keepdims=True)
    std = raw[:n_train].std(axis=0, keepdims=True)
    if np.any(std < 1e-12):
        raise ValueError(f"{asset} has a near-constant train channel.")
    scaled = (raw - mean) / std
    x_train, y_train = make_windows(scaled, 0, n_train_windows)
    x_val, y_val = make_windows(scaled, val_start, n_val_windows)
    x_test, y_test = make_windows(scaled, test_start, n_test_windows)
    close = raw[:, 3]
    close_train = make_close_windows(close, 0, n_train_windows)
    close_val = make_close_windows(close, val_start, n_val_windows)
    close_test = make_close_windows(close, test_start, n_test_windows)
    x_train, x_val, x_test, detector = build_input_views(
        x_train, x_val, x_test, close_train, close_val, close_test, feature_view, time_coordinate
    )
    return AssetData(x_train, y_train, x_val, y_val, x_test, y_test, detector)


def prediction_curvature(prediction: torch.Tensor) -> torch.Tensor:
    if prediction.shape[1] < 3:
        return torch.zeros((), device=prediction.device, dtype=prediction.dtype)
    return (prediction[:, 2:] - 2.0 * prediction[:, 1:-1] + prediction[:, :-2]).square().mean()


def train_model(
    model: nn.Module,
    data: AssetData,
    seed: int,
    curvature_weight: float,
) -> tuple[nn.Module, float, int]:
    set_seed(seed)
    model = model.cpu()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)
    loss_fn = nn.MSELoss()
    x_train, y_train = torch.tensor(data.x_train), torch.tensor(data.y_train)
    x_val, y_val = torch.tensor(data.x_val), torch.tensor(data.y_val)
    best_value = math.inf
    best_state: dict[str, torch.Tensor] | None = None
    bad_epochs = 0
    epochs_run = 0
    for epoch in range(EPOCHS):
        epochs_run = epoch + 1
        model.train()
        ordering = torch.randperm(len(x_train))
        for begin in range(0, len(x_train), BATCH):
            indices = ordering[begin:begin + BATCH]
            prediction = model(x_train[indices])
            loss = loss_fn(prediction, y_train[indices])
            if curvature_weight:
                loss = loss + curvature_weight * prediction_curvature(prediction)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        scheduler.step()
        model.eval()
        with torch.no_grad():
            value = float(loss_fn(model(x_val), y_val))
        if value < best_value - 1e-6:
            best_value = value
            bad_epochs = 0
            best_state = {key: tensor.detach().cpu().clone() for key, tensor in model.state_dict().items()}
        else:
            bad_epochs += 1
            if bad_epochs >= PATIENCE:
                break
    if best_state is None:
        raise RuntimeError("Training produced no validation state.")
    model.load_state_dict(best_state)
    model.eval()
    return model, best_value, epochs_run


def paired_bootstrap(delta: np.ndarray, seed: int) -> tuple[float, float]:
    if len(delta) == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(delta), size=(BOOTSTRAP_RESAMPLES, len(delta)))
    means = delta[indices].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def write_json(path: Path, value: Any) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)


def prepare_output(manifest: dict[str, Any]) -> Path:
    configured = manifest.get("output_root")
    root = (ROOT / configured) if configured else DEFAULT_RESULTS_ROOT
    output = root / manifest["protocol_id"]
    if output.exists():
        raise ManifestError(f"Output path already exists and will not be overwritten: {output}")
    output.mkdir(parents=True, exist_ok=False)
    return output


def run(manifest: dict[str, Any]) -> Path:
    output = prepare_output(manifest)
    write_json(output / "manifest.lock.json", manifest)
    write_json(output / "component_registry.json", {
        "temporal_ns": "global-coefficient local flux/curvature proxy; no physical claim",
        "causal_conv": "ordinary causal temporal convolution baseline",
        "ssm": "stationary non-selective diagonal SSM baseline",
        "fusion": "not implemented: fixed fusion is an ordinary readout; adaptive fusion is prohibited",
        "time_coordinate": "common fixed coordinate feature supplied to every model",
        "regularizer": "common prediction-curvature penalty supplied to every model",
        "detector": "history-only local variance statistic, analysis-only and never a selector",
    })
    regularizer_weight = float(manifest["regularizer"].get("prediction_curvature_weight", 0.0))
    result_rows: list[dict[str, Any]] = []
    comparison_rows: list[dict[str, Any]] = []
    run_index: list[dict[str, Any]] = []
    for asset in manifest["assets"]:
        data = load_asset(asset, manifest["feature_view"], manifest["time_coordinate"])
        channels = data.x_train.shape[2]
        for capacity_name, mlp_hidden in CAPACITIES.items():
            anchor = MLPForecaster(channels, mlp_hidden)
            budget = count_parameters(anchor)
            for seed in SEEDS:
                fitted: dict[str, dict[str, Any]] = {}
                for name in MODEL_ORDER:
                    set_seed(seed)
                    if name == "mlp":
                        model = MLPForecaster(channels, mlp_hidden)
                        parameter_count = count_parameters(model)
                    else:
                        model, parameter_count = closest_budget_model(name, channels, budget)
                    model, best_validation, epochs_run = train_model(model, data, seed, regularizer_weight)
                    with torch.no_grad():
                        prediction = model(torch.tensor(data.x_test)).numpy()
                    square_error = ((prediction - data.y_test) ** 2).mean(axis=1)
                    run_name = f"{asset}__{capacity_name}__{name}__s{seed}"
                    np.savez_compressed(
                        output / f"{run_name}.npz",
                        prediction=prediction.astype(np.float32),
                        target=data.y_test.astype(np.float32),
                        square_error=square_error.astype(np.float32),
                        closure_q=data.detector_test.astype(np.float32),
                    )
                    run_metadata = {
                        "asset": asset,
                        "capacity": capacity_name,
                        "model": name,
                        "seed": seed,
                        "parameter_count": parameter_count,
                        "budget_anchor_params": budget,
                        "parameter_gap": parameter_count - budget,
                        "best_validation_mse": best_validation,
                        "epochs_run": epochs_run,
                        "test_mse": float(square_error.mean()),
                        "raw_output": f"{run_name}.npz",
                    }
                    write_json(output / f"{run_name}.json", run_metadata)
                    result_rows.append(run_metadata)
                    run_index.append(run_metadata)
                    fitted[name] = {"square_error": square_error, "metadata": run_metadata}
                candidate_error = fitted["temporal_ns"]["square_error"]
                for baseline in ("mlp", "causal_conv", "ssm"):
                    delta = candidate_error - fitted[baseline]["square_error"]
                    ci_low, ci_high = paired_bootstrap(delta, seed)
                    correlation = pd.Series(data.detector_test).corr(pd.Series(delta), method="spearman")
                    comparison_rows.append({
                        "asset": asset,
                        "capacity": capacity_name,
                        "seed": seed,
                        "candidate": "temporal_ns",
                        "baseline": baseline,
                        "mean_delta_mse": float(delta.mean()),
                        "bootstrap_ci_low": ci_low,
                        "bootstrap_ci_high": ci_high,
                        "detector_spearman_with_delta": None if pd.isna(correlation) else float(correlation),
                        "detector_note": "Analysis-only; closure_q uses the input window before each forecast origin.",
                    })
    pd.DataFrame(result_rows).to_csv(output / "run_summary.csv", index=False)
    pd.DataFrame(comparison_rows).to_csv(output / "paired_comparisons.csv", index=False)
    write_json(output / "run_index.json", run_index)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path, help="Locked JSON experiment manifest.")
    parser.add_argument("--execute", action="store_true", help="Run training. Omit for read-only preflight.")
    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    validate_manifest(manifest, execute=args.execute)
    if not args.execute:
        print("PRECHECK_OK: manifest is structurally valid. No model, dataset, or output was written.")
        print(f"protocol_id={manifest['protocol_id']} assets={manifest['assets']}")
        print("Execution remains blocked until status=LOCKED, C1_REPLICATED evidence, hashes, and report path are present.")
        return 0
    output = run(manifest)
    print(f"COMPLETE: raw outputs and summaries written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
