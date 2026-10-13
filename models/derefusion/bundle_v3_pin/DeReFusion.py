import torch
import torch.nn as nn
from layers.RevIN import RevIN
from layers.derefusion_components import DLinearBranch, ResidualBranch


class Model(nn.Module):
    """
    DeReFusion — Decomposition-Residual Fusion for Financial Time Series

    Architecture:
      1. RevIN normalisation
      2. DLinear branch: seasonal-trend decomposition → linear projection (base)
      3. TransformerLSTM branch: LSTM → Transformer → projection (residual)
      4. Direct additive fusion: base + residual
      5. RevIN de-normalisation
    """

    def __init__(self, configs):
        super().__init__()
        self.seq_len: int = configs.seq_len
        self.pred_len: int = configs.pred_len
        self.enc_in: int = configs.enc_in
        self.d_model: int = configs.d_model
        kernel_size: int = getattr(configs, "moving_avg", 25)

        self.revin = RevIN(self.enc_in)
        self.dlinear_branch = DLinearBranch(self.seq_len, self.pred_len, kernel_size)
        self.res_branch = ResidualBranch(
            self.enc_in, self.d_model, self.seq_len, self.pred_len,
            use_lstm=True, use_transformer=True,
            n_heads=configs.n_heads, e_layers=configs.e_layers,
            d_ff=configs.d_ff, dropout=configs.dropout,
        )

    def forecast(self, x_enc: torch.Tensor) -> torch.Tensor:
        x_norm = self.revin(x_enc, "norm")
        base = self.dlinear_branch(x_norm)
        residual = self.res_branch(x_norm)
        fused = base + residual
        return self.revin(fused, "denorm")

    def forward(self, x_enc, x_mark_enc, x_dec, x_mark_dec, mask=None):
        return self.forecast(x_enc)
