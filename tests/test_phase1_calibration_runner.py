import unittest

from reproduction.batches.run_phase1_calibration import (
    CONFIG_PATH,
    MANIFEST_PATH,
    REGISTRY_PATH,
    build_command,
    load_csv,
    run_id,
)
import json


class Phase1CalibrationRunnerTest(unittest.TestCase):
    def test_frozen_grid_has_unique_complete_commands(self):
        config = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
        rows = load_csv(MANIFEST_PATH)
        registry = {row['asset']: row for row in load_csv(REGISTRY_PATH)}
        self.assertEqual(len(rows), 15)
        identifiers = set()
        for index, row in enumerate(rows, start=1):
            identifier = run_id(index, row)
            self.assertNotIn(identifier, identifiers)
            identifiers.add(identifier)
            command = build_command(row, registry, config)
            joined = ' '.join(command)
            self.assertIn('--deterministic', command)
            self.assertIn('--no_use_gpu', command)
            self.assertIn('--result_log reproduction/logs/phase1/calibration_result_log.txt', joined)
            self.assertIn(f"--model {row['model']}", joined)
            self.assertIn(f"--rand_seed {row['seed']}", joined)


if __name__ == '__main__':
    unittest.main()
