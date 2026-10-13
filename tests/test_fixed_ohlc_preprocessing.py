"""Synthetic invariants for the extracted transform and exact source loader."""
import hashlib
import importlib.util
from pathlib import Path
import shutil
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
import numpy as np
import torch
from reproduction.preprocessing.fixed_ohlc import AggregationPlan, aggregate_ohlc, derived_cache_key
from models.derefusion.bundle_v3_pin.loader import HERE as ARCHIVE, load_model_class, verify_archive

ROOT = Path(__file__).resolve().parents[1]
PLAN = AggregationPlan(96, 4, 16, 32)

def load_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class FixedOHLC(unittest.TestCase):
    def test_exact_frozen_transform_and_no_input_mutation(self):
        old = load_file('frozen_pilot_transform_reference', ROOT/'research_work/project_management_2026_10_10/compression_pilot_2026_10_13/run_pilot_v1.py')
        rng = np.random.default_rng(413)
        for dtype in (np.float32, np.float64, np.int32, np.uint16):
            for n in (0, 1, 7, 67):
                x = (rng.random((n, 96, 4))*100).astype(dtype)
                saved = x.copy()
                actual = aggregate_ohlc(x, PLAN)
                np.testing.assert_array_equal(actual, old.aggregate(x))
                np.testing.assert_array_equal(x, saved)
                self.assertEqual(actual.dtype, x.dtype)
                self.assertFalse(np.shares_memory(x, actual))

    def test_block_boundaries_recent_context_and_last_close(self):
        x = np.arange(96*4).reshape(1, 96, 4)
        y = aggregate_ohlc(x, PLAN)
        for j in range(16):
            np.testing.assert_array_equal(y[0, j], [x[0, j*4, 0], x[0, j*4+3, 1],
                                                  x[0, j*4, 2], x[0, j*4+3, 3]])
        np.testing.assert_array_equal(y[:, 16:], x[:, 64:])
        np.testing.assert_array_equal(y[:, -1], x[:, -1])
        self.assertEqual(PLAN.position_spans_days(), [4]*16+[1]*32)
        self.assertEqual(sum(PLAN.position_spans_days()), 96)

    def test_positive_affine_commutation(self):
        close = 100+np.arange(96, dtype=np.float64)
        x = np.stack((close-.2, close+.7, close-.8, close), axis=1)[None]
        mean, std = np.array([30, 40, 50, 60]), np.array([2, 3, 4, 5])
        np.testing.assert_allclose(aggregate_ohlc((x-mean)/std, PLAN),
                                   (aggregate_ohlc(x, PLAN)-mean)/std, rtol=0, atol=2e-14)

    def test_invalid_plans_and_input_fail_closed(self):
        for args in ((96, 4, 15, 32), (96, 0, 16, 32), (96, 4, 16, -1),
                     (True, 4, 16, 32), (96.0, 4, 16, 32)):
            with self.assertRaises(ValueError): AggregationPlan(*args)
        with self.assertRaises(ValueError): AggregationPlan(96, 4, 16, 32, channel_order=list(PLAN.channel_order))
        for x in (np.ones((96, 4)), np.ones((1, 95, 4)), np.ones((1, 96, 3)),
                  np.full((1, 96, 4), np.nan), np.full((1, 96, 4), np.inf),
                  np.ones((1, 96, 4), dtype=complex), np.ones((1, 96, 4), dtype=bool),
                  np.full((1, 96, 4), '1'), [[[1]]]):
            with self.assertRaises(ValueError): aggregate_ohlc(x, PLAN)

    def test_configuration_and_cache_identities(self):
        self.assertEqual(PLAN.canonical_json(), AggregationPlan(96, 4, 16, 32).canonical_json())
        self.assertEqual(PLAN.config_sha256(), AggregationPlan(96, 4, 16, 32).config_sha256())
        self.assertNotEqual(PLAN.config_sha256(), AggregationPlan(96, 2, 32, 32).config_sha256())
        args = dict(source_package_sha256='a'*64, source_manifest_sha256='b'*64,
                    scaler_sha256='c'*64, module_sha256='d'*64, numpy_version='2.1.2', plan=PLAN)
        identity = derived_cache_key(**args)
        for key in ('source_package_sha256', 'source_manifest_sha256', 'scaler_sha256', 'module_sha256'):
            self.assertNotEqual(identity, derived_cache_key(**dict(args, **{key: 'e'*64})))
        self.assertNotEqual(identity, derived_cache_key(**dict(args, numpy_version='different')))
        with self.assertRaises(ValueError): derived_cache_key(**dict(args, module_sha256='invalid'))

class PinnedSource(unittest.TestCase):
    def test_archive_matches_top_level_initialization_and_output(self):
        torch.set_num_threads(2)
        torch.use_deterministic_algorithms(True)
        top = load_file('top_derefusion_reference', ROOT/'models/derefusion/DeReFusion.py')
        pinned = load_model_class()
        for length, expected_count in ((96, 21743), (48, 21599)):
            cfg = SimpleNamespace(seq_len=length, pred_len=1, enc_in=4, d_model=32,
                                  moving_avg=25, n_heads=4, e_layers=1, d_ff=128, dropout=.3)
            torch.manual_seed(17); a = top.Model(cfg).eval()
            torch.manual_seed(17); b = pinned(cfg).eval()
            self.assertEqual(sum(v.numel() for v in b.parameters()), expected_count)
            self.assertEqual(list(a.state_dict()), list(b.state_dict()))
            h = hashlib.sha256()
            for k, v in sorted(b.state_dict().items()):
                self.assertTrue(torch.equal(v, a.state_dict()[k]), k)
                h.update(k.encode()); h.update(v.numpy().tobytes())
            if length == 96:
                self.assertEqual(h.hexdigest(), '564e61a1932803617c37856f673bffb58c5f22fede24b3aeebdb685b6e1f560d')
            x = torch.arange(2*length*4, dtype=torch.float32).reshape(2, length, 4)/100
            with torch.no_grad():
                self.assertTrue(torch.equal(a(x, None, None, None), b(x, None, None, None)))

    def test_loader_isolated_from_other_layers_modules(self):
        before_path = list(sys.path)
        previous = {k: sys.modules.get(k) for k in ('layers.RevIN', 'layers.derefusion_components')}
        try:
            for key in previous: sys.modules[key] = ModuleType(key)
            c = load_model_class()
            cfg = SimpleNamespace(seq_len=48, pred_len=1, enc_in=4, d_model=32,
                                  moving_avg=25, n_heads=4, e_layers=1, d_ff=128, dropout=.3)
            self.assertEqual(sum(p.numel() for p in c(cfg).parameters()), 21599)
            self.assertEqual(sys.path, before_path)
            for key in previous: self.assertEqual(list(vars(sys.modules[key])).count('RevIN'), 0)
        finally:
            for key, module in previous.items():
                if module is None: sys.modules.pop(key, None)
                else: sys.modules[key] = module

    def test_archive_drift_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for filename in ('DeReFusion.py', 'derefusion_components.py', 'RevIN.py',
                             '__init__.py', 'BUNDLE_PIN_MANIFEST_V1.json'):
                shutil.copyfile(ARCHIVE/filename, root/filename)
            with (root/'RevIN.py').open('ab') as f: f.write(b'\n')
            with self.assertRaises(ValueError): verify_archive(root)

if __name__ == '__main__': unittest.main()
