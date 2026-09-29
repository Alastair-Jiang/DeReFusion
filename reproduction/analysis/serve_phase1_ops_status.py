"""Bounded localhost operational observations; never trains or modifies evidence.

Run with ``python serve_phase1_ops_status.py --repo-root PATH``. The only
subprocesses are fixed, read-only NVIDIA and Windows process observations.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import re
import subprocess
import threading
import time
from urllib.parse import urlsplit

SCHEMA_VERSION = "phase1-ops/v1"
ALLOWED_ORIGINS = {"http://localhost:8964", "http://127.0.0.1:8964"}
MAX_JSON_BYTES = 16 * 1024 * 1024
FRESH_SECONDS = 180


def utc_now():
    return datetime.now(timezone.utc)


def iso(value):
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def timestamp(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed
    except (TypeError, ValueError):
        return None


def read_json(path):
    try:
        if path.is_symlink() or path.stat().st_size > MAX_JSON_BYTES:
            return {}
        with path.open(encoding="utf-8-sig") as stream:
            result = json.load(stream)
        return result if isinstance(result, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def mtime(path):
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
    except OSError:
        return None


def children(path, pattern="*"):
    try:
        return [p for p in path.glob(pattern) if not p.is_symlink()]
    except OSError:
        return []


def freshness(value, now):
    if value is None:
        return "unknown"
    return "fresh" if max(0, (now - value).total_seconds()) <= FRESH_SECONDS else "stale"


def number(value):
    try:
        result = float(value)
        return result if result >= 0 and result < 1e9 else None
    except (TypeError, ValueError):
        return None


def count(value, default=0):
    parsed = number(value)
    return int(parsed) if parsed is not None else default


def safe_run(value):
    # Only the protocol run identifier enters responses, never a command or path.
    return value if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,180}", value) else None


def completed_receipts(root):
    identities = set()
    latest = None
    for path in children(root, "*/receipt.json"):
        receipt = read_json(path)
        if str(receipt.get("status", "")).startswith("completed"):
            identity = safe_run(receipt.get("logical_run_id")) or path.parent.name
            identities.add(identity)
            observed = timestamp(receipt.get("created_at_utc")) or mtime(path)
            if observed and (latest is None or observed > latest):
                latest = observed
    return identities, latest


def consumer_receipts(root):
    identities = set()
    latest = None
    failures = 0
    for path in children(root, "pass*/acknowledgement.json"):
        ack = read_json(path)
        observed = timestamp(ack.get("created_at_utc")) or mtime(path)
        if observed and (latest is None or observed > latest):
            latest = observed
        if ack.get("error") or ack.get("intake_status") in {"failed", "error"}:
            failures += 1
            continue
        hashes = ack.get("receipt_hashes", {})
        if isinstance(hashes, dict):
            identities.update(k.split("__attempt-", 1)[0] for k in hashes if safe_run(k))
    return identities, latest, failures


def local_gpu_probe():
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,utilization.gpu,memory.used,memory.total",
             "--format=csv,noheader,nounits"], capture_output=True, text=True,
            timeout=3, check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        rows = list(csv.reader(io.StringIO(result.stdout)))
        row = next((r for r in rows if len(r) == 4 and "5060" in r[0]), None)
        if row:
            return {"available": True, "utilizationPercent": number(row[1]),
                    "memoryUsedMiB": number(row[2]), "memoryTotalMiB": number(row[3]),
                    "observedAt": iso(utc_now())}
    except (OSError, subprocess.SubprocessError):
        pass
    return {"available": False}


def local_process_probe(repo_root):
    if os.name != "nt":
        return {"available": False}
    # Repo root travels as an environment value, never interpolated shell code.
    script = r"""
