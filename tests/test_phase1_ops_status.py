"""Local receipt fixtures only: no training, device probes, or remote access."""
import http.client
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from http.server import ThreadingHTTPServer


BACKEND = Path(__file__).resolve().parents[1] / "reproduction/analysis/serve_phase1_ops_status.py"
SPEC = importlib.util.spec_from_file_location("phase1_ops_status_test_backend", BACKEND)
ops = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ops
SPEC.loader.exec_module(ops)


class OpsStatusTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.phase = self.root / "reproduction/results/phase1"
        self.local = self.phase / "local-5060-stage-c-v1"
        self.remote = self.phase / "rtx8000-intake-20260929-v2"
        self.now = datetime(2026, 9, 29, 9, 0, tzinfo=timezone.utc)
        self.run = "C_confirmation_AAPL_DeReFusion_h1_s2022"

    def write_json(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def progress(self, root=None, age=30, **extra):
        data = {"status": "running", "current_run": self.run,
                "total_selected": 360, "newly_completed": 99,
                "updated_at_utc": (self.now - timedelta(seconds=age)).isoformat()}
        data.update(extra)
        return self.write_json((root or self.local) / "batch_progress.json", data)

    def receipt(self, root, logical, attempt=1, status="completed_unreviewed"):
        name = f"{logical}__attempt-{attempt:02d}"
        return self.write_json(root / name / "receipt.json", {
            "status": status, "logical_run_id": logical, "attempt_id": name,
            "created_at_utc": (self.now - timedelta(seconds=30)).isoformat(),
        })

    def acknowledgement(self, consumer, name, hashes, status="completed_descriptive_only", **extra):
        data = {"created_at_utc": (self.now - timedelta(seconds=30)).isoformat(),
                "intake_status": status, "receipt_hashes": hashes,
                "summary": {"eligible_packages": len(hashes)},
                "training_performed": False, "gpu_used": False}
        data.update(extra)
        return self.write_json(self.phase / consumer / f"pass-{name}" / "acknowledgement.json", data)

    def snapshot(self, processes=None, gpu=None):
        return ops.build_snapshot(self.root, now=self.now,
                                  gpu_probe=lambda: gpu or {"available": False},
                                  process_probe=lambda: processes or {"available": False})

    @staticmethod
    def tasks(snapshot):
        return {task["id"]: task for task in snapshot["tasks"]}

    def test_empty_repository_has_stable_ids_and_unavailable_observations(self):
        first = self.snapshot()
        self.assertEqual(first["schemaVersion"], "phase1-ops/v1")
        self.assertTrue(first["readOnly"])
        expected = {"stage-c", "remote-stage-b", "transfer", "intake-c", "intake-8000",
                    "p4-archive", "bridge-replay", "gpu-replay-queue"}
        self.assertEqual(set(self.tasks(first)), expected)
        self.progress()
        self.assertEqual(set(self.tasks(self.snapshot())), expected)
        gpu = next(item for item in first["hardware"] if item["id"] == "local-5060")
        self.assertIsNone(gpu["utilizationPercent"])
        self.assertEqual(self.tasks(first)["stage-c"]["freshness"], "unknown")

    def test_running_report_expires_at_freshness_boundary(self):
        for age, freshness, status in ((180, "fresh", "reported-running"), (181, "stale", "stale")):
            with self.subTest(age=age):
                self.progress(age=age)
                task = self.tasks(self.snapshot())["stage-c"]
                self.assertEqual((task["freshness"], task["status"]), (freshness, status))
                self.assertFalse(task["processVerified"])

    def test_verified_local_process_overrides_stale_progress(self):
        self.progress(age=600)
        task = self.tasks(self.snapshot(processes={"available": True, "stage-c": True}))["stage-c"]
        self.assertEqual(task["status"], "running")
        self.assertTrue(task["processVerified"])
        self.assertEqual(task["freshness"], "stale")

    def test_newest_remote_snapshot_uses_arrival_time_and_preserves_runner_staleness(self):
        older = self.remote / "snapshots/z-old"
        latest = self.remote / "snapshots/a-new"
        self.progress(older, age=10, current_run="B_screen_OLD", total_selected=10)
        self.progress(latest, age=600, current_run="B_screen_NEW", total_selected=55)
        for path, age in ((older, 60), (latest, 30)):
            stamp = (self.now - timedelta(seconds=age)).timestamp()
            os.utime(path, (stamp, stamp))
        tasks = self.tasks(self.snapshot())
        self.assertEqual(tasks["remote-stage-b"]["currentRun"], "B_screen_NEW")
        self.assertEqual(tasks["remote-stage-b"]["total"], 55)
        self.assertEqual(tasks["remote-stage-b"]["freshness"], "stale")
        self.assertEqual(tasks["remote-stage-b"]["status"], "stale")
        self.assertEqual(tasks["transfer"]["freshness"], "fresh")
        stamp = (self.now - timedelta(seconds=181)).timestamp()
        os.utime(latest, (stamp, stamp))
        os.utime(older, (stamp - 30, stamp - 30))
        self.assertEqual(self.tasks(self.snapshot())["transfer"]["freshness"], "stale")

    def test_fresh_remote_running_report_is_explicitly_unverified(self):
        snapshot = self.remote / "snapshots/current"
        self.progress(snapshot, age=30)
        stamp = (self.now - timedelta(seconds=30)).timestamp()
        os.utime(snapshot, (stamp, stamp))
        task = self.tasks(self.snapshot())["remote-stage-b"]
        self.assertEqual(task["status"], "reported-running")
        self.assertFalse(task["processVerified"])

    def test_fresh_remote_health_verifies_stale_runner_and_whitelists_gpu_numbers(self):
        directory = self.remote / "snapshots/current"
        self.progress(directory, age=600)
        health = {"observedAt": (self.now - timedelta(seconds=30)).isoformat(),
                  "runnerAlive": True, "trainingWorkerAlive": True, "gpuProbeSucceeded": True,
                  "utilizationPercent": "98", "memoryUsedMiB": 9000, "memoryTotalMiB": "48000",
                  "command": "OPS_TEST_PRIVATE_REMOTE_CREDENTIAL", "rawNvidiaOutput": "not public"}
        self.write_json(directory / "remote_health.json", health)
        snapshot = self.snapshot()
        task = self.tasks(snapshot)["remote-stage-b"]
        self.assertEqual((task["status"], task["freshness"]), ("running", "fresh"))
        self.assertTrue(task["processVerified"])
        gpu = next(item for item in snapshot["hardware"] if item["id"] == "remote-8000")
        self.assertEqual((gpu["utilizationPercent"], gpu["memoryUsedMiB"], gpu["memoryTotalMiB"]),
                         (98, 9000, 48000))
        self.assertNotIn(health["command"], json.dumps(snapshot))
        self.assertNotIn("rawNvidiaOutput", json.dumps(snapshot))
        health["utilizationPercent"] = "invalid telemetry"
        self.write_json(directory / "remote_health.json", health)
        gpu = next(item for item in self.snapshot()["hardware"] if item["id"] == "remote-8000")
        self.assertIsNone(gpu["utilizationPercent"])

    def test_expired_remote_health_loses_process_verification_and_gpu_telemetry(self):
        directory = self.remote / "snapshots/current"
        self.progress(directory, age=600)
        self.write_json(directory / "remote_health.json", {
            "observedAt": (self.now - timedelta(seconds=181)).isoformat(),
            "runnerAlive": True, "gpuProbeSucceeded": True,
            "utilizationPercent": 98, "memoryUsedMiB": 9000, "memoryTotalMiB": 48000,
        })
        snapshot = self.snapshot()
        task = self.tasks(snapshot)["remote-stage-b"]
        self.assertEqual((task["status"], task["freshness"]), ("stale", "stale"))
        self.assertFalse(task["processVerified"])
        gpu = next(item for item in snapshot["hardware"] if item["id"] == "remote-8000")
        for field in ("utilizationPercent", "memoryUsedMiB", "memoryTotalMiB"):
            self.assertIsNone(gpu[field])

    def test_failed_injected_probes_keep_receipt_observations_without_leaking_errors(self):
        self.progress()
        secret = "OPS_TEST_PRIVATE_PROBE_CREDENTIAL"

        def failed_probe():
            raise RuntimeError(secret)

        snapshot = ops.build_snapshot(self.root, now=self.now,
                                      gpu_probe=failed_probe, process_probe=failed_probe)
        task = self.tasks(snapshot)["stage-c"]
        self.assertEqual(task["status"], "reported-running")
        self.assertFalse(task["processVerified"])
        gpu = next(item for item in snapshot["hardware"] if item["id"] == "local-5060")
        self.assertIsNone(gpu["utilizationPercent"])
        self.assertNotIn(secret, json.dumps(snapshot))

    def test_completed_counts_deduplicate_logical_receipts_and_ignore_runner_counter(self):
        self.progress()
        for root in (self.local, self.remote / "attempts"):
            self.receipt(root, self.run)
            self.receipt(root, self.run, attempt=2)
            self.receipt(root, "C_confirmation_SECOND")
            self.receipt(root, "C_confirmation_RUNNING", status="running")
        tasks = self.tasks(self.snapshot())
        self.assertEqual(tasks["stage-c"]["completed"], 2)
        self.assertEqual(tasks["remote-stage-b"]["completed"], 2)
        self.assertEqual(tasks["transfer"]["completed"], 2)
        self.assertEqual(tasks["gpu-replay-queue"]["queued"], 2)

    def forward_report(self, directory, results):
        return self.write_json(self.phase / directory / "report.json", {"results": results})

    def test_gpu_replay_queue_counts_only_written_rtx8000_forwards(self):
        self.progress()
        self.receipt(self.remote / "attempts", self.run)
        self.receipt(self.remote / "attempts", "B_screen_SECOND")
        # The P4 bridge report carries its own reference tracks; it must not
        # clear a queue that is waiting on RTX 8000 forwards.
        self.forward_report("checkpoint-forward-5060-v1", [
            {"logical_run_id": self.run, "reference_track": "p4"},
            {"logical_run_id": "B_screen_SECOND", "reference_track": "local"},
        ])
        task = self.tasks(self.snapshot())["gpu-replay-queue"]
        self.assertEqual((task["completed"], task["queued"], task["total"]), (0, 2, 2))
        # A written forward clears exactly the received package it names, in its
        # own report directory; a forward for a package never received adds nothing.
        self.forward_report("checkpoint-forward-rtx8000-on-5060-v1", [
            {"logical_run_id": self.run, "reference_track": "rtx8000"},
            {"logical_run_id": "B_screen_NEVER_RECEIVED", "reference_track": "rtx8000"},
        ])
        task = self.tasks(self.snapshot())["gpu-replay-queue"]
        self.assertEqual((task["completed"], task["queued"], task["total"]), (1, 1, 2))
        self.assertEqual(task["status"], "waiting-resource")
        # Repeated forwards of the same package still count once.
        self.forward_report("checkpoint-forward-rtx8000-on-5060-v1", [
            {"logical_run_id": self.run, "reference_track": "rtx8000"},
            {"logical_run_id": self.run, "reference_track": "rtx8000"},
            {"logical_run_id": "B_screen_SECOND", "reference_track": "rtx8000"},
        ])
        task = self.tasks(self.snapshot())["gpu-replay-queue"]
        self.assertEqual((task["completed"], task["queued"], task["total"]), (2, 0, 2))
        self.assertEqual(task["status"], "completed")

    def test_cpu_acknowledgements_deduplicate_successes_and_report_failed_pass(self):
        hashes = {self.run + "__attempt-01": "a" * 64, "C_confirmation_SECOND__attempt-01": "b" * 64}
        for consumer, identifier in (("consumer-stagec-20260929-v1", "intake-c"),
                                     ("consumer-rtx8000-20260929-v1", "intake-8000")):
            self.acknowledgement(consumer, "01", hashes)
            self.acknowledgement(consumer, "02", {self.run + "__attempt-02": "c" * 64})
            self.acknowledgement(consumer, "03", {"FAILED__attempt-01": "d" * 64}, status="failed")
            task = self.tasks(self.snapshot())[identifier]
            self.assertEqual(task["completed"], 2)
            self.assertEqual(task["status"], "failed")
        self.write_json(self.phase / "intake-p4-20260929-v1/report.json", {
            "summary": {"eligible_packages": 7, "attempts_seen": 9},
            "created_at_utc": self.now.isoformat(),
        })
        p4 = self.tasks(self.snapshot())["p4-archive"]
        self.assertEqual((p4["completed"], p4["total"]), (7, 9))

    def test_current_step_uses_recent_log_category_without_returning_log_or_credentials(self):
        secret = "OPS_TEST_PRIVATE_TOKEN_DO_NOT_RETURN"
        self.progress(ssh_password=secret, command="ssh user:password@private-host")
        log = self.local / (self.run + "__attempt-01") / "run.log"
        log.parent.mkdir(parents=True)
        for line, expected in (("Epoch: 4, Steps: 52 | Train Loss: 0.04", "training"),
                               ("test shape: (20, 1, 1)", "evaluation"),
                               ("saved: figures/forecast.png", "plotting")):
            with self.subTest(expected=expected):
                log.write_text(f"ssh_password={secret}\n{line}\n", encoding="utf-8")
                snapshot = self.snapshot()
                self.assertEqual(self.tasks(snapshot)["stage-c"]["currentStep"], expected)
                serialized = json.dumps(snapshot)
                self.assertNotIn(secret, serialized)
                self.assertNotIn("private-host", serialized)
                self.assertNotIn(str(self.root), serialized)

    def start_server(self, builder=None):
        cache = ops.StatusCache(self.root, ttl=3600, builder=builder or (lambda _root: self.snapshot()))
        server = ThreadingHTTPServer(("127.0.0.1", 0), ops.make_handler(cache))
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        thread.start()

        def stop():
            server.shutdown()
            server.server_close()
            thread.join(timeout=1)

        self.addCleanup(stop)
        return server.server_address[1]

    def request(self, port, method="GET", path="/status", origin=None):
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
        try:
            connection.request(method, path, headers={"Origin": origin} if origin else {})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), json.loads(response.read())
        finally:
            connection.close()

    def test_health_is_available_without_running_observation_probes(self):
        def unexpected(_root):
            self.fail("health endpoint must not invoke status observations")

        code, headers, body = self.request(self.start_server(unexpected), path="/health")
        self.assertEqual(code, 200)
        self.assertEqual(body, {"status": "ok", "readOnly": True, "schemaVersion": "phase1-ops/v1"})
        self.assertEqual(headers["Cache-Control"], "no-store")

    def test_status_cors_only_allows_local_dashboard_origins(self):
        port = self.start_server()
        for origin in ("http://localhost:8964", "http://127.0.0.1:8964"):
            with self.subTest(origin=origin):
                code, headers, body = self.request(port, origin=origin)
                self.assertEqual(code, 200)
                self.assertEqual(headers["Access-Control-Allow-Origin"], origin)
                self.assertTrue(body["readOnly"])
        code, headers, _ = self.request(port, origin="https://untrusted.example")
        self.assertEqual(code, 403)
        self.assertNotIn("Access-Control-Allow-Origin", headers)

    def test_status_service_rejects_mutations_and_unknown_paths(self):
        port = self.start_server()
        for method in ("POST", "PUT", "PATCH", "DELETE"):
            with self.subTest(method=method):
                code, _, body = self.request(port, method=method)
                self.assertEqual(code, 405)
                self.assertTrue(body["readOnly"])
        self.assertEqual(self.request(port, path="/not-a-status-route")[0], 404)


if __name__ == "__main__":
    unittest.main()
