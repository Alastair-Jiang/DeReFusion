"""Read-only SFTP receiver for completed Phase 1 packages; never fits or loads a model.

Install Paramiko only in an isolated transfer-tools environment. Passwords are
prompted interactively and held in memory. OpenSSH known_hosts is authoritative.
Only atomically published ``attempts`` directories are ready for local intake.
"""
from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import posixpath
import re
import shlex
import socket
import stat
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ("checkpoint.pth", "pred.npy", "true.npy", "metrics.npy", "run.log")
REQUIRED_METADATA = ("authorization.json", "environment_fingerprint.json", "batch_meta.json")
OPTIONAL_METADATA = ("batch_progress.json", "manifest.csv")
MARKER = ".phase1-receiver.json"
MAX_JSON_BYTES = 4 * 1024 * 1024


class IntegrityError(RuntimeError):
    """Evidence needs review; do not overwrite any existing evidence."""


def fresh_name() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ") + "-" + uuid.uuid4().hex


def remote_root_path(value: str) -> str:
    if not value.startswith("/") or "\\" in value or "\x00" in value or ".." in value.split("/"):
        raise ValueError("remote root must be an absolute POSIX path without traversal")
    result = posixpath.normpath(value)
    if result == "/":
        raise ValueError("remote root cannot be filesystem root")
    return result


def safe_name(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", value) or value in {".", ".."}:
        raise IntegrityError("unsafe remote filename")
    return value


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_receipt(raw: bytes, attempt_id: str) -> dict:
    try:
        receipt = json.loads(raw)
    except (ValueError, UnicodeError) as error:
        raise IntegrityError("invalid receipt JSON") from error
    if not isinstance(receipt, dict):
        raise IntegrityError("receipt must be an object")
    if receipt.get("status") != "completed_unreviewed":
        return receipt
    identity = re.fullmatch(r"(.+)__attempt-([0-9]+)", safe_name(attempt_id))
    if (not identity or int(identity[2]) < 1 or receipt.get("attempt_id") != attempt_id
            or receipt.get("logical_run_id") != identity[1]
            or receipt.get("attempt") != int(identity[2])):
        raise IntegrityError("receipt attempt identity differs from directory")
    hashes = receipt.get("sha256")
    if not isinstance(hashes, dict) or set(hashes) != set(ARTIFACTS):
        raise IntegrityError("receipt must bind exactly the five required artifacts")
    if any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value)
           for value in hashes.values()):
        raise IntegrityError("invalid artifact SHA256")
    return receipt


def prepare_local_root(path: Path, remote_root: str) -> Path:
    path = path.resolve()
    # In-repository output is permitted only as a dedicated Phase 1 child.
    if path == ROOT or path in ROOT.parents:
        raise ValueError("local root cannot contain the repository")
    if path.is_relative_to(ROOT) and path.parent != ROOT / "reproduction/results/phase1":
        raise ValueError("local root inside repository must be a new direct Phase 1 child")
    if path.is_relative_to(ROOT) and "intake" not in path.name:
        raise ValueError("receiver root must be an isolated intake directory")
    identity = {"receiver_version": "phase1-sftp-receiver/v2", "remote_root": remote_root}
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        marker = path / MARKER
        if not marker.is_file() or json.loads(marker.read_text(encoding="utf-8")) != identity:
            raise FileExistsError("existing local root is not this receiver's isolated directory")
    else:
        path.mkdir(parents=True, exist_ok=True)
        with (path / MARKER).open("x", encoding="utf-8") as stream:
            json.dump(identity, stream, indent=2)
    for name in ("attempts", "incoming", "quarantine", "snapshots", "reports"):
        directory = path / name
        if directory.is_symlink():
            raise IntegrityError("receiver subdirectory cannot be a symlink")
        directory.mkdir(exist_ok=True)
    return path


