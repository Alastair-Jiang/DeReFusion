"""Versioned fixed OHLC aggregation; no fitting, targets, I/O, or role selection."""
from dataclasses import dataclass
import hashlib
import json
import numpy as np

TRANSFORM_ID = 'fixed-ohlc-block-aggregate'
TRANSFORM_VERSION = 1
OHLC = ('open', 'high', 'low', 'close')

@dataclass(frozen=True)
class AggregationPlan:
    context_days: int
    block_days: int
    n_blocks: int
    recent_days: int
    channel_order: tuple = OHLC

    def __post_init__(self):
        for name in ('context_days', 'block_days', 'n_blocks', 'recent_days'):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(name + ' must be a positive integer')
        if self.block_days*self.n_blocks+self.recent_days != self.context_days:
            raise ValueError('Plan must partition the complete original context')
        if not isinstance(self.channel_order, tuple) or self.channel_order != OHLC:
            raise ValueError('Channel order must be immutable OHLC')

    def canonical_json(self):
        return json.dumps({'transform_id': TRANSFORM_ID, 'transform_version': TRANSFORM_VERSION,
                           'context_days': self.context_days, 'block_days': self.block_days,
                           'n_blocks': self.n_blocks, 'recent_days': self.recent_days,
                           'channel_order': self.channel_order}, sort_keys=True, separators=(',', ':'))

    def config_sha256(self):
        return hashlib.sha256(self.canonical_json().encode('utf-8')).hexdigest()

    def position_spans_days(self):
        return [self.block_days]*self.n_blocks+[1]*self.recent_days

def aggregate_ohlc(x, plan):
    if not isinstance(plan, AggregationPlan):
        raise ValueError('An AggregationPlan is required')
    if not isinstance(x, np.ndarray) or x.ndim != 3 or x.shape[1:] != (plan.context_days, 4):
        raise ValueError('Input must have shape (n, context_days, 4)')
    if x.dtype.kind not in 'fiu' or not np.isfinite(x).all():
        raise ValueError('Finite real numeric OHLC input required')
    early = plan.n_blocks*plan.block_days
    blocks = x[:, :early].reshape(len(x), plan.n_blocks, plan.block_days, 4)
    summaries = np.stack((blocks[:, :, 0, 0], blocks[:, :, :, 1].max(axis=2),
                          blocks[:, :, :, 2].min(axis=2), blocks[:, :, -1, 3]), axis=2)
    # Cross-channel inequalities cannot be checked after channelwise scaling.
    return np.concatenate((summaries, x[:, early:]), axis=1).astype(x.dtype, copy=False)

def derived_cache_key(*, source_package_sha256, source_manifest_sha256,
                      scaler_sha256, module_sha256, numpy_version, plan):
    """Bind payload, role/key metadata, scaler, configuration and implementation."""
    digests = {'source_package_sha256': source_package_sha256,
               'source_manifest_sha256': source_manifest_sha256,
               'scaler_sha256': scaler_sha256, 'module_sha256': module_sha256}
    for name, value in digests.items():
        if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
            raise ValueError(name + ' must be lowercase SHA-256')
    if not isinstance(plan, AggregationPlan) or not isinstance(numpy_version, str) or not numpy_version:
        raise ValueError('Plan and NumPy version required')
    identity = dict(digests, numpy_version=numpy_version, configuration_sha256=plan.config_sha256())
    return hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
