import json
import unittest

from reproduction.batches.run_phase1_stages import (
    CONFIG,
    MANIFESTS,
    build_command,
    rows,
    validate_preflight,
)


class Phase1StageRunnerTest(unittest.TestCase):
    def test_frozen_manifests_and_preflight_keys(self):
        expected = {"B_screen": 300, "C_confirmation": 360, "D_temporal_robustness": 144}
        for stage, count in expected.items():
            manifest = rows(MANIFESTS[stage])
            self.assertEqual(len(manifest), count)
            _, _, problems = validate_preflight(manifest)
            self.assertEqual(problems, [])

    def test_date_stage_command_preserves_explicit_boundaries(self):
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        row = next(r for r in rows(MANIFESTS["D_temporal_robustness"]) if r["asset"] == "AAPL")
        registry = {r["asset"]: r for r in rows(CONFIG.parents[1] / "results/dataset_registry.csv")}
        command = build_command(row, config["common"], registry[row["asset"]], 1, "cuda")
        for value in ("--split_mode", "dates", "--train_end", row["train_end"],
                      "--val_end", row["val_end"], "--test_end", row["test_end"], "--deterministic"):
            self.assertIn(value, command)
        self.assertIn("--gpu_type", command)


if __name__ == "__main__":
    unittest.main()