class Receiver:
    def __init__(self, local_root: Path, remote_root: str, expected_authorization_sha256: str | None = None,
                 progress=print):
        self.remote_root = remote_root_path(remote_root)
        self.local_root = prepare_local_root(local_root, self.remote_root)
        if expected_authorization_sha256 is not None and not re.fullmatch(r"[0-9a-f]{64}", expected_authorization_sha256):
            raise ValueError("expected authorization SHA256 must be 64 lowercase hexadecimal characters")
        self.expected_authorization_sha256 = expected_authorization_sha256
        self.progress = progress
        self.deadline: float | None = None
        self.manifest_hash_verified = False
        # Only process-lifetime verified receipt bytes are cached. Restart
        # verifies every already-published artifact again, including checkpoints.
        self.verified: dict[str, bytes] = {}

    def remote_file(self, sftp, path: str):
        info = sftp.lstat(path)
        if not stat.S_ISREG(info.st_mode):
            raise IntegrityError("remote input is not a regular file: " + path)
        return info

    def read_small(self, sftp, path: str) -> bytes:
        info = self.remote_file(sftp, path)
        if info.st_size > MAX_JSON_BYTES:
            raise IntegrityError("metadata exceeds bounded size: " + path)
        with sftp.open(path, "rb") as stream:
            result = stream.read(MAX_JSON_BYTES + 1)
        if len(result) > MAX_JSON_BYTES or len(result) != info.st_size:
            raise IntegrityError("metadata changed size while reading: " + path)
        return result

    def snapshot_metadata(self, sftp, entries) -> Path:
        metadata = {}
        names = {entry.filename for entry in entries}
        optional = set(OPTIONAL_METADATA) | {
            safe_name(name) for name in names if name.endswith("manifest.csv")
        }
        for name in (*REQUIRED_METADATA, *sorted(optional - set(REQUIRED_METADATA))):
            if name not in names:
                if name in REQUIRED_METADATA:
                    raise IntegrityError("required root metadata missing: " + name)
                continue
            metadata[name] = self.read_small(sftp, posixpath.join(self.remote_root, name))
        snapshot = self.local_root / "snapshots" / fresh_name()
        snapshot.mkdir()
        for name, raw in metadata.items():
            with (snapshot / name).open("xb") as stream:
                stream.write(raw)
        return snapshot

    def validate_batch_metadata(self, snapshot: Path) -> dict:
        """Bind intake to the exact authorized remote RTX8000 supplement batch."""
        try:
            authorization_raw = (snapshot / "authorization.json").read_bytes()
            authorization = json.loads(authorization_raw)
            environment_raw = (snapshot / "environment_fingerprint.json").read_bytes()
            environment = json.loads(environment_raw)
            batch_meta = json.loads((snapshot / "batch_meta.json").read_bytes())
        except (OSError, ValueError, UnicodeError) as error:
            raise IntegrityError("batch metadata is unreadable or invalid JSON") from error
        if not all(isinstance(item, dict) for item in (authorization, environment, batch_meta)):
            raise IntegrityError("authorization, environment and batch metadata must be JSON objects")
        if self.expected_authorization_sha256 is None:
            raise IntegrityError("trusted expected authorization SHA256 was not supplied")
        if hashlib.sha256(authorization_raw).hexdigest() != self.expected_authorization_sha256:
            raise IntegrityError("authorization does not match the trusted expected SHA256")
        if authorization.get("authorization_version") != "phase1-remote-supplement-auth/v1":
            raise IntegrityError("unsupported batch authorization version")
        protocol_version = authorization.get("protocol_version")
        if not isinstance(protocol_version, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", protocol_version):
            raise IntegrityError("authorization has no valid protocol version")
        batch_id = safe_name(authorization.get("batch_id"))
        if batch_id != posixpath.basename(self.remote_root):
            raise IntegrityError("authorized batch ID differs from the requested remote root")
        if posixpath.normpath(str(authorization.get("output_root", ""))) != self.remote_root:
            raise IntegrityError("authorized output root differs from the requested remote root")
        if authorization.get("execution_track") != "nonconfirmatory_remote_gpu_supplement":
            raise IntegrityError("batch authorization is not for the remote nonconfirmatory supplement")
        stages = authorization.get("stages")
        if (not isinstance(stages, list) or not stages
                or not all(isinstance(stage, str) and stage for stage in stages)):
            raise IntegrityError("batch authorization has no valid stage list")
        if "B_screen" not in stages:
            raise IntegrityError("batch authorization does not include B_screen")
        if any(bool(authorization.get(key)) for key in
               ("pooling_authorized", "ranking_authorized", "equivalence_claim_authorized")):
            raise IntegrityError("batch authorization exceeds the receiver's descriptive-only scope")
        manifest_hash = authorization.get("manifest_sha256")
        environment_hash = authorization.get("environment_fingerprint_sha256")
        source_commit = authorization.get("git_commit")
        if not isinstance(manifest_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", manifest_hash):
            raise IntegrityError("authorization has no valid manifest hash")
        if not isinstance(environment_hash, str) or hashlib.sha256(environment_raw).hexdigest() != environment_hash:
            raise IntegrityError("environment fingerprint differs from authorization")
        if not isinstance(source_commit, str) or not re.fullmatch(r"[0-9a-f]{40}", source_commit):
            raise IntegrityError("authorization has no valid source commit")
        if environment.get("mismatches") != {} or environment.get("track") != authorization["execution_track"]:
            raise IntegrityError("environment fingerprint is not a matching passing observation")
        expected_batch_meta = {
            "authorization_sha256": hashlib.sha256(authorization_raw).hexdigest(),
            "batch_id": batch_id,
            "environment_fingerprint_sha256": environment_hash,
            "git_commit": source_commit,
            "manifest_sha256": manifest_hash,
        }
        if any(batch_meta.get(key) != value for key, value in expected_batch_meta.items()):
            raise IntegrityError("batch metadata does not match its authorization and environment")
        manifest_files = list(snapshot.glob("*manifest.csv"))
        self.manifest_hash_verified = any(file_hash(path) == manifest_hash for path in manifest_files)
        return authorization

    @staticmethod
    def validate_receipt_scope(receipt: dict, authorization: dict) -> None:
        """Reject receipts that do not belong to the authorized batch/source/stack."""
        protocol_version = authorization.get("protocol_version")
        if not isinstance(protocol_version, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", protocol_version):
            raise IntegrityError("authorization has no valid protocol version")
        expected = {
            "batch_id": authorization["batch_id"],
            "authorization_commit": authorization["git_commit"],
            "environment_fingerprint_sha256": authorization["environment_fingerprint_sha256"],
            "execution_track": authorization["execution_track"],
            "protocol_version": protocol_version,
        }
        if any(receipt.get(key) != value for key, value in expected.items()):
            raise IntegrityError("receipt identity differs from the authorized batch")
        if receipt.get("stage") not in authorization["stages"]:
            raise IntegrityError("receipt stage is outside the authorized batch")

    def verify_existing(self, directory: Path, raw: bytes, receipt: dict) -> None:
        if directory.is_symlink() or not directory.is_dir():
            raise IntegrityError("published attempt is not a normal directory")
        marker = directory / "receipt.json"
        if marker.is_symlink() or not marker.is_file():
            raise IntegrityError("published receipt is missing or is not a normal file; preserved for review")
        try:
            marker_raw = marker.read_bytes()
        except OSError as error:
            raise IntegrityError("published receipt is missing or unreadable; preserved for review") from error
        if marker_raw != raw:
            raise IntegrityError("published receipt differs from remote; preserved for review")
        for name in ARTIFACTS:
            path = directory / name
            if path.is_symlink() or not path.is_file() or file_hash(path) != receipt["sha256"][name]:
                raise IntegrityError("published artifact hash mismatch; preserved for review: " + name)

    def download(self, sftp, remote: str, local: Path, expected: str) -> None:
        info = self.remote_file(sftp, remote)
        digest, transferred, next_update = hashlib.sha256(), 0, 25 * 1024 * 1024
        with sftp.open(remote, "rb") as source, local.open("xb") as target:
            # Bounded pipelining avoids one network round-trip per 32 KiB read.
            # Byte order and the full size/hash checks below remain unchanged.
            if callable(getattr(source, "prefetch", None)):
                source.prefetch(file_size=info.st_size, max_concurrent_requests=32)
            while True:
                if self.deadline is not None and time.monotonic() >= self.deadline:
                    raise TimeoutError("authorized receiver duration expired; partial files retained")
                chunk = source.read(1024 * 1024)
                if not chunk:
                    break
                target.write(chunk)
                digest.update(chunk)
                transferred += len(chunk)
                if local.name == "checkpoint.pth" and transferred >= next_update:
                    self.progress(f"checkpoint bytes {transferred}/{info.st_size}: {local.parent.name}")
                    next_update += 25 * 1024 * 1024
            target.flush()
            os.fsync(target.fileno())
        if transferred != info.st_size or digest.hexdigest() != expected:
            raise IntegrityError("artifact size or SHA256 mismatch: " + local.name)

    def receive_pass(self, sftp, remote_health: dict | None = None) -> dict:
        report = {"status": "running", "published": [], "skipped": [], "issues": [],
                  "remote_root": self.remote_root, "pooling_authorized": False,
                  "training_performed": False, "manifest_hash_verified": False, "gate_table": []}
        try:
            entries = sftp.listdir_attr(self.remote_root)
            metadata_snapshot = self.snapshot_metadata(sftp, entries)
            report["metadata_snapshot"] = str(metadata_snapshot)
            authorization = self.validate_batch_metadata(metadata_snapshot)
            report["manifest_hash_verified"] = self.manifest_hash_verified
            if remote_health is not None:
                with (metadata_snapshot / "remote_health.json").open("x", encoding="utf-8") as stream:
                    json.dump(remote_health, stream, indent=2)
            for entry in sorted(entries, key=lambda item: item.filename):
                if not stat.S_ISDIR(entry.st_mode) or "__attempt-" not in entry.filename:
                    continue
                attempt_id = safe_name(entry.filename)
                remote = posixpath.join(self.remote_root, attempt_id)
                # lstat prevents traversing a substituted symlink directory.
                if not stat.S_ISDIR(sftp.lstat(remote).st_mode):
                    raise IntegrityError("attempt directory changed type")
                try:
                    raw = self.read_small(sftp, posixpath.join(remote, "receipt.json"))
                    receipt = parse_receipt(raw, attempt_id)
                    if receipt.get("status") == "completed_unreviewed":
                        self.validate_receipt_scope(receipt, authorization)
                except FileNotFoundError:
                    continue
                except IntegrityError as error:
                    report["issues"].append({"attempt_id": attempt_id, "error": str(error)})
                    continue
                if receipt.get("status") != "completed_unreviewed":
                    continue
                published = self.local_root / "attempts" / attempt_id
                if attempt_id in self.verified and self.verified[attempt_id] == raw:
                    report["skipped"].append(attempt_id)
                    continue
                if published.exists():
                    # Any existing mismatch is a hard error: never replace it.
                    self.verify_existing(published, raw, receipt)
                    self.verified[attempt_id] = raw
                    report["skipped"].append(attempt_id)
                    continue
                incoming = self.local_root / "incoming" / (attempt_id + "--" + fresh_name())
                incoming.mkdir()
                incoming_verified = False
                try:
                    for name in ARTIFACTS:
                        self.download(sftp, posixpath.join(remote, name), incoming / name,
                                      receipt["sha256"][name])
                    if self.read_small(sftp, posixpath.join(remote, "receipt.json")) != raw:
                        raise IntegrityError("receipt changed during transfer")
                    with (incoming / "receipt.json").open("xb") as stream:
                        stream.write(raw)
                        stream.flush()
                        os.fsync(stream.fileno())
                    self.verify_existing(incoming, raw, receipt)
                    incoming_verified = True
                    if published.exists():
                        raise IntegrityError("destination appeared during transfer")
                    incoming.rename(published)
                except IntegrityError as error:
                    quarantined = self.local_root / "quarantine" / incoming.name
                    incoming.rename(quarantined)
                    report["issues"].append({"attempt_id": attempt_id, "error": str(error),
                                             "quarantine": str(quarantined)})
                    continue
                except Exception as error:
                    # Preserve bytes under incoming and record their exact location
                    # before propagating a transport or publication failure.
                    issue = {
                        "attempt_id": attempt_id,
                        "error": f"{type(error).__name__}: {error}",
                    }
                    if incoming_verified:
                        issue["incoming_verified_package"] = str(incoming)
                        issue["state"] = "complete package verified; publication failed; retained"
                    else:
                        issue["incoming_partial"] = str(incoming)
                        issue["state"] = "incomplete transfer retained; not published"
                    report["issues"].append(issue)
                    raise
                self.verified[attempt_id] = raw
                report["published"].append(attempt_id)
                self.progress("published completed package: " + attempt_id)
            report["status"] = "requires_resolution" if report["issues"] else "completed_descriptive_only"
            return report
        except Exception as error:
            report["status"] = "failed"
            report["error"] = f"{type(error).__name__}: {error}"
            raise
        finally:
            report["gate_table"] = [
                {"check": "transport integrity", "input": "receipt and five SHA256-bound files",
                 "status": report["status"], "evidence": "published and issues records",
                 "next_permitted_action": "local CPU intake and fixed-checkpoint diagnostics"},
                {"check": "scientific use", "input": "received packages", "status": "requires-resolution",
                 "evidence": ("transfer only; authorized manifest bytes verified" if report["manifest_hash_verified"]
                              else "transfer only; authorization declares a manifest hash but no matching manifest bytes were received"),
                 "next_permitted_action": ("approved intake and protocol review" if report["manifest_hash_verified"]
                                           else "reconcile the authorized manifest bytes before scientific intake or evaluation")}]
            with (self.local_root / "reports" / (fresh_name() + ".json")).open("x", encoding="utf-8") as stream:
                json.dump(report, stream, indent=2)


def read_remote_health(client) -> dict:
    """Fixed infrastructure observation; no secrets, writes, or training control."""
    source = """import csv,datetime,json,subprocess
def probe(argv):
 result=subprocess.run(argv,capture_output=True,text=True,timeout=4)
 return result.returncode,result.stdout.strip()
status={"observedAt":datetime.datetime.now(datetime.timezone.utc).isoformat(),"probeSucceeded":True}
code,output=probe(["nvidia-smi","--query-gpu=name,utilization.gpu,memory.used,memory.total","--format=csv,noheader,nounits"])
status["gpuProbeSucceeded"]=code==0
if code==0:
 fields=next(csv.reader(output.splitlines()))
 status.update(gpuName=fields[0].strip(),utilizationPercent=float(fields[1]),memoryUsedMiB=float(fields[2]),memoryTotalMiB=float(fields[3]))
status["tmuxAlive"]=probe(["tmux","has-session","-t","rtx8timesnet"])[0]==0
status["runnerAlive"]=probe(["pgrep","-f","run_phase1_stages.py.*rtx8000-timesnet-remaining-v1"])[0]==0
status["trainingWorkerAlive"]=probe(["pgrep","-f","run.py.*rx8_v1"])[0]==0
print(json.dumps(status))"""
    try:
        _, stdout, _ = client.exec_command("/data/envs/phase1-rx8000/bin/python -c " + shlex.quote(source), timeout=20)
        raw = stdout.read(MAX_JSON_BYTES + 1)
        if len(raw) > MAX_JSON_BYTES:
            raise ValueError("health probe response too large")
        result = json.loads(raw)
        if not isinstance(result, dict) or not result.get("observedAt"):
            raise ValueError("invalid health probe response")
        return result
    except Exception as error:
        return {"observedAt": datetime.now(timezone.utc).isoformat(), "probeSucceeded": False,
                "errorClass": type(error).__name__}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--host", required=True)
    result.add_argument("--port", type=int, default=22)
    result.add_argument("--user", required=True)
    result.add_argument("--remote-root", default="/data/coding/DeReFusion/reproduction/results/phase1/rtx8000-timesnet-remaining-v1")
    result.add_argument("--local-root", type=Path, required=True)
    mode = result.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true", help="default: receive currently completed packages and exit")
    mode.add_argument("--poll-seconds", type=float, help="foreground polling interval, at least 10 seconds")
    result.add_argument("--max-hours", type=float, default=8, help="bounded polling duration; set remaining authorized GPU budget")
    result.add_argument("--known-hosts", type=Path, default=Path.home() / ".ssh/known_hosts")
    result.add_argument("--remote-health", action="store_true",
                        help="also run a fixed read-only GPU/tmux/process probe on the authorized worker")
    result.add_argument("--expected-authorization-sha256", required=True,
                        help="trusted SHA256 of the exact authorization.json for this batch")
    return result


def main() -> int:
    args = parser().parse_args()
    if (not 1 <= args.port <= 65535 or not 0 < args.max_hours <= 8
            or args.poll_seconds is not None and args.poll_seconds < 10):
        raise SystemExit("port must be valid, max-hours in (0, 8], polling at least 10 seconds")
    if not args.known_hosts.is_file():
        raise SystemExit("existing OpenSSH known_hosts is required; receiver never accepts new host keys")
    import paramiko  # isolated transfer-tools environment only; no runtime installation
    receiver = Receiver(args.local_root, args.remote_root,
                        expected_authorization_sha256=args.expected_authorization_sha256)
    password = getpass.getpass(f"SSH password for {args.user}@{args.host}: ")
    deadline = time.monotonic() + args.max_hours * 3600
    receiver.deadline = deadline
    result = 0
    try:
        while time.monotonic() < deadline:
            client = paramiko.SSHClient()
            client.load_host_keys(str(args.known_hosts))
            client.set_missing_host_key_policy(paramiko.RejectPolicy())
            try:
                client.connect(args.host, port=args.port, username=args.user, password=password,
                               look_for_keys=False, allow_agent=False, timeout=30,
                               banner_timeout=30, auth_timeout=30)
                with client.open_sftp() as sftp:
                    sftp.get_channel().settimeout(60)
                    report = receiver.receive_pass(
                        sftp, read_remote_health(client) if args.remote_health else None)
                print(json.dumps({key: report[key] for key in ("status", "published", "skipped", "issues")}))
                if report["issues"]:
                    result = 2
            except (paramiko.AuthenticationException, paramiko.BadHostKeyException, IntegrityError) as error:
                print(f"receiver stopped: {type(error).__name__}: {error}")
                return 2
            except (paramiko.SSHException, socket.timeout, OSError, EOFError) as error:
                print(f"transport interrupted; partial evidence retained: {type(error).__name__}: {error}")
                if args.poll_seconds is None:
                    return 2
            finally:
                client.close()
            if args.poll_seconds is None:
                break
            time.sleep(min(args.poll_seconds, max(0, deadline - time.monotonic())))
    except KeyboardInterrupt:
        print("receiver stopped; all published and partial evidence retained")
        return 130
    finally:
        password = None
    return result


if __name__ == "__main__":
    raise SystemExit(main())
