"""No real arrays, downloads, fitting or scoring: bootstrap and boundary tests."""
import json
from pathlib import Path
import unittest
import uuid
from reproduction.analysis import compression_replay as replay
from reproduction.analysis.check_artifact_boundary import violations, POLICY

class ReplayBootstrap(unittest.TestCase):
    def test_relative_paths_and_historical_rebinding(self):
        root = replay.ROOT
        self.assertEqual(replay.resolve_relative(root, 'data/roles/train.npz'), root/'data/roles/train.npz')
        for path in ('../outside', '/outside', 'C:\\outside', 'C:relative', 'data\\..\\outside'):
            with self.assertRaises(ValueError): replay.resolve_relative(root, path)
        old = 'C:\\Users\\someone\\repo\\data\\shrink-cdd-20261013-v1\\packages_v1_1\\ETHUSD_f100\\train.npz'
        self.assertEqual(replay.historical_private_relative(old),
                         'data/shrink-cdd-20261013-v1/packages_v1_1/ETHUSD_f100/train.npz')
        with self.assertRaises(ValueError): replay.historical_private_relative('C:/other/data/test/test.npz')

    def test_invalid_attempt_names_create_nothing(self):
        for name in ('../old', 'new/old', 'C:foo', '', '.hidden', 'a'*65):
            with self.assertRaises(ValueError): replay.generate(name)

    def test_generation_binds_sources_but_does_not_authorize_fitting(self):
        # Retain this tiny private attempt as synthetic validation provenance.
        attempt = replay.generate('synthetic_bootstrap_'+uuid.uuid4().hex[:12])
        self.assertTrue(attempt.is_relative_to(replay.ROOT/'data/compression-replay-attempts'))
        protocol = replay.load(attempt/'PROTOCOL_V1.json')
        self.assertEqual(protocol['repository'], str(replay.ROOT))
        self.assertIn('separate execution authorization', protocol['status'])
        self.assertEqual(replay.load(attempt/'EXECUTION_AUTHORIZATION_TEMPLATE.json')['decision'], 'NOT_APPROVED')
        engine = replay.configure(attempt)
        engine.verify_sources()
        self.assertFalse(engine.PREP.exists())
        with self.assertRaises(FileNotFoundError): engine.release()
        self.assertFalse(engine.RELEASE.exists())
        self.assertFalse(engine.PRIVATE.exists())

    def test_source_drift_is_rejected_before_private_arrays_are_read(self):
        attempt = replay.generate('synthetic_drift_'+uuid.uuid4().hex[:12])
        file = attempt/'PROTOCOL_V1.json'
        protocol = replay.load(file)
        protocol['replay']['code_sha256']['reproduction/preprocessing/fixed_ohlc.py'] = '0'*64
        file.write_text(json.dumps(protocol), encoding='utf-8')
        with self.assertRaises(ValueError): replay.configure(attempt)

class Boundary(unittest.TestCase):
    def test_new_private_paths_denied_and_text_records_allowed(self):
        policy = json.loads(POLICY.read_text(encoding='utf-8'))
        paths = ['model.PT', 'data/cdd/raw.csv', 'private/train.npz', 'x/validation.predictions.csv',
                 'docs/report.md', 'models/derefusion/bundle_v3_pin/DeReFusion.py',
                 'research_work/project_management_2026_10_10/compression_pilot_2026_10_13/RESULTS_V1.json']
        self.assertEqual(set(violations(paths, policy)), set(paths[:4]))

if __name__ == '__main__': unittest.main()
