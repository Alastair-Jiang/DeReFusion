"""Synthetic-only tests for the fail-closed release entry.

No private arrays, no fitting, no scoring, no historical rewrites. Every case
uses a temporary fake repository so the real attempts area is never touched.
"""
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from reproduction.analysis import compression_replay_release_v2 as gate

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = Path(gate.__file__).resolve()
HEAD = "a" * 40
PIN_FIELDS = gate.PIN_FIELDS


class ReleaseGateV2Test(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.root = base / "root"
        self.attempt = self.root / "data/compression-replay-attempts/test"
        self.attempt.mkdir(parents=True)
        self.engine = self.root / "pinned/engine.py"
        self.engine.parent.mkdir()
        self.engine.write_text("# synthetic engine\n", encoding="utf-8")
        self.historical_path = self.root / gate.HISTORICAL_PREPARATION
        self.historical_path.parent.mkdir(parents=True)
        self.runner = self.attempt / gate.RUNNER_NAME
        self.runner.write_text("# synthetic runner\n", encoding="utf-8")
        self.protocol_path = self.attempt / gate.PROTOCOL_NAME
        self.historical = {"result": "PASS", "arms": {
            arm: {role: {"sha256": (arm + role).encode().hex()[:64].ljust(64, "0"),
                         "manifest_sha256": "1" * 64,
                         "keys_count": 7,
                         "keys_sha256": "2" * 64}
                   for role in gate.ROLES}
            for arm in gate.ARMS}}
        self.write(self.historical_path, self.historical)
        self.protocol = {
            "protocol_id": "synthetic-protocol",
            "head": HEAD,
            "replay": {
                "gate": gate.GATE_VERSION,
                "gate_implementation_sha256": gate.sha(GATE_PATH),
                "code_sha256": {
                    "pinned/engine.py": gate.sha(self.engine),
                    gate.HISTORICAL_PREPARATION: gate.sha(self.historical_path),
                },
            },
        }
        self.write(self.protocol_path, self.protocol)
        self.protocol_sha = gate.sha(self.protocol_path)
        self.runner_sha = gate.sha(self.runner)
        self.preparation = {"result": "PASS", "protocol_sha256": self.protocol_sha,
                            "runner_sha256": self.runner_sha,
                            "arms": json.loads(json.dumps(self.historical["arms"]))}
        self.synthetic = {"result": "PASS", "protocol_sha256": self.protocol_sha,
                          "runner_sha256": self.runner_sha}
        self.authorization = {"decision": "APPROVED", "scope": gate.REQUIRED_SCOPE,
                              "head": HEAD, "protocol_sha256": self.protocol_sha,
                              "decision_owner": "synthetic lead",
                              "authorization_basis": "synthetic gate test only"}
        self.write_all()

    @staticmethod
    def write(path, value):
        Path(path).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def write_all(self):
        self.write(self.attempt / gate.SYNTHETIC_NAME, self.synthetic)
        self.write(self.attempt / gate.PREPARATION_NAME, self.preparation)
        self.write(self.attempt / gate.AUTHORIZATION_NAME, self.authorization)

    def rewrite_protocol(self):
        self.write(self.protocol_path, self.protocol)
        self.protocol_sha = gate.sha(self.protocol_path)
        for record in (self.preparation, self.synthetic):
            record["protocol_sha256"] = self.protocol_sha
        self.authorization["protocol_sha256"] = self.protocol_sha
        self.write_all()

    def check(self, current_head=HEAD):
        return gate.check_release_prerequisites(
            attempt=self.attempt, root=self.root, current_head=current_head,
            gate_path=GATE_PATH)

    def cli(self, *extra, optimized=False, expect=None):
        command = [sys.executable]
        if optimized:
            command.append("-O")
        command += ["-m", "reproduction.analysis.compression_replay_release_v2",
                    "--attempt", str(self.attempt), "--root", str(self.root),
                    "--current-head", HEAD, *extra]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if expect is not None:
            self.assertEqual(result.returncode, expect, result.stdout + result.stderr)
        return result

    # --- positive paths -------------------------------------------------

    def test_valid_bindings_pass(self):
        bindings = self.check()
        self.assertEqual(bindings["gate"], gate.GATE_VERSION)
        self.assertEqual(bindings["decision"], "APPROVED")
        self.assertEqual(bindings["head"], HEAD)
        self.assertEqual(bindings["protocol_id"], "synthetic-protocol")

    def test_cli_passes_in_normal_mode(self):
        result = self.cli(expect=0)
        self.assertIn('"result": "PASS"', result.stdout)

    def test_cli_passes_under_optimized_python(self):
        result = self.cli(optimized=True, expect=0)
        self.assertIn('"result": "PASS"', result.stdout)

    # --- protocol binding ----------------------------------------------

    def test_missing_protocol_fails_closed(self):
        self.protocol_path.unlink()
        with self.assertRaisesRegex(gate.GateError, "protocol missing"):
            self.check()

    def test_malformed_protocol_fails_closed(self):
        self.protocol_path.write_text("{not json", encoding="utf-8")
        with self.assertRaisesRegex(gate.GateError, "not valid JSON"):
            self.check()

    def test_protocol_must_declare_gate_version(self):
        self.protocol["replay"]["gate"] = "compression-replay-release/v1"
        self.rewrite_protocol()
        with self.assertRaisesRegex(gate.GateError, "does not declare"):
            self.check()

    def test_protocol_must_bind_gate_implementation(self):
        del self.protocol["replay"]["gate_implementation_sha256"]
        self.rewrite_protocol()
        with self.assertRaisesRegex(gate.GateError, "bind this gate"):
            self.check()

    def test_protocol_head_must_be_lowercase_hex(self):
        self.protocol["head"] = "A" * 40
        self.rewrite_protocol()
        with self.assertRaisesRegex(gate.GateError, "lowercase source head"):
            self.check()

    def test_head_drift_fails_closed(self):
        with self.assertRaisesRegex(gate.GateError, "HEAD differs"):
            self.check(current_head="b" * 40)

    def test_pinned_code_drift_fails_closed(self):
        self.engine.write_text("# changed after protocol\n", encoding="utf-8")
        with self.assertRaisesRegex(gate.GateError, "code entry drifted"):
            self.check()

    def test_pinned_code_missing_fails_closed(self):
        self.engine.unlink()
        with self.assertRaisesRegex(gate.GateError, "missing on disk"):
            self.check()

    def test_pinned_code_path_escape_fails_closed(self):
        self.protocol["replay"]["code_sha256"]["../outside.py"] = "0" * 64
        (self.root.parent / "outside.py").write_text("x", encoding="utf-8")
        self.rewrite_protocol()
        with self.assertRaisesRegex(gate.GateError, "plain repository-relative"):
            self.check()

    def test_historical_preparation_must_be_pinned(self):
        del self.protocol["replay"]["code_sha256"][gate.HISTORICAL_PREPARATION]
        self.rewrite_protocol()
        with self.assertRaisesRegex(gate.GateError, "does not pin the historical"):
            self.check()

    def test_attempt_outside_root_is_rejected(self):
        outside = Path(self.temp.name) / "outside-attempt"
        outside.mkdir()
        with self.assertRaisesRegex(gate.GateError, "outside the repository root"):
            gate.check_release_prerequisites(
                attempt=outside, root=self.root, current_head=HEAD,
                gate_path=GATE_PATH)

    # --- authorization --------------------------------------------------

    def test_missing_runner_fails_closed(self):
        self.runner.unlink()
        with self.assertRaisesRegex(gate.GateError, "runner missing"):
            self.check()

    def test_missing_authorization_fails_closed(self):
        (self.attempt / gate.AUTHORIZATION_NAME).unlink()
        with self.assertRaisesRegex(gate.GateError, "authorization missing"):
            self.check()

    def test_unapproved_authorization_fails_closed(self):
        self.authorization["decision"] = "NOT_APPROVED"
        self.write_all()
        with self.assertRaisesRegex(gate.GateError, "not APPROVED"):
            self.check()

    def test_unapproved_authorization_blocks_under_optimized_python(self):
        self.authorization["decision"] = "NOT_APPROVED"
        self.write_all()
        result = self.cli(optimized=True, expect=2)
        self.assertIn('"result": "BLOCKED"', result.stdout)
        self.assertIn("not APPROVED", result.stdout)

    def test_missing_authorization_blocks_under_optimized_python(self):
        (self.attempt / gate.AUTHORIZATION_NAME).unlink()
        result = self.cli(optimized=True, expect=2)
        self.assertIn("authorization missing", result.stdout)

    def test_authorization_scope_mismatch_fails_closed(self):
        self.authorization["scope"] = "single-arm-descriptive"
        self.write_all()
        with self.assertRaisesRegex(gate.GateError, "scope differs"):
            self.check()

    def test_authorization_protocol_hash_mismatch_fails_closed(self):
        self.authorization["protocol_sha256"] = "0" * 64
        self.write_all()
        with self.assertRaisesRegex(gate.GateError, "protocol binding differs"):
            self.check()

    def test_authorization_head_mismatch_fails_closed(self):
        self.authorization["head"] = "c" * 40
        self.write_all()
        with self.assertRaisesRegex(gate.GateError, "authorization head differs"):
            self.check()

    def test_authorization_without_owner_fails_closed(self):
        self.authorization["decision_owner"] = "   "
        self.write_all()
        with self.assertRaisesRegex(gate.GateError, "decision_owner"):
            self.check()

    # --- synthetic and preparation -------------------------------------

    def test_synthetic_check_must_pass(self):
        self.synthetic["result"] = "FAIL"
        self.write_all()
        with self.assertRaisesRegex(gate.GateError, "synthetic check did not pass"):
            self.check()

    def test_synthetic_runner_drift_fails_closed(self):
        self.synthetic["runner_sha256"] = "0" * 64
        self.write_all()
        with self.assertRaisesRegex(gate.GateError, "synthetic runner binding"):
            self.check()

    def test_failed_preparation_fails_closed(self):
        self.preparation["result"] = "FAIL"
        self.write_all()
        with self.assertRaisesRegex(gate.GateError, "preparation did not pass"):
            self.check()

    def test_failed_preparation_blocks_under_optimized_python(self):
        self.preparation["result"] = "FAIL"
        self.write_all()
        result = self.cli(optimized=True, expect=2)
        self.assertIn("preparation did not pass", result.stdout)

    def test_preparation_protocol_hash_drift_fails_closed(self):
        self.preparation["protocol_sha256"] = "0" * 64
        self.write_all()
        with self.assertRaisesRegex(gate.GateError, "preparation protocol binding"):
            self.check()

    def test_preparation_runner_hash_drift_fails_closed(self):
        self.preparation["runner_sha256"] = "0" * 64
        self.write_all()
        with self.assertRaisesRegex(gate.GateError, "preparation runner binding"):
            self.check()

    def test_historical_pin_drift_fails_closed(self):
        self.preparation["arms"]["mixed48"]["train"]["sha256"] = "f" * 64
        self.write_all()
        with self.assertRaisesRegex(gate.GateError, "mixed48/train/sha256"):
            self.check()

    def test_wrong_hash_blocks_under_optimized_python(self):
        self.preparation["arms"]["raw96"]["validation"]["keys_sha256"] = "e" * 64
        self.write_all()
        result = self.cli(optimized=True, expect=2)
        self.assertIn("raw96/validation/keys_sha256", result.stdout)

    # --- head resolution ------------------------------------------------

    def test_declared_head_must_match_git_head(self):
        with self.assertRaisesRegex(gate.GateError, "differs from git HEAD"):
            gate.resolve_current_head(ROOT, "b" * 40)

    def test_current_head_is_required_outside_a_git_checkout(self):
        with self.assertRaisesRegex(gate.GateError, "cannot determine current HEAD"):
            gate.resolve_current_head(self.root, None)

    def test_runner_symlink_is_rejected(self):
        target = Path(self.temp.name) / "runner-target.py"
        target.write_text("# elsewhere\n", encoding="utf-8")
        self.runner.unlink()
        try:
            self.runner.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation is not permitted for this account")
        with self.assertRaisesRegex(gate.GateError, "runner must not be a symlink"):
            self.check()

    # --- release record -------------------------------------------------

    def test_write_requires_all_checks(self):
        self.authorization["decision"] = "NOT_APPROVED"
        self.write_all()
        result = self.cli("--write", expect=2)
        self.assertIn('"result": "BLOCKED"', result.stdout)
        self.assertFalse((self.attempt / gate.RELEASE_NAME).exists())

    def test_write_emits_release_and_refuses_overwrite(self):
        result = self.cli("--write", expect=0)
        self.assertIn('"result": "PASS"', result.stdout)
        release_path = self.attempt / gate.RELEASE_NAME
        release = json.loads(release_path.read_text(encoding="utf-8"))
        self.assertEqual(release["gate"], gate.GATE_VERSION)
        self.assertEqual(release["decision"], "APPROVED")
        self.assertEqual(release["protocol_sha256"], gate.sha(self.protocol_path))
        self.assertEqual(release["runner_sha256"], gate.sha(self.runner))
        self.assertEqual(release["authorization_sha256"],
                         gate.sha(self.attempt / gate.AUTHORIZATION_NAME))
        self.assertEqual(release["head"], HEAD)
        second = self.cli("--write", expect=2)
        self.assertIn("already exists", second.stdout)

    def test_write_helper_refuses_existing_record(self):
        (self.attempt / gate.RELEASE_NAME).write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(gate.GateError, "already exists"):
            gate.write_release(self.attempt, self.check())


if __name__ == "__main__":
    unittest.main()