$r = $env:PHASE1_OPS_REPO_ROOT.Replace('/', '\')
$a = @(Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" -ErrorAction Stop)
$rootPattern = [regex]::Escape($r) + '(?:[\\\s"'']|$)'
$p = @($a | Where-Object { $_.CommandLine -and $_.CommandLine.Replace('/', '\') -match $rootPattern })
$cpuUnbound = @($a | Where-Object { $_.CommandLine -and
  $_.CommandLine.Replace('/', '\') -notmatch $rootPattern -and
  $_.CommandLine -match '(?:^|[\\/\s"''])(?:watch_phase1_completed_intake|receive_phase1_completed)\.py(?:[\s"'']|$)' }).Count
function Seen($name, $tag) { return [bool](@($p | Where-Object {
  $_.CommandLine -match ('(?:^|[\\/\s""''])' + [regex]::Escape($name) + '(?:[\s""'']|$)') -and
  $_.CommandLine.Contains($tag) }).Count) }
@{ available=$true; cpuVerified=($cpuUnbound -eq 0);
   'stage-c'=((Seen 'run_phase1_stages.py' 'local-5060-stage-c-v1') -or (Seen 'run.py' 'stagec_5060_v1'));
   'intake-c'=(Seen 'watch_phase1_completed_intake.py' 'consumer-stagec-20260929-v1');
   'intake-8000'=(Seen 'watch_phase1_completed_intake.py' 'consumer-rtx8000-20260929-v1');
   transfer=(Seen 'receive_phase1_completed.py' 'rtx8000-intake-20260929-v2') } | ConvertTo-Json -Compress
"""
    env = os.environ.copy()
    env["PHASE1_OPS_REPO_ROOT"] = str(repo_root)
    try:
        result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
                                capture_output=True, text=True, timeout=3, check=True, env=env,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        values = json.loads(result.stdout)
        return {key: values.get(key) is True for key in
                ("available", "cpuVerified", "stage-c", "intake-c", "intake-8000", "transfer")}
    except (OSError, ValueError, subprocess.SubprocessError):
        return {"available": False}


def current_step(root, current_run):
    if not current_run:
        return "packaging"
    logs = children(root, current_run + "__attempt-*/run.log")
    if not logs:
        return "starting"
    path = max(logs, key=lambda p: mtime(p) or datetime.min.replace(tzinfo=timezone.utc))
    try:
        with path.open("rb") as stream:
            stream.seek(max(0, path.stat().st_size - 8192))
            lines = stream.read(8192).decode("utf-8", errors="replace").splitlines()
    except OSError:
        return "unknown"
    for line in reversed(lines):
        lower = line.lower()
        if any(word in lower for word in ("generating", "saved:", "figures")):
            return "plotting"
        if any(word in lower for word in ("test shape", "metrics=", "mse:", "testing")):
            return "evaluation"
        if re.search(r"\bepoch\b", lower):
            return "training"
    return "starting"


def task(identifier, label, hardware, status, completed, total, observed, source,
         detail, now, current_run=None, **extra):
    return {"id": identifier, "label": label, "hardwareId": hardware, "status": status,
            "currentRun": current_run, "completed": completed, "total": total,
            "updatedAt": iso(observed) if observed else None, "source": source,
            "detail": detail, "freshness": freshness(observed, now), **extra}


def build_snapshot(repo_root, now=None, gpu_probe=None, process_probe=None):
    repo_root = Path(repo_root).resolve()
    now = now or utc_now()
    phase = repo_root / "reproduction/results/phase1"
    local_root = phase / "local-5060-stage-c-v1"
    remote_root = phase / "rtx8000-intake-20260929-v2"
    local_progress = read_json(local_root / "batch_progress.json")
    local_completed, local_receipt_time = completed_receipts(local_root)
    local_updated = timestamp(local_progress.get("updated_at_utc")) or local_receipt_time
    local_run = safe_run(local_progress.get("current_run"))
    snapshots = [p for p in children(remote_root / "snapshots") if p.is_dir()]
    latest_snapshot = max(snapshots, key=lambda p: p.stat().st_mtime) if snapshots else None
    remote_progress = read_json(latest_snapshot / "batch_progress.json") if latest_snapshot else {}
    remote_health = read_json(latest_snapshot / "remote_health.json") if latest_snapshot else {}
    remote_health_time = timestamp(remote_health.get("observedAt"))
    remote_health_fresh = freshness(remote_health_time, now) == "fresh"
    remote_process_verified = remote_health_fresh and isinstance(remote_health.get("runnerAlive"), bool)
    remote_updated = timestamp(remote_progress.get("updated_at_utc"))
    received_at = mtime(latest_snapshot) if latest_snapshot else None
    remote_completed, remote_receipt_time = completed_receipts(remote_root / "attempts")
    intake_c, intake_c_time, intake_c_fail = consumer_receipts(phase / "consumer-stagec-20260929-v1")
    intake_remote, intake_remote_time, intake_remote_fail = consumer_receipts(phase / "consumer-rtx8000-20260929-v1")
    p4_report = read_json(phase / "intake-p4-20260929-v1/report.json")
    p4_summary = p4_report.get("summary", {})
    p4_summary = p4_summary if isinstance(p4_summary, dict) else {}
    p4_count = count(p4_summary.get("eligible_packages"))
    p4_time = timestamp(p4_report.get("completed_at_utc") or p4_report.get("created_at_utc"))
    bridge_report = read_json(phase / "checkpoint-forward-5060-v1/report.json")
    bridge_results = bridge_report.get("results", [])
    bridge_count = len(bridge_results) if isinstance(bridge_results, list) else 0
    bridge_time = timestamp(bridge_report.get("created_at_utc"))
    try:
        gpu = (gpu_probe or local_gpu_probe)()
    except Exception:
        gpu = {"available": False}
    try:
        processes = (process_probe or (lambda: local_process_probe(repo_root)))()
    except Exception:
        processes = {"available": False}
    processes = processes if isinstance(processes, dict) else {}
    gpu = gpu if isinstance(gpu, dict) else {}
    verified = processes.get("available") is True
    cpu_verified = verified and processes.get("cpuVerified", True)
    local_status = "running" if verified and processes.get("stage-c") else (
        "reported-running" if local_progress.get("status") == "running" and freshness(local_updated, now) == "fresh"
        else "stale" if local_progress.get("status") == "running" else "completed" if local_progress.get("status") in {"completed", "completed_unreviewed"} else "unknown")
    remote_fresh = freshness(remote_updated, now)
    remote_status = ("reported-running" if remote_progress.get("status") == "running" and remote_fresh == "fresh"
                     else "stale" if remote_progress.get("status") == "running" else
                     "completed" if remote_progress.get("status") == "completed" else "unknown")
    if remote_process_verified:
        remote_status = "running" if remote_health["runnerAlive"] else "idle"
    remote_observed = remote_health_time if remote_process_verified else remote_updated
    remote_gpu_available = remote_health_fresh and remote_health.get("gpuProbeSucceeded") is True
    local_total = count(local_progress.get("total_selected"), None)
    remote_total = count(remote_progress.get("total_selected"), None)
    transfer_state = "running" if verified and processes.get("transfer") else "observed" if freshness(received_at, now) == "fresh" else "stale" if received_at else "unknown"
    cpu_busy = verified and (processes.get("intake-c") or processes.get("intake-8000") or processes.get("transfer"))
    hardware = [
        {"id": "local-5060", "label": "RTX 5060 Ti", "kind": "gpu", "state": "busy" if local_status == "running" else "observed" if gpu.get("available") else "unknown",
         "observedAt": iso(timestamp(gpu.get("observedAt")) or now) if gpu.get("available") else None,
         "utilizationPercent": number(gpu.get("utilizationPercent")), "memoryUsedMiB": number(gpu.get("memoryUsedMiB")),
         "memoryTotalMiB": number(gpu.get("memoryTotalMiB")), "detail": "Local NVIDIA observation; utilization is a point-in-time sample."},
        {"id": "local-cpu", "label": "Local CPU", "kind": "cpu", "state": "busy" if cpu_busy else "idle" if cpu_verified else "unknown",
         "observedAt": iso(now) if cpu_verified or cpu_busy else None, "utilizationPercent": None, "memoryUsedMiB": None,
         "memoryTotalMiB": None, "detail": "Known receiver and CPU intake processes verified." if cpu_verified or cpu_busy else "Process binding to this repository is unverified; receipt progress remains readable."},
        {"id": "remote-8000", "label": "Remote RTX 8000", "kind": "gpu", "state": remote_status,
         "observedAt": iso(remote_health_time) if remote_gpu_available else iso(remote_observed) if remote_observed else None,
         "utilizationPercent": number(remote_health.get("utilizationPercent")) if remote_gpu_available else None,
         "memoryUsedMiB": number(remote_health.get("memoryUsedMiB")) if remote_gpu_available else None,
         "memoryTotalMiB": number(remote_health.get("memoryTotalMiB")) if remote_gpu_available else None,
         "detail": "Fresh read-only receiver telemetry verifies remote runner state." if remote_process_verified else "Receiver metadata reports runner state; remote process and GPU health are unverified."},
        {"id": "p4-archive", "label": "P4 archive", "kind": "archive", "state": "released", "observedAt": iso(p4_time) if p4_time else None,
         "utilizationPercent": None, "memoryUsedMiB": None, "memoryTotalMiB": None, "detail": "Historical packages; P4 is released."},
        {"id": "local-intel", "label": "Intel XPU", "kind": "gpu", "state": "unassigned", "observedAt": None,
         "utilizationPercent": None, "memoryUsedMiB": None, "memoryTotalMiB": None, "detail": "XPU execution is not enabled for this workflow."},
    ]
    def intake_status(identifier, seen, failures):
        return "running" if verified and processes.get(identifier) else "failed" if failures else "observed" if seen else "unknown"
    # GPU forward replay receipts are never inferred from successful CPU intake:
    # only a written checkpoint-forward report for a received package counts.
    # Each replay run writes its own report directory (the P4 bridge and the
    # RTX 8000 supplement are separate runs), so every report is read.
    replayed = set()
    for path in children(phase, "checkpoint-forward*/report.json"):
        results = read_json(path).get("results", [])
        for result in results if isinstance(results, list) else []:
            if isinstance(result, dict) and result.get("reference_track") == "rtx8000":
                identity = safe_run(result.get("logical_run_id"))
                if identity in remote_completed:
                    replayed.add(identity)
    queue_count = len(remote_completed - replayed)
    tasks = [
        task("stage-c", "Stage C confirmation", "local-5060", local_status, len(local_completed), local_total,
             local_updated, "local batch progress + completed receipts", "Local confirmatory track; receipts await their stage gate.", now,
             local_run, currentStep=current_step(local_root, local_run), processVerified=bool(verified and processes.get("stage-c"))),
        task("remote-stage-b", "Remote Stage B", "remote-8000", remote_status, len(remote_completed), remote_total,
             remote_observed, "latest receiver snapshot + completed copies", "Fresh receiver health verifies process state." if remote_process_verified else "Runner state is reported metadata; no direct remote health probe.", now,
             safe_run(remote_progress.get("current_run")), processVerified=remote_process_verified,
             runnerUpdatedAt=iso(remote_updated) if remote_updated else None),
        task("transfer", "Completed package transfer", "local-cpu", transfer_state, len(remote_completed), remote_total,
             received_at, "receiver snapshot arrival + copied receipts", "Receiver freshness and remote runner freshness are separate observations.", now,
             processVerified=bool(verified and processes.get("transfer"))),
        task("intake-c", "Stage C CPU intake", "local-cpu", intake_status("intake-c", intake_c, intake_c_fail), len(intake_c), len(local_completed),
             intake_c_time, "CPU consumer acknowledgements", "Unique acknowledged packages; CPU intake does not perform GPU replay.", now),
        task("intake-8000", "RTX 8000 CPU intake", "local-cpu", intake_status("intake-8000", intake_remote, intake_remote_fail), len(intake_remote), len(remote_completed),
             intake_remote_time, "CPU consumer acknowledgements", "Unique acknowledged packages; descriptive integrity intake.", now),
        task("p4-archive", "P4 archived intake", "p4-archive", "completed" if p4_report else "unknown", p4_count,
             count(p4_summary.get("attempts_seen"), None), p4_time, "historical intake report",
             "Verified package integrity; historical device is released.", now),
        task("bridge-replay", "Fixed checkpoint bridge replay", "local-5060", "completed" if bridge_report else "unknown", bridge_count,
             bridge_count if bridge_report else None, bridge_time, "fixed checkpoint forward report",
             "Completed descriptive forwards; numerical equivalence and pooling are not claimed.", now),
        task("gpu-replay-queue", "RTX 8000 GPU replay queue", "local-5060",
             "empty" if not remote_completed else "completed" if not queue_count else "waiting-resource",
             len(replayed), len(remote_completed),
             remote_receipt_time, "received completions minus recorded GPU replay",
             "Waiting for the single CUDA resource used by Stage C." if queue_count else
             "Every received package has a recorded descriptive forward; numerical equivalence is not claimed.", now,
             queued=queue_count),
    ]
    edges = [
        {"from": "stage-c", "to": "intake-c", "label": "completed receipts", "kind": "artifact"},
        {"from": "remote-stage-b", "to": "transfer", "label": "completed packages", "kind": "transfer"},
        {"from": "transfer", "to": "intake-8000", "label": "local copies", "kind": "artifact"},
        {"from": "intake-8000", "to": "gpu-replay-queue", "label": "integrity intake", "kind": "queue"},
        {"from": "p4-archive", "to": "bridge-replay", "label": "fixed checkpoints", "kind": "artifact"},
        {"from": "gpu-replay-queue", "to": "local-5060", "label": "await CUDA slot", "kind": "resource"},
    ]
    alerts = []
    if remote_fresh != "fresh" and not remote_process_verified:
        alerts.append({"id": "remote-observation", "level": "warning", "message": "Remote runner observation is stale or unavailable; current remote health is unverified."})
    if not gpu.get("available"):
        alerts.append({"id": "gpu-observation", "level": "info", "message": "Local NVIDIA telemetry is unavailable."})
    if intake_c_fail or intake_remote_fail:
        alerts.append({"id": "intake-errors", "level": "warning", "message": "A CPU intake acknowledgement recorded an error; inspect local evidence."})
    return {"schemaVersion": SCHEMA_VERSION, "observedAt": iso(now), "readOnly": True,
            "hardware": hardware, "tasks": tasks, "edges": edges, "alerts": alerts}


class StatusCache:
    def __init__(self, repo_root, ttl=5, builder=build_snapshot):
        self.repo_root = Path(repo_root)
        self.ttl = ttl
        self.builder = builder
        self.lock = threading.Lock()
        self.value = None
        self.expires = 0

    def get(self):
        with self.lock:
            if self.value is None or time.monotonic() >= self.expires:
                self.value = self.builder(self.repo_root)
                self.expires = time.monotonic() + self.ttl
            return self.value


def make_handler(cache):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def response(self, status, data):
            origin = self.headers.get("Origin")
            payload = json.dumps(data, allow_nan=False, separators=(",", ":")).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            if origin in ALLOWED_ORIGINS:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            if self.headers.get("Origin") and self.headers["Origin"] not in ALLOWED_ORIGINS:
                return self.response(403, {"error": "origin forbidden", "readOnly": True})
            path = urlsplit(self.path).path
            if path == "/health":
                return self.response(200, {"status": "ok", "readOnly": True, "schemaVersion": SCHEMA_VERSION})
            if path != "/status":
                return self.response(404, {"error": "not found", "readOnly": True})
            try:
                self.response(200, cache.get())
            except Exception:
                self.response(503, {"error": "observation unavailable", "readOnly": True})

        def do_POST(self):
            self.response(405, {"error": "read-only service", "readOnly": True})

        do_PUT = do_DELETE = do_PATCH = do_OPTIONS = do_POST
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--port", type=int, default=8970)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve(strict=True)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(StatusCache(repo_root)))
    print(f"Read-only operational status on http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
