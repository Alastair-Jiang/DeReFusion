"""Shared building blocks for the DeReFusion model family.

This module is intentionally placed under ``layers/`` (which ``exp/exp_basic.py``
does *not* scan), so importing it never registers a new model name.

It centralises the pieces that were previously copy-pasted across the seven
files under ``models/derefusion/``:

* ``MovingAvg`` / ``SeriesDecomposition`` / ``DLinearBranch`` -- identical in
  every variant.
* ``ResidualBranch`` -- a single composable definition that reproduces the three
  previously duplicated shapes:
    * ``use_lstm=True,  use_transformer=True``  -> the old ``TransformerLSTMResidualBranch``
      (DeReFusion and the three gate variants)
    * ``use_lstm=False, use_transformer=True``  -> the old ``TransformerResidualBranch``
      (DeReFusion-woLSTM)
    * ``use_lstm=True,  use_transformer=False`` -> the old ``LSTMResidualBranch``
      (DeReFusion-woTransformer)

The sub-modules are constructed in the exact same order as the three original
classes did, so parameter initialisation (and therefore the RNG stream, and the
resulting weights) is byte-for-byte identical to the pre-refactor code.

The Transformer hyper-parameters continue to come from ``configs``:
``n_heads -> nhead``, ``e_layers -> num_layers``, ``d_ff -> dim_feedforward``,
``dropout -> dropout``. ``n_heads`` has no default. The LSTM ``num_layers=1`` is
kept hard-wired on purpose: it is not part of the pre-registered protocol.

To plug in a *new* residual-branch implementation later, either add a new flag
combination here or expose an alternative branch class and switch to it in each
variant's ``Model.__init__`` -- the fusion logic in the variants stays untouched.
"""

import torch
import torch.nn as nn


# ========== 1. Decomposition building blocks ==========
class MovingAvg(nn.Module):
    """Moving average block to highlight the trend of time series."""

    def __init__(self, kernel_size: int):
        super().__init__()
        self.kernel_size = kernel_size
        self.avg = nn.AvgPool1d(kernel_size=kernel_size, stride=1, padding=0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        front = x[:, :1, :].repeat(1, (self.kernel_size - 1) // 2, 1)
        end = x[:, -1:, :].repeat(1, (self.kernel_size - 1) // 2, 1)
        x_padded = torch.cat([front, x, end], dim=1)
        return self.avg(x_padded.permute(0, 2, 1)).permute(0, 2, 1)


class SeriesDecomposition(nn.Module):
    """Decompose a time series into seasonal and trend components."""

    def __init__(self, kernel_size: int = 25):
        super().__init__()
        self.moving_avg = MovingAvg(kernel_size)

    def forward(self, x: torch.Tensor):
        trend = self.moving_avg(x)
        return x - trend, trend


# ========== 2. Base branch ==========
class DLinearBranch(nn.Module):
    """DLinear-style branch: decompose -> project seasonal & trend independently."""

    def __init__(self, seq_len: int, pred_len: int, kernel_size: int = 25):
        super().__init__()
        self.decomp = SeriesDecomposition(kernel_size)
        self.linear_seasonal = nn.Linear(seq_len, pred_len)
        self.linear_trend = nn.Linear(seq_len, pred_len)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        seasonal, trend = self.decomp(x)
        seasonal_out = self.linear_seasonal(seasonal.permute(0, 2, 1))
        trend_out = self.linear_trend(trend.permute(0, 2, 1))
        return (seasonal_out + trend_out).permute(0, 2, 1)


# ========== 3. Composable residual branch ==========
class ResidualBranch(nn.Module):
    """
    Single definition behind the three residual-branch shapes used across the
    DeReFusion family. Construction order matches the original classes exactly,
    so parameter initialisation is unchanged.

    Shapes:
      (use_lstm=True,  use_transformer=True)  feature_proj -> LSTM -> Transformer -> proj
      (use_lstm=False, use_transformer=True)  feature_proj -> Transformer -> proj
      (use_lstm=True,  use_transformer=False) LSTM(input=enc_in) -> proj
    """

    def __init__(
        self, enc_in: int, d_model: int, seq_len: int, pred_len: int,
        use_lstm: bool, use_transformer: bool,
        n_heads: int, e_layers: int, d_ff: int, dropout: float,
    ):
        super().__init__()
        self.use_lstm = use_lstm
        self.use_transformer = use_transformer

        if use_transformer:
            self.feature_proj = nn.Linear(enc_in, d_model)

        if use_lstm:
            lstm_input = d_model if use_transformer else enc_in
            self.lstm = nn.LSTM(
                input_size=lstm_input, hidden_size=d_model,
                num_layers=1, batch_first=True,
            )

        if use_transformer:
            encoder_layer = nn.TransformerEncoderLayer(
                d_model=d_model, nhead=n_heads,
                dim_feedforward=d_ff, batch_first=True, dropout=dropout,
            )
            self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=e_layers)

        self.time_proj = nn.Linear(seq_len, pred_len)
        self.channel_proj = nn.Linear(d_model, enc_in)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if self.use_transformer:
            x = self.feature_proj(x)
        if self.use_lstm:
            x, _ = self.lstm(x)
        if self.use_transformer:
            x = self.transformer(x)
        x = self.time_proj(x.permute(0, 2, 1)).permute(0, 2, 1)
        return self.channel_proj(x)
