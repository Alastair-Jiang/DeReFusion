"""No network, SSH credentials, GPU, or training: small mock SFTP fixtures."""
import hashlib
import io
import json
import stat
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from reproduction.analysis import receive_phase1_completed as receiver


class MockSFTP:
    def __init__(self, files):
        self.files = files
        self.reads = []
        self.mutate_on_artifact = False
        self.fail_once = False

    def lstat(self, path):
        if path in self.files:
            return SimpleNamespace(st_mode=stat.S_IFREG, st_size=len(self.files[path]))
        if any(name.startswith(path + "/") for name in self.files):
            return SimpleNamespace(st_mode=stat.S_IFDIR, st_size=0)
        raise FileNotFoundError(path)

    def listdir_attr(self, path):
        names = {name[len(path) + 1:].split("/")[0] for name in self.files if name.startswith(path + "/")}
        return [SimpleNamespace(filename=name, st_mode=self.lstat(path + "/" + name).st_mode)
                for name in names]

    def open(self, path, mode):
        assert mode == "rb", "remote writes forbidden"
        self.reads.append(path)
        if path.endswith("checkpoint.pth") and self.fail_once:
            self.fail_once = False
            raise EOFError("transport dropped")
        if path.endswith("run.log") and self.mutate_on_artifact:
            marker = path.rsplit("/", 1)[0] + "/receipt.json"
            self.files[marker] += b" "
        return io.BytesIO(self.files[path])


class CompletedReceiverTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "rtx8000-intake-test"
        self.remote = "/results/batch"
        self.attempt = "B_screen_ASSET_MODEL_h1_s2021__attempt-01"
        environment_raw = json.dumps({"mismatches": {},
                                      "track": "nonconfirmatory_remote_gpu_supplement"}).encode()
        manifest_raw = b"synthetic frozen manifest\n"
        self.authorization = {
            "authorization_version": "phase1-remote-supplement-auth/v1",
            "batch_id": "batch", "output_root": self.remote,
            "execution_track": "nonconfirmatory_remote_gpu_supplement",
            "stages": ["B_screen"], "pooling_authorized": False,
            "ranking_authorized": False, "equivalence_claim_authorized": False,
            "manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
            "environment_fingerprint_sha256": hashlib.sha256(environment_raw).hexdigest(),
            "git_commit": "b" * 40, "protocol_version": "phase1-v1.1-2026-09-19",
        }
        authorization_raw = json.dumps(self.authorization).encode()
        self.expected_authorization_sha256 = hashlib.sha256(authorization_raw).hexdigest()
        batch_meta_raw = json.dumps({
            "authorization_sha256": hashlib.sha256(authorization_raw).hexdigest(),
            "batch_id": "batch",
            "environment_fingerprint_sha256": self.authorization["environment_fingerprint_sha256"],
            "git_commit": self.authorization["git_commit"],
            "manifest_sha256": self.authorization["manifest_sha256"],
        }).encode()
        self.files = {
            self.remote + "/authorization.json": authorization_raw,
            self.remote + "/environment_fingerprint.json": environment_raw,
            self.remote + "/batch_meta.json": batch_meta_raw,
            self.remote + "/selected-manifest.csv": manifest_raw,
        }
        self.receipt = {"status": "completed_unreviewed", "attempt_id": self.attempt,
                        "logical_run_id": self.attempt.split("__attempt-")[0], "attempt": 1,
                        "batch_id": "batch", "authorization_commit": "b" * 40,
                        "environment_fingerprint_sha256": self.authorization["environment_fingerprint_sha256"],
                        "execution_track": "nonconfirmatory_remote_gpu_supplement",
                        "protocol_version": "phase1-v1.1-2026-09-19", "stage": "B_screen",
                        "sha256": {}}
        for name in receiver.ARTIFACTS:
            payload = (name + " frozen bytes").encode()
            self.files[self.remote + "/" + self.attempt + "/" + name] = payload
            self.receipt["sha256"][name] = hashlib.sha256(payload).hexdigest()
        self.rewrite()
        self.sftp = MockSFTP(self.files)
        self.instance = receiver.Receiver(self.root, self.remote,
                                         expected_authorization_sha256=self.expected_authorization_sha256,
                                         progress=lambda value: None)

    def rewrite(self):
        self.files[self.remote + "/" + self.attempt + "/receipt.json"] = json.dumps(self.receipt).encode()

    def test_publish_six_original_files_and_cache_unchanged_receipt(self):
        report = self.instance.receive_pass(self.sftp)
        self.assertEqual(report["published"], [self.attempt])
        published = self.root / "attempts" / self.attempt
        self.assertEqual({p.name for p in published.iterdir()}, set(receiver.ARTIFACTS) | {"receipt.json"})
        self.assertFalse(report["pooling_authorized"])
        self.assertTrue(report["manifest_hash_verified"])
        self.assertTrue(all((Path(report["metadata_snapshot"]) / n).exists() for n in receiver.REQUIRED_METADATA))
        self.sftp.reads.clear()
        report = self.instance.receive_pass(self.sftp)
        self.assertEqual(report["skipped"], [self.attempt])
        self.assertFalse(any(path.endswith("checkpoint.pth") for path in self.sftp.reads))

    def test_required_and_optional_metadata_are_disjoint(self):
        self.assertNotIn("batch_meta.json", receiver.OPTIONAL_METADATA)
        self.assertTrue(set(receiver.REQUIRED_METADATA).isdisjoint(receiver.OPTIONAL_METADATA))

    def test_bounded_prefetch_preserves_hash_validation(self):
        calls = []
        class PrefetchFile(io.BytesIO):
            def prefetch(self, **kwargs):
                calls.append(kwargs)
        path = self.remote + "/" + self.attempt + "/checkpoint.pth"
        with patch.object(self.sftp, "open", return_value=PrefetchFile(self.files[path])):
            target = self.root / "prefetched.pth"
            self.instance.download(self.sftp, path, target, self.receipt["sha256"]["checkpoint.pth"])
        self.assertEqual(calls, [{"file_size": len(self.files[path]), "max_concurrent_requests": 32}])
        self.assertEqual(target.read_bytes(), self.files[path])

    def test_hash_mismatch_quarantines_and_never_publishes(self):
        self.files[self.remote + "/" + self.attempt + "/checkpoint.pth"] = b"corrupt"
        report = self.instance.receive_pass(self.sftp)
        self.assertEqual(report["status"], "requires_resolution")
        self.assertFalse((self.root / "attempts" / self.attempt).exists())
        self.assertTrue(list((self.root / "quarantine").iterdir()))

    def test_receipt_change_quarantines_complete_download(self):
        self.sftp.mutate_on_artifact = True
        report = self.instance.receive_pass(self.sftp)
        self.assertIn("receipt changed", report["issues"][0]["error"])
        self.assertFalse((self.root / "attempts" / self.attempt).exists())

    def test_network_retry_keeps_partial_and_uses_new_directory(self):
        self.sftp.fail_once = True
        with self.assertRaises(EOFError):
            self.instance.receive_pass(self.sftp)
        partial = list((self.root / "incoming").iterdir())
        self.assertEqual(len(partial), 1)
        reports = list((self.root / "reports").glob("*.json"))
        self.assertEqual(len(reports), 1)
        report = json.loads(reports[0].read_bytes())
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["issues"][0]["incoming_partial"], str(partial[0]))
        self.assertIn("EOFError", report["issues"][0]["error"])
        self.assertEqual(report["issues"][0]["state"], "incomplete transfer retained; not published")
        self.assertEqual(self.instance.receive_pass(self.sftp)["published"], [self.attempt])
        self.assertTrue(partial[0].exists())

    def test_publication_failure_preserves_verified_package_and_labels_it(self):
        original_rename = Path.rename

        def fail_incoming_publish(source, target):
            if source.parent == self.root / "incoming" and Path(target).parent == self.root / "attempts":
                Path(target).mkdir()
                raise FileExistsError("simulated destination race")
            return original_rename(source, target)

        with patch.object(Path, "rename", new=fail_incoming_publish):
            with self.assertRaisesRegex(OSError, "destination race"):
                self.instance.receive_pass(self.sftp)
        appeared = self.root / "attempts" / self.attempt
        self.assertTrue(appeared.is_dir())
        self.assertFalse((appeared / "receipt.json").exists())
        incoming = list((self.root / "incoming").iterdir())
        self.assertEqual(len(incoming), 1)
        self.assertEqual({path.name for path in incoming[0].iterdir()},
                         set(receiver.ARTIFACTS) | {"receipt.json"})
        reports = list((self.root / "reports").glob("*.json"))
        report = json.loads(reports[0].read_bytes())
        self.assertEqual(report["issues"][0]["incoming_verified_package"], str(incoming[0]))
        self.assertEqual(report["issues"][0]["state"],
                         "complete package verified; publication failed; retained")

    def test_existing_attempt_without_receipt_fails_closed_with_integrity_error(self):
        published = self.root / "attempts" / self.attempt
        published.mkdir()
        with self.assertRaisesRegex(receiver.IntegrityError, "published receipt is missing"):
            self.instance.receive_pass(self.sftp)
        self.assertFalse((published / "receipt.json").exists())
        self.assertEqual(list((self.root / "incoming").iterdir()), [])

    def test_truthy_scope_claim_prevents_artifact_reads(self):
        authorization = dict(self.authorization, pooling_authorized="false")
        authorization_raw = json.dumps(authorization).encode()
        self.files[self.remote + "/authorization.json"] = authorization_raw
        batch_meta = json.loads(self.files[self.remote + "/batch_meta.json"])
        batch_meta["authorization_sha256"] = hashlib.sha256(authorization_raw).hexdigest()
        self.files[self.remote + "/batch_meta.json"] = json.dumps(batch_meta).encode()
        self.instance.expected_authorization_sha256 = hashlib.sha256(authorization_raw).hexdigest()
        with self.assertRaisesRegex(receiver.IntegrityError, "descriptive-only scope"):
            self.instance.receive_pass(self.sftp)
        self.assertFalse(any(path.endswith("checkpoint.pth") for path in self.sftp.reads))

    def test_invalid_stage_list_prevents_artifact_reads(self):
        authorization = dict(self.authorization, stages="B_screen")
        authorization_raw = json.dumps(authorization).encode()
        self.files[self.remote + "/authorization.json"] = authorization_raw
        batch_meta = json.loads(self.files[self.remote + "/batch_meta.json"])
        batch_meta["authorization_sha256"] = hashlib.sha256(authorization_raw).hexdigest()
        self.files[self.remote + "/batch_meta.json"] = json.dumps(batch_meta).encode()
        self.instance.expected_authorization_sha256 = hashlib.sha256(authorization_raw).hexdigest()
        with self.assertRaisesRegex(receiver.IntegrityError, "stage list"):
            self.instance.receive_pass(self.sftp)
        self.assertFalse(any(path.endswith("checkpoint.pth") for path in self.sftp.reads))

    def test_missing_protocol_version_is_an_integrity_error(self):
        authorization = dict(self.authorization)
        del authorization["protocol_version"]
        authorization_raw = json.dumps(authorization).encode()
        self.files[self.remote + "/authorization.json"] = authorization_raw
        batch_meta = json.loads(self.files[self.remote + "/batch_meta.json"])
        batch_meta["authorization_sha256"] = hashlib.sha256(authorization_raw).hexdigest()
        self.files[self.remote + "/batch_meta.json"] = json.dumps(batch_meta).encode()
        self.instance.expected_authorization_sha256 = hashlib.sha256(authorization_raw).hexdigest()
        with self.assertRaisesRegex(receiver.IntegrityError, "protocol version"):
            self.instance.receive_pass(self.sftp)
        self.assertFalse(any(path.endswith("checkpoint.pth") for path in self.sftp.reads))

    def test_restart_verifies_full_checkpoint_and_never_overwrites(self):
        self.instance.receive_pass(self.sftp)
        checkpoint = self.root / "attempts" / self.attempt / "checkpoint.pth"
        checkpoint.write_bytes(b"local corruption")
        restarted = receiver.Receiver(self.root, self.remote,
                                      expected_authorization_sha256=self.expected_authorization_sha256,
                                      progress=lambda value: None)
        with self.assertRaises(receiver.IntegrityError):
            restarted.receive_pass(self.sftp)
        self.assertEqual(checkpoint.read_bytes(), b"local corruption")

    def test_running_receipt_does_not_read_artifacts(self):
        self.receipt["status"] = "running"
        self.rewrite()
        self.assertEqual(self.instance.receive_pass(self.sftp)["published"], [])
        self.assertFalse(any(path.endswith("checkpoint.pth") for path in self.sftp.reads))

    def test_running_receipt_without_batch_scope_is_skipped_without_issue(self):
        self.receipt = {"status": "running", "attempt_id": self.attempt}
        self.rewrite()
        report = self.instance.receive_pass(self.sftp)
        self.assertEqual(report["published"], [])
        self.assertEqual(report["issues"], [])
        self.assertFalse(any(path.endswith("checkpoint.pth") for path in self.sftp.reads))

    def test_reject_existing_unowned_roots_and_traversal(self):
        with self.assertRaises(FileExistsError):
            receiver.Receiver(Path(self.temp.name), self.remote,
                              expected_authorization_sha256=self.expected_authorization_sha256)
        with self.assertRaises(ValueError):
            receiver.Receiver(self.root / "bad", "/results/../secret",
                              expected_authorization_sha256=self.expected_authorization_sha256)
        with self.assertRaises(ValueError):
            receiver.Receiver(receiver.ROOT / "dataset/intake", self.remote,
                              expected_authorization_sha256=self.expected_authorization_sha256)
        for name in ("../checkpoint.pth", "/absolute", "bad\\name"):
            with self.assertRaises(receiver.IntegrityError):
                receiver.safe_name(name)

    def test_legacy_receiver_v1_root_is_not_reused(self):
        old_root = Path(self.temp.name) / "legacy-intake"
        old_root.mkdir()
        (old_root / receiver.MARKER).write_text(json.dumps({
            "receiver_version": "phase1-sftp-receiver/v1", "remote_root": self.remote,
        }), encoding="utf-8")
        with self.assertRaises(FileExistsError):
            receiver.Receiver(old_root, self.remote,
                              expected_authorization_sha256=self.expected_authorization_sha256)

    def test_missing_authorization_prevents_publish(self):
        del self.files[self.remote + "/authorization.json"]
        with self.assertRaises(receiver.IntegrityError):
            self.instance.receive_pass(self.sftp)
        self.assertFalse(list((self.root / "attempts").iterdir()))

    def test_wrong_batch_authorization_prevents_artifact_reads(self):
        authorization = dict(self.authorization, batch_id="other-batch")
        authorization_raw = json.dumps(authorization).encode()
        self.files[self.remote + "/authorization.json"] = authorization_raw
        batch_meta = json.loads(self.files[self.remote + "/batch_meta.json"])
        batch_meta["authorization_sha256"] = hashlib.sha256(authorization_raw).hexdigest()
        batch_meta["batch_id"] = "other-batch"
        self.files[self.remote + "/batch_meta.json"] = json.dumps(batch_meta).encode()
        with self.assertRaises(receiver.IntegrityError):
            self.instance.receive_pass(self.sftp)
        self.assertFalse(any(path.endswith("checkpoint.pth") for path in self.sftp.reads))
        self.assertFalse(list((self.root / "attempts").iterdir()))

    def test_authorization_hash_mismatch_prevents_artifact_reads(self):
        authorization = dict(self.authorization, approved_by="different source")
        authorization_raw = json.dumps(authorization).encode()
        self.files[self.remote + "/authorization.json"] = authorization_raw
        batch_meta = json.loads(self.files[self.remote + "/batch_meta.json"])
        batch_meta["authorization_sha256"] = hashlib.sha256(authorization_raw).hexdigest()
        self.files[self.remote + "/batch_meta.json"] = json.dumps(batch_meta).encode()
        with self.assertRaises(receiver.IntegrityError):
            self.instance.receive_pass(self.sftp)
        self.assertFalse(any(path.endswith("checkpoint.pth") for path in self.sftp.reads))
        self.assertFalse(list((self.root / "attempts").iterdir()))

    def test_receipt_from_another_batch_is_rejected(self):
        self.receipt["batch_id"] = "other-batch"
        self.rewrite()
        report = self.instance.receive_pass(self.sftp)
        self.assertEqual(report["status"], "requires_resolution")
        self.assertFalse(any(path.endswith("checkpoint.pth") for path in self.sftp.reads))
        self.assertFalse(list((self.root / "attempts").iterdir()))

    def test_missing_authorized_manifest_bytes_blocks_scientific_intake(self):
        del self.files[self.remote + "/selected-manifest.csv"]
        report = self.instance.receive_pass(self.sftp)
        scientific_gate = next(item for item in report["gate_table"]
                               if item["check"] == "scientific use")
        self.assertFalse(report["manifest_hash_verified"])
        self.assertIn("no matching manifest bytes", scientific_gate["evidence"])
        self.assertIn("reconcile the authorized manifest", scientific_gate["next_permitted_action"])

    def test_empty_precreated_dedicated_root_is_owned_without_overwrite(self):
        fresh = Path(self.temp.name) / "precreated-intake"
        fresh.mkdir()
        instance = receiver.Receiver(fresh, self.remote,
                                     expected_authorization_sha256=self.expected_authorization_sha256,
                                     progress=lambda value: None)
        self.assertTrue((fresh / receiver.MARKER).is_file())
        self.assertEqual(instance.receive_pass(self.sftp)["published"], [self.attempt])

    def test_deadline_retains_partial_without_publishing(self):
        self.instance.deadline = 0
        with self.assertRaises(TimeoutError):
            self.instance.receive_pass(self.sftp)
        self.assertFalse(list((self.root / "attempts").iterdir()))
        partial = list((self.root / "incoming").iterdir())
        self.assertEqual(len(partial), 1)
        reports = list((self.root / "reports").glob("*.json"))
        self.assertEqual(len(reports), 1)
        report = json.loads(reports[0].read_bytes())
        self.assertEqual(report["issues"][0]["incoming_partial"], str(partial[0]))
        self.assertIn("TimeoutError", report["issues"][0]["error"])
        self.assertEqual(report["issues"][0]["state"], "incomplete transfer retained; not published")

    def test_remote_health_success_is_snapshotted(self):
        payload = json.dumps({"observedAt": "2026-10-30T00:00:00+00:00",
                              "probeSucceeded": True, "gpuProbeSucceeded": True}).encode()
        client = MockHealthClient(payload)
        report = self.instance.receive_pass(self.sftp, receiver.read_remote_health(client))
        recorded = json.loads((Path(report["metadata_snapshot"]) / "remote_health.json").read_text())
        self.assertEqual(recorded, json.loads(payload))
        self.assertEqual(report["published"], [self.attempt])
        self.assertEqual(client.commands[0][1], 20)
        self.assertIn("nvidia-smi", client.commands[0][0])

    def test_remote_health_failure_is_recorded_and_not_fatal(self):
        health = receiver.read_remote_health(MockHealthClient(error=OSError("probe unavailable")))
        self.assertFalse(health["probeSucceeded"])
        self.assertEqual(health["errorClass"], "OSError")
        report = self.instance.receive_pass(self.sftp, health)
        self.assertEqual(report["published"], [self.attempt])
        recorded = json.loads((Path(report["metadata_snapshot"]) / "remote_health.json").read_text())
        self.assertFalse(recorded["probeSucceeded"])

    def test_remote_health_invalid_json_is_recorded_and_not_fatal(self):
        health = receiver.read_remote_health(MockHealthClient(b"not-json"))
        self.assertFalse(health["probeSucceeded"])
        self.assertEqual(health["errorClass"], "JSONDecodeError")
        self.assertEqual(self.instance.receive_pass(self.sftp, health)["published"], [self.attempt])


class MockHealthClient:
    def __init__(self, payload=None, error=None):
        self.payload = payload
        self.error = error
        self.commands = []

    def exec_command(self, command, timeout=None):
        self.commands.append((command, timeout))
        if self.error is not None:
            raise self.error
        return None, io.BytesIO(self.payload), io.BytesIO(b"")


if __name__ == "__main__":
    unittest.main()
