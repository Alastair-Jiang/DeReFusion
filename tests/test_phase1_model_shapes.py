import importlib
import unittest
from types import SimpleNamespace

import torch


class Phase1ModelShapeTest(unittest.TestCase):
    def test_all_frozen_models_accept_ms_protocol_shape(self):
        configs = SimpleNamespace(
            task_name='long_term_forecast',
            seq_len=96,
            label_len=48,
            pred_len=24,
            enc_in=4,
            dec_in=4,
            c_out=1,
            d_model=32,
            moving_avg=25,
            factor=1,
            dropout=0.1,
            n_heads=8,
            d_ff=128,
            e_layers=2,
            activation='gelu',
            embed='timeF',
            freq='b',
            top_k=5,
            num_kernels=6,
            num_class=2,
        )
        modules = [
            'models.revin-DLinear',
            'models.derefusion.DeReFusion',
            'models.revin-PatchTST',
            'models.revin-iTransformer',
            'models.revin-TimesNet',
        ]
        x_enc = torch.randn(2, configs.seq_len, configs.enc_in)
        for module_name in modules:
            with self.subTest(model=module_name):
                model = importlib.import_module(module_name).Model(configs).eval()
                with torch.no_grad():
                    output = model(x_enc, None, None, None)
                self.assertEqual(tuple(output.shape), (2, configs.pred_len, configs.enc_in))
                self.assertTrue(torch.isfinite(output).all())


if __name__ == '__main__':
    unittest.main()
