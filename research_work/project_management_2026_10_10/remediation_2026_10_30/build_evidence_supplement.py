"""Build a versioned evidence supplement for the 1830 stage report's inputs.

Metadata and hashes only. This script never copies reviewer content and never
prints file bodies; it records size, hash, Git object identity, and coarse
pattern counts so a reader can decide whether an exact byte set may be
published.

Usage:
    python -m research_work.project_management_2026_10_10.remediation_2026_10_30.build_evidence_supplement \
        --local-root <primary checkout> --candidate-root <isolated worktree> \
        --output <json path>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPORT = "docs/DRF_SHRINK_STAGE_REPORT_1830_V1_2026-10-13_HASHES.json"
SCHEMA = "derefusion.evidence-supplement/v2"

CREDENTIAL = re.compile(r"(?i)password|passwd|secret|token|api[_-]?key|BEGIN [A-Z ]*PRIVATE KEY")
LOCAL_PATH = re.compile(r"(?i)(?:[A-Z]:[\\/]Users[\\/]|/Users/|/home/)")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True)


def tracked(root: Path, path: str) -> bool:
    return git(root, "ls-files", "--error-unmatch", "--", path).returncode == 0


def staged_blob(root: Path, path: str) -> str | None:
    result = git(root, "cat-file", "-e", ":" + path)
    if result.returncode != 0:
        return None
    return git(root, "rev-parse", ":" + path).stdout.decode().strip() or None


def inspect(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    return {
        "lines": text.count("\n") + (0 if text.endswith("\n") or not text else 1),
        "credential_pattern_hits": len(CREDENTIAL.findall(text)),
        "contains_local_absolute_path": bool(LOCAL_PATH.search(text)),
    }


def classify(exists: bool, in_candidate: bool) -> tuple[str, str]:
    if not exists:
        return ("missing-not-verifiable",
                "Named path is absent from the local checkout. Do not reconstruct "
                "the historical review or claim its content.")
    if in_candidate:
        return ("in-candidate-subject-to-review",
                "Exact bytes are in the candidate index. Hash equality establishes "
                "identity only; provenance, rights and content review remain open.")
    return ("local-only-not-published",
            "Present only as untracked local material. Not published; any release "
            "would need de-identification and a separate artifact-specific decision.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-root", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", default=REPORT)
    args = parser.parse_args()
    local = args.local_root.resolve()
    candidate = args.candidate_root.resolve()

    report_path = local / args.report
    report = json.loads(report_path.read_text(encoding="utf-8"))
    declared = report.get("inputs")
    if not isinstance(declared, list):
        raise SystemExit("stage report has no inputs list")

    records = []
    for entry in declared:
        path = entry["path"]
        source = local / path
        exists = source.is_file()
        observed = sha256(source) if exists else None
        in_candidate = staged_blob(candidate, path) is not None
        disposition, basis = classify(exists, in_candidate)
        record = {
            "path": path,
            "declared_sha256": entry.get("sha256"),
            "observed_sha256": observed,
            "exists": exists,
            "hash_match": bool(exists and observed == entry.get("sha256")),
            "local_tracked": tracked(local, path),
            "candidate_tracked": in_candidate,
            "candidate_git_blob": staged_blob(candidate, path),
            "disposition": disposition,
            "basis": basis,
        }
        if exists:
            record["size_bytes"] = source.stat().st_size
            record.update(inspect(source))
        records.append(record)

    summary = {
        "declared": len(records),
        "present_and_hash_matching": sum(r["hash_match"] for r in records),
        "present_but_hash_mismatch": sum(r["exists"] and not r["hash_match"] for r in records),
        "missing": sum(not r["exists"] for r in records),
        "candidate_tracked": sum(r["candidate_tracked"] for r in records),
        "local_only_not_published": sum(
            r["disposition"] == "local-only-not-published" for r in records),
        "missing_not_verifiable": sum(
            r["disposition"] == "missing-not-verifiable" for r in records),
        "credential_pattern_hits": sum(r.get("credential_pattern_hits", 0) for r in records),
    }
    output = {
        "schema": SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "subject_report": args.report,
        "subject_report_sha256": sha256(report_path),
        "local_checkout": "primary working tree (absolute path withheld)",
        "candidate_checkout": "isolated reconciliation worktree (absolute path withheld)",
        "method": (
            "Declared paths and SHA-256 from the stage report are re-observed. "
            "Presence in the candidate index is resolved through git, not by filesystem "
            "copy. Content is scanned only for credential-like and local-path patterns; "
            "no file body is copied into this record. A hash match establishes byte "
            "identity, not provenance, rights, or scientific validity."
        ),
        "summary": summary,
        "inputs": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
