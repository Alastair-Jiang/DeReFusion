"""Fail-closed release entry for a bound compression replay attempt (v2).

This module is the reviewed replacement for the historical release() paths in
compression_replay.py and compression_pilot_2026_10_13/run_pilot_v1.py, which
gate the same prerequisites with assert statements that disappear under
"python -O". Those historical files are frozen and are not modified here.

IMPORTANT: those historical files, and the historical PREPARATION_V1.json this
entry pins, are NOT part of the main-baseline tree. They exist only on the
docs/project-status-catalog-2026-10-10 candidate. On a tree that does not carry
them the entry cannot pass: an existing historical protocol has no replay
object and fails at "protocol has no replay object", while a new-schema
protocol that pins the missing path fails at "protocol code entry is missing
on disk". It therefore cannot be exercised against real historical records on
the main baseline. That is intended, not a defect. Note also that
replay.runner_sha256 is mandatory, so no pre-existing protocol satisfies this
entry.

Revision note (after external review): the runner is now pinned by the
protocol, the attempt directory is confined to the replay area, a non-git
checkout requires an explicit fixture flag, every attempt record must be a
regular file, and pin fields must be present on both sides. The binding above
this module is its SHA-256, not the label.

Design rules:

* Every prerequisite failure raises GateError; there is no assert in this
  file, so behaviour is identical under "python" and "python -O".
* The release record is written only after every check passes, only with
  --write, and never overwrites an existing record.
* The historical preparation used for the pin cross-check is not a free
  parameter: it must be pinned in protocol["replay"]["code_sha256"] and its
  bytes are re-hashed before use.
* This module reads metadata only. It never trains, fits, scores, downloads
  or touches private arrays.

Scope of the guarantee: the gate refuses to proceed when the protocol,
authorization, runner, preparation and synthetic records are mutually
inconsistent or when a pinned byte changed. It cannot make a fabricated
protocol trustworthy, because the protocol and the authorization that names
its hash are both repository files. The human decision recorded in
authorization.decision_owner is the only anchor above this gate; the gate
verifies consistency, not the legitimacy of that decision.

A future execution protocol binds this file by SHA-256 and declares
replay.gate == GATE_VERSION, replay.gate_implementation_sha256 and
replay.runner_sha256. Because the runner must be written before the protocol,
a future attempt generator must emit the wrapper first, hash it, and only then
write the protocol.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath

GATE_VERSION = "compression-replay-release/v2"
REQUIRED_SCOPE = "two-arm-validation-replay"
ARMS = ("raw96", "mixed48")
ROLES = ("train", "validation")
PIN_FIELDS = ("sha256", "manifest_sha256", "keys_count", "keys_sha256")

PROTOCOL_NAME = "PROTOCOL_V1.json"
AUTHORIZATION_NAME = "EXECUTION_AUTHORIZATION.json"
SYNTHETIC_NAME = "SYNTHETIC_CHECK_V1.json"
PREPARATION_NAME = "PREPARATION_V1.json"
RELEASE_NAME = "EXECUTION_RELEASE_V1.json"
RUNNER_NAME = "run_pilot_v1.py"

REPLAY_AREA = "data/compression-replay-attempts"
ATTEMPT_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")

HISTORICAL_PREPARATION = (
    "research_work/project_management_2026_10_10/"
    "compression_pilot_2026_10_13/PREPARATION_V1.json"
)

HEX40 = re.compile(r"[0-9a-f]{40}")
HEX64 = re.compile(r"[0-9a-f]{64}")


class GateError(RuntimeError):
    """A release prerequisite failed; no release record may be written."""


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise GateError(message)


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_object(path: Path, label: str) -> dict:
    path = Path(path)
    require(path.is_file(), f"{label} missing: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as error:
        raise GateError(f"{label} is not valid JSON: {path}") from error
    require(isinstance(value, dict), f"{label} must be a JSON object: {path}")
    return value


def resolve_within(root: Path, relative: str, label: str) -> Path:
    """Resolve a plain repository-relative path, refusing escapes."""
    root = Path(root).resolve()
    text = str(relative)
    candidate = Path(text)
    windows = PureWindowsPath(text)
    if (not text or candidate.is_absolute() or windows.drive or windows.root
            or "\\" in text or ".." in candidate.parts):
        raise GateError(f"{label} must be a plain repository-relative path: {text}")
    resolved = (root / candidate).resolve()
    if not resolved.is_relative_to(root):
        raise GateError(f"{label} escapes the repository root: {text}")
    return resolved


def check_protocol_binding(protocol: dict, gate_path: Path, root: Path) -> None:
    replay = protocol.get("replay")
    require(isinstance(replay, dict), "protocol has no replay object")
    require(replay.get("gate") == GATE_VERSION,
            f"protocol does not declare {GATE_VERSION}")
    require(replay.get("gate_implementation_sha256") == sha(gate_path),
            "protocol does not bind this gate implementation")
    head = protocol.get("head")
    require(isinstance(head, str) and HEX40.fullmatch(head) is not None,
            "protocol has no full lowercase source head")
    codes = replay.get("code_sha256")
    require(isinstance(codes, dict) and bool(codes),
            "protocol has no implementation hash set")
    for relative, expected in codes.items():
        require(isinstance(relative, str) and isinstance(expected, str)
                and HEX64.fullmatch(expected) is not None,
                f"protocol has an invalid code hash entry: {relative!r}")
        path = resolve_within(root, relative, "protocol code entry")
        require(path.is_file(),
                f"protocol code entry is missing on disk: {relative}")
        require(sha(path) == expected,
                f"protocol code entry drifted: {relative}")


def load_historical_preparation(protocol: dict, root: Path) -> tuple[dict, str]:
    """Load the pinned historical preparation and re-hash it at use time."""
    codes = protocol["replay"]["code_sha256"]
    require(HISTORICAL_PREPARATION in codes,
            "protocol does not pin the historical preparation")
    path = resolve_within(root, HISTORICAL_PREPARATION, "historical preparation")
    historical = load_object(path, "historical preparation")
    observed = sha(path)
    require(observed == codes[HISTORICAL_PREPARATION],
            "historical preparation changed after the protocol pin was checked")
    require(historical.get("result") == "PASS",
            "historical preparation is not a PASS record")
    require(isinstance(historical.get("arms"), dict),
            "historical preparation has no arm records")
    return historical, observed


def check_preparation(preparation: dict, protocol_sha: str, runner_sha: str,
                      historical: dict) -> None:
    require(preparation.get("result") == "PASS", "preparation did not pass")
    require(preparation.get("protocol_sha256") == protocol_sha,
            "preparation protocol binding differs")
    require(preparation.get("runner_sha256") == runner_sha,
            "preparation runner binding differs")
    prepared_arms = preparation.get("arms")
    historical_arms = historical.get("arms")
    require(isinstance(prepared_arms, dict) and isinstance(historical_arms, dict),
            "preparation arm records are missing")
    for arm in ARMS:
        for role in ROLES:
            prepared = prepared_arms.get(arm, {})
            pinned = historical_arms.get(arm, {})
            require(isinstance(prepared, dict) and isinstance(pinned, dict),
                    f"preparation lacks {arm}/{role}")
            prepared_role = prepared.get(role)
            pinned_role = pinned.get(role)
            require(isinstance(prepared_role, dict) and isinstance(pinned_role, dict),
                    f"preparation lacks {arm}/{role}")
            for field in PIN_FIELDS:
                prepared_value = prepared_role.get(field)
                pinned_value = pinned_role.get(field)
                require(prepared_value is not None and pinned_value is not None,
                        f"preparation pin absent for {arm}/{role}/{field}")
                if field == "keys_count":
                    require(isinstance(prepared_value, int) and isinstance(pinned_value, int)
                            and not isinstance(prepared_value, bool)
                            and not isinstance(pinned_value, bool),
                            f"preparation pin has the wrong type for {arm}/{role}/{field}")
                else:
                    require(isinstance(prepared_value, str) and isinstance(pinned_value, str)
                            and HEX64.fullmatch(prepared_value) is not None
                            and HEX64.fullmatch(pinned_value) is not None,
                            f"preparation pin has the wrong type for {arm}/{role}/{field}")
                require(prepared_value == pinned_value,
                        f"preparation pin differs for {arm}/{role}/{field}")


def resolve_current_head(root: Path, override: str | None,
                         allow_fixture: bool = False) -> str:
    """Return the head to compare, refusing to let an override hide a git drift."""
    actual = None
    try:
        actual = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True,
            stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.SubprocessError):
        actual = None
    if actual is None:
        require(allow_fixture,
                "cannot determine current HEAD; a non-git --root requires "
                "--allow-non-git-fixture and is for synthetic fixtures only")
        require(override is not None,
                "a non-git fixture root requires --current-head")
        return override
    if override is None:
        return actual
    require(actual == override, "declared current head differs from git HEAD")
    return override


def require_regular(path: Path, label: str) -> None:
    require(path.is_file(), f"{label} missing: {path}")
    require(not path.is_symlink(), f"{label} must not be a symlink: {path}")


def check_release_prerequisites(*, attempt: Path, root: Path, current_head: str,
                                gate_path: Path) -> dict:
    """Verify every binding; raise GateError on the first failure."""
    attempt = Path(attempt).resolve()
    root = Path(root).resolve()
    require(attempt.is_dir(), f"attempt directory missing: {attempt}")
    require(attempt.is_relative_to(root),
            "attempt directory is outside the repository root")
    require(attempt.is_relative_to(root / REPLAY_AREA),
            f"attempt directory must live under {REPLAY_AREA}")
    require(attempt.parent == (root / REPLAY_AREA),
            f"attempt directory must be a direct child of {REPLAY_AREA}")
    require(ATTEMPT_NAME.fullmatch(attempt.name) is not None,
            "attempt directory name must be letters, digits, underscore or hyphen")

    protocol_path = attempt / PROTOCOL_NAME
    synthetic_path = attempt / SYNTHETIC_NAME
    preparation_path = attempt / PREPARATION_NAME
    authorization_path = attempt / AUTHORIZATION_NAME
    runner_path = attempt / RUNNER_NAME
    for path, label in ((protocol_path, "protocol"),
                        (authorization_path, "execution authorization"),
                        (synthetic_path, "synthetic check"),
                        (preparation_path, "preparation"),
                        (runner_path, "runner")):
        require_regular(path, label)

    protocol = load_object(protocol_path, "protocol")
    check_protocol_binding(protocol, gate_path, root)
    require(protocol.get("head") == current_head,
            "current HEAD differs from protocol head")

    protocol_sha = sha(protocol_path)
    runner_sha = sha(runner_path)
    require(protocol["replay"].get("runner_sha256") == runner_sha,
            "protocol does not bind the runner")

    authorization = load_object(authorization_path, "execution authorization")
    require(authorization.get("decision") == "APPROVED",
            "execution authorization is not APPROVED")
    require(authorization.get("scope") == REQUIRED_SCOPE,
            "execution authorization scope differs")
    require(authorization.get("head") == protocol["head"],
            "execution authorization head differs")
    require(authorization.get("protocol_sha256") == protocol_sha,
            "execution authorization protocol binding differs")
    for field in ("decision_owner", "authorization_basis"):
        value = authorization.get(field)
        require(isinstance(value, str) and bool(value.strip()),
                f"execution authorization has no {field}")
    declared_owner = protocol.get("decision_owner")
    if declared_owner is not None:
        require(declared_owner == authorization["decision_owner"],
                "protocol decision owner differs from the authorization")

    synthetic = load_object(synthetic_path, "synthetic check")
    require(synthetic.get("result") == "PASS", "synthetic check did not pass")
    require(synthetic.get("protocol_sha256") == protocol_sha,
            "synthetic protocol binding differs")
    require(synthetic.get("runner_sha256") == runner_sha,
            "synthetic runner binding differs")

    preparation = load_object(preparation_path, "preparation")
    historical, historical_sha = load_historical_preparation(protocol, root)
    check_preparation(preparation, protocol_sha, runner_sha, historical)

    return {
        "gate": GATE_VERSION,
        "decision": "APPROVED",
        "head": current_head,
        "protocol_id": protocol.get("protocol_id"),
        "protocol_sha256": protocol_sha,
        "runner_sha256": runner_sha,
        "authorization_sha256": sha(authorization_path),
        "synthetic_sha256": sha(synthetic_path),
        "preparation_sha256": sha(preparation_path),
        "historical_preparation_sha256": historical_sha,
        "decision_owner": authorization["decision_owner"],
        "branch": protocol.get("branch"),
        "resources": protocol.get("resources"),
        "code_sha256": dict(sorted(protocol["replay"]["code_sha256"].items())),
        "scope": REQUIRED_SCOPE,
    }


def write_release(attempt: Path, bindings: dict) -> Path:
    """Write the release record; never overwrite an existing one."""
    attempt = Path(attempt)
    release_path = attempt / RELEASE_NAME
    require(not release_path.exists(),
            f"release record already exists: {RELEASE_NAME}")
    payload = {"timestamp_utc": utc(), **bindings}
    try:
        with release_path.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    except FileExistsError as error:
        raise GateError("release record already exists: " + RELEASE_NAME) from error
    return release_path


def default_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--current-head")
    parser.add_argument("--allow-non-git-fixture", action="store_true",
                        help="permit a synthetic non-git root; never use for a real release")
    parser.add_argument("--write", action="store_true",
                        help="write EXECUTION_RELEASE_V1.json after every check passes")
    args = parser.parse_args(argv)
    root = (args.root or default_root()).resolve()
    attempt = args.attempt.resolve()
    try:
        current_head = resolve_current_head(
            root, args.current_head, allow_fixture=args.allow_non_git_fixture)
        bindings = check_release_prerequisites(
            attempt=attempt, root=root, current_head=current_head,
            gate_path=Path(__file__).resolve())
        if args.write:
            bindings["release_path"] = str(write_release(attempt, bindings))
        print(json.dumps({"gate": GATE_VERSION, "result": "PASS", **bindings},
                         indent=2))
        return 0
    except GateError as error:
        print(json.dumps({"gate": GATE_VERSION, "result": "BLOCKED",
                          "reason": str(error)}, indent=2))
        return 2
    except Exception as error:  # fail closed on unexpected errors too
        print(json.dumps({"gate": GATE_VERSION, "result": "BLOCKED",
                          "reason": f"{type(error).__name__}: {error}"}, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
