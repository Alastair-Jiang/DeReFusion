"""Two-arm, validation-only pilot; frozen parent sources/packages are read-only."""
import os
for key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
    os.environ[key] = '2'
import argparse
import csv
import ctypes
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone
from types import SimpleNamespace
import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PROTOCOL = HERE / 'PROTOCOL_V1.json'
P = json.loads(PROTOCOL.read_text(encoding='utf-8'))
PARENT = ROOT / P['parent_directory']
PARENT_P = json.loads((PARENT / 'SHRINK_CDD_EXPLORATORY_PROTOCOL_V0.2.json').read_text(encoding='utf-8'))
PRIVATE = ROOT / P['private_storage']
BUNDLE = ROOT / PARENT_P['model']['bundle']
PREP = HERE / 'PREPARATION_V1.json'
SYNTH = HERE / 'SYNTHETIC_CHECK_V1.json'
RELEASE = HERE / 'EXECUTION_RELEASE_V1.json'
RESULT = HERE / 'RESULTS_V1.json'
ARMS = ('raw96', 'mixed48')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def utc():
    return datetime.now(timezone.utc).isoformat()

def dump(path, obj):
    path = Path(path)
    payload = (json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    if PRIVATE in path.parents:
        bounded_write(path, payload)
    else:
        if path.exists():
            raise ValueError('Refuse public record overwrite: ' + str(path))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)

def private_bytes():
    return sum(p.stat().st_size for p in PRIVATE.rglob('*') if p.is_file()) if PRIVATE.exists() else 0

def bounded_write(path, payload):
    path = Path(path)
    if PRIVATE not in path.parents or path.exists():
        raise ValueError('Private path outside candidate or overwrite')
    if private_bytes() + len(payload) > P['resources']['private_output_bytes']:
        raise ValueError('Private output hard cap exceeded')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as f:
        f.write(payload)

def verify_sources():
    if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() != P['head']:
        raise ValueError('HEAD drift')
    for filename, key in [('SHRINK_CDD_EXPLORATORY_PROTOCOL_V0.2.json', 'parent_protocol_sha256'),
                          ('CDD_PREPARATION_MANIFEST_V1_1.json', 'parent_preparation_sha256'),
                          ('CDD_SHRINK_EXPLORATORY_RESULTS_V1_1.json', 'parent_results_sha256')]:
        if sha(PARENT / filename) != P[key]:
            raise ValueError('Parent artifact drift: ' + filename)
    for filename, expected in PARENT_P['model']['source_sha256'].items():
        if sha(BUNDLE / filename) != expected:
            raise ValueError('Model source drift: ' + filename)

def aggregate(x):
    if x.ndim != 3 or x.shape[1:] != (96, 4):
        raise ValueError('Aggregation expects n x 96 x OHLC')
    blocks = x[:, :64].reshape(len(x), 16, 4, 4)
    old = np.stack((blocks[:, :, 0, 0], blocks[:, :, :, 1].max(axis=2),
                    blocks[:, :, :, 2].min(axis=2), blocks[:, :, -1, 3]), axis=2)
    return np.concatenate((old, x[:, 64:]), axis=1).astype(x.dtype, copy=False)

def model(arm):
    verify_sources()
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(P['model']['seed'])
    np.random.seed(P['model']['seed'])
    sys.path.insert(0, str(BUNDLE))
    spec = importlib.util.spec_from_file_location('compression_derefusion', BUNDLE / 'models/derefusion/DeReFusion.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    config = dict(P['model']['configuration'], seq_len=P['arms'][arm]['seq_len'])
    return module.Model(SimpleNamespace(**config)).float()

def peak_working_set():
    if os.name != 'nt':
        return None
    class Counters(ctypes.Structure):
        _fields_ = [('cb', ctypes.c_ulong), ('PageFaultCount', ctypes.c_ulong)] + [
            (name, ctypes.c_size_t) for name in ('PeakWorkingSetSize', 'WorkingSetSize',
            'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
            'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    psapi = ctypes.WinDLL('psapi', use_last_error=True)
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_ulong]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return int(counters.PeakWorkingSetSize)

def read_role(path, role, length):
    path = Path(path)
    meta = json.loads(path.with_suffix('.keys.json').read_text(encoding='utf-8'))
    if meta['payload_sha256'] != sha(path) or meta['role'] != role:
        raise ValueError('Role payload binding drift')
    with np.load(path, allow_pickle=False) as z:
        x, y, keys = z['x'].copy(), z['y'].copy(), z['keys'].tolist()
        sd, scale = float(z['close_output_std']), float(z['rmsse_denominator'])
        if str(z['role'].item()) != role:
            raise ValueError('Role mismatch')
    if x.shape != (len(keys), length, 4) or y.shape != (len(keys), 4):
        raise ValueError('Role shape mismatch')
    if keys != meta['expected_keys'] or len(set(keys)) != len(keys):
        raise ValueError('Key mismatch')
    if not np.isfinite(x).all() or not np.isfinite(y).all() or min(sd, scale) <= 0:
        raise ValueError('Non-finite or invalid scaler')
    return x, y, keys, sd, scale

def predict(m, x):
    m.eval()
    output = []
    with torch.no_grad():
        for i in range(0, len(x), 64):
            yp = m(torch.from_numpy(x[i:i+64]), None, None, None)
            if tuple(yp.shape) != (len(x[i:i+64]), 1, 4):
                raise ValueError('Forecast shape mismatch')
            output.append(yp[:, 0, 3].double().numpy())
    output = np.concatenate(output)
    if len(output) != len(x) or not np.isfinite(output).all():
        raise ValueError('Forecast coverage/non-finite failure')
    return output

def synthetic():
    verify_sources()
    days = np.arange(96, dtype=np.float64)
    closes = 100 + days
    x = np.stack((closes-.2, closes+.7, closes-.8, closes), axis=1)[None]
    reduced = aggregate(x)
    expected = np.stack([np.array([x[0, j, 0], x[0, j:j+4, 1].max(),
                         x[0, j:j+4, 2].min(), x[0, j+3, 3]]) for j in range(0, 64, 4)])
    assert np.array_equal(reduced[0, :16], expected)
    assert np.array_equal(reduced[:, 16:], x[:, 64:])
    mean, std = np.array([30, 40, 50, 60]), np.array([2, 3, 4, 5])
    assert np.allclose(aggregate((x-mean)/std), (aggregate(x)-mean)/std, rtol=0, atol=2e-14)
    changed = x.copy(); changed[:, 64:] += 1000
    assert np.array_equal(aggregate(changed)[:, :16], reduced[:, :16])
    params = {}
    for arm in ARMS:
        m = model(arm)
        xin = np.repeat(x if arm == 'raw96' else reduced, 3, axis=0).astype(np.float32)
        yp = m(torch.from_numpy(xin), None, None, None)
        assert tuple(yp.shape) == (3, 1, 4)
        loss = (yp[:, 0, 3]-torch.from_numpy(xin[:, -1, 3])).square().mean()
        loss.backward()
        assert torch.isfinite(loss) and all(torch.isfinite(q.grad).all() for q in m.parameters() if q.grad is not None)
        params[arm] = sum(q.numel() for q in m.parameters())
    assert params == {'raw96': 21743, 'mixed48': 21599}
    dump(SYNTH, {'result': 'PASS', 'timestamp_utc': utc(), 'protocol_sha256': sha(PROTOCOL),
                'runner_sha256': sha(__file__), 'parameters': params,
                'checks': ['OHLC group boundaries', 'Recent daily rows and last Close exact',
                           'Affine normalization commutation', 'Recent rows do not affect old blocks',
                           'Both model shapes and finite gradients', 'Parameter capacity comparison'],
                'scope': 'Synthetic only; no real performance claim'})
    print(json.dumps({'synthetic': 'PASS', 'parameters': params}), flush=True)

def prepare():
    verify_sources()
    meta = json.loads((PARENT / 'CDD_PREPARATION_MANIFEST_V1_1.json').read_text(encoding='utf-8'))
    combo = next(c for c in meta['combinations'] if c['asset'] == 'ETHUSD' and c['fraction'] == 1)
    result = {'result': 'PASS', 'timestamp_utc': utc(), 'protocol_sha256': sha(PROTOCOL),
              'runner_sha256': sha(__file__), 'arms': {a: {} for a in ARMS}, 'aggregation_seconds': 0.0}
    for role in ('train', 'validation'):
        source = Path(combo['packages'][role]['path'])
        if sha(source) != combo['packages'][role]['sha256']:
            raise ValueError('Parent package pin drift')
        x, y, keys, sd, scale = read_role(source, role, 96)
        started = time.perf_counter(); xc = aggregate(x)
        result['aggregation_seconds'] += time.perf_counter() - started
        dest = PRIVATE / 'mixed48' / (role + '.npz')
        buf = io.BytesIO()
        np.savez(buf, role=np.array(role), x=xc, y=y, keys=np.array(keys),
                 close_output_std=np.array(sd), rmsse_denominator=np.array(scale))
        bounded_write(dest, buf.getvalue())
        dump(dest.with_suffix('.keys.json'), {'role': role, 'expected_keys': keys, 'payload_sha256': sha(dest)})
        for arm, path, values in [('raw96', source, x), ('mixed48', dest, xc)]:
            result['arms'][arm][role] = {'path': str(path), 'sha256': sha(path),
                'manifest_sha256': sha(path.with_suffix('.keys.json')), 'keys_count': len(keys),
                'keys_sha256': hashlib.sha256('\n'.join(keys).encode()).hexdigest(), 'x_bytes': values.nbytes,
                'y_bytes': y.nbytes, 'shape': list(values.shape), 'close_output_std': sd, 'rmsse_denominator': scale}
        x2, y2, k2, sd2, scale2 = read_role(dest, role, 48)
        assert np.array_equal(x2, xc) and np.array_equal(y2, y) and keys == k2 and sd == sd2 and scale == scale2
        assert np.array_equal(x[:, -1, 3], x2[:, -1, 3])
    dump(PREP, result)
    print(json.dumps({'preparation': 'PASS', 'aggregation_seconds': result['aggregation_seconds']}), flush=True)

def verify_release():
    verify_sources()
    release = json.loads(RELEASE.read_text(encoding='utf-8'))
    if release['decision'] != 'APPROVED':
        raise ValueError('No execution approval')
    for path, key in [(PROTOCOL, 'protocol_sha256'), (Path(__file__), 'runner_sha256'),
                      (PREP, 'preparation_sha256'), (SYNTH, 'synthetic_sha256')]:
        if sha(path) != release[key]:
            raise ValueError('Execution pin drift: ' + key)
    return release

def release():
    verify_sources()
    s = json.loads(SYNTH.read_text(encoding='utf-8'))
    prepared = json.loads(PREP.read_text(encoding='utf-8'))
    assert s['result'] == prepared['result'] == 'PASS'
    assert s['protocol_sha256'] == prepared['protocol_sha256'] == sha(PROTOCOL)
    assert s['runner_sha256'] == prepared['runner_sha256'] == sha(__file__)
    dump(RELEASE, {'decision': 'APPROVED', 'timestamp_utc': utc(), 'protocol_id': P['protocol_id'],
         'head': P['head'], 'branch': P['branch'], 'decision_owner': P['decision_owner'],
         'scope': 'Two ETH train/validation fits; no test read, download, confirmation or publication',
         'protocol_sha256': sha(PROTOCOL), 'runner_sha256': sha(__file__),
         'preparation_sha256': sha(PREP), 'synthetic_sha256': sha(SYNTH),
         'model_source_sha256': PARENT_P['model']['source_sha256'], 'resources': P['resources'],
         'torch': torch.__version__, 'python': sys.version.split()[0]})
    print(json.dumps({'execution_release': 'APPROVED'}), flush=True)

def worker(arm, train, validation, output):
    verify_release()
    prepared = json.loads(PREP.read_text(encoding='utf-8'))['arms'][arm]
    for role, path in [('train', train), ('validation', validation)]:
        if Path(prepared[role]['path']).resolve() != Path(path).resolve() or sha(path) != prepared[role]['sha256']:
            raise ValueError('Worker must use released role paths')
    length = P['arms'][arm]['seq_len']
    xt, yt, kt, sd, scale = read_role(train, 'train', length)
    xv, yv, kv, sv, vs = read_role(validation, 'validation', length)
    if (sd, scale) != (sv, vs):
        raise ValueError('Shared ruler mismatch')
    m = model(arm)
    opt = torch.optim.Adam(m.parameters(), lr=.001, betas=(.9, .999), eps=1e-8, weight_decay=0)
    loader = DataLoader(TensorDataset(torch.from_numpy(xt), torch.from_numpy(yt)), batch_size=32,
                        shuffle=True, drop_last=False, generator=torch.Generator().manual_seed(17))
    iterator = iter(loader)
    best, state, history, seen, best_step = float('inf'), None, [], 0, None
    started = time.perf_counter()
    for step in range(1, 601):
        try:
            xb, yb = next(iterator)
        except StopIteration:
            iterator = iter(loader); xb, yb = next(iterator)
        m.train(); opt.zero_grad(set_to_none=True)
        pred = m(xb, None, None, None)
        loss = (pred[:, 0, 3]-yb[:, 3]).square().mean()
        if not torch.isfinite(loss):
            raise ValueError('Non-finite loss')
        loss.backward(); opt.step(); seen += len(xb)
        if step % 50 == 0:
            val = float(np.mean((predict(m, xv)-yv[:, 3].astype(np.float64))**2))
            improved = val < best
            if improved:
                best, best_step = val, step
                state = {k: v.detach().cpu().clone() for k, v in m.state_dict().items()}
            history.append({'step': step, 'validation_normalized_MSE': val, 'strict_improvement': improved})
    neural_seconds = time.perf_counter() - started
    peak = peak_working_set()
    m.load_state_dict(state)
    fp = predict(m, xv)
    flat, fv = xt.reshape(len(xt), -1).astype(np.float64), xv.reshape(len(xv), -1).astype(np.float64)
    xm, ym = flat.mean(axis=0), float(yt[:, 3].mean(dtype=np.float64))
    centered = flat-xm
    gram, rhs = centered.T@centered/len(flat), centered.T@(yt[:, 3].astype(np.float64)-ym)/len(flat)
    ridge_best, coef, ridge_lambda, ridge_history = float('inf'), None, None, []
    for alpha in PARENT_P['linear_baseline']['lambdas']:
        weights = np.linalg.solve(gram+alpha*np.eye(flat.shape[1]), rhs)
        score = float(np.mean(((fv-xm)@weights+ym-yv[:, 3].astype(np.float64))**2))
        ridge_history.append({'lambda': alpha, 'validation_normalized_MSE': score})
        if score < ridge_best:
            ridge_best, coef, ridge_lambda = score, weights, alpha
    preds = {'F': fp, 'L': (fv-xm)@coef+ym, 'P': xv[:, -1, 3].astype(np.float64)}
    mse = {arm: float(np.mean((p-yv[:, 3].astype(np.float64))**2)*sd**2) for arm, p in preds.items()}
    state_hash = hashlib.sha256()
    for key, value in sorted(state.items()):
        state_hash.update(key.encode()); state_hash.update(value.numpy().tobytes())
    summary = {'arm': arm, 'seed': 17, 'steps': 600, 'train_keys': len(kt), 'validation_keys': len(kv),
               'samples_seen': seen, 'effective_epochs': seen/len(kt), 'parameters': sum(q.numel() for q in m.parameters()),
               'best_step': best_step, 'history': history, 'neural_fit_validation_seconds': neural_seconds,
               'training_phase_peak_working_set_bytes': peak, 'ridge_lambda': ridge_lambda, 'ridge_history': ridge_history,
               'mse': mse, 'rmsse': {arm: math.sqrt(v/scale) for arm, v in mse.items()},
               'close_output_std': sd, 'rmsse_denominator': scale,
               'validation_keys_sha256': hashlib.sha256('\n'.join(kv).encode()).hexdigest(),
               'train_package_sha256': sha(train), 'validation_package_sha256': sha(validation),
               'state_tensor_sha256': state_hash.hexdigest(), 'test_inputs_received': False}
    checkpoint = io.BytesIO()
    torch.save({'F': state, 'summary': summary, 'ridge_coef': torch.from_numpy(coef),
                'ridge_x_mean': torch.from_numpy(xm), 'ridge_y_mean': ym}, checkpoint)
    bounded_write(output / 'model.pt', checkpoint.getvalue())
    buf = io.StringIO(newline='')
    w = csv.writer(buf)
    w.writerow(['key', 'F', 'L', 'P', 'target'])
    for i, key in enumerate(kv):
        w.writerow([key, *[float(preds[a][i]) for a in ('F', 'L', 'P')], float(yv[i, 3])])
    bounded_write(output / 'validation.predictions.csv', buf.getvalue().encode('utf-8'))
    dump(output / 'fit.json', summary)
    print(json.dumps(summary), flush=True)

def run():
    verify_release()
    prep = json.loads(PREP.read_text(encoding='utf-8'))
    if RESULT.exists():
        raise ValueError('No result overwrite or automatic retry')
    summaries, start = [], time.monotonic()
    for arm in ARMS:
        remaining = P['resources']['batch_seconds']-(time.monotonic()-start)
        if remaining <= 0:
            raise ValueError('Batch time hard cap exhausted')
        out = PRIVATE / 'runs' / arm
        if out.exists():
            raise ValueError('Prior attempt exists; stop')
        cmd = [sys.executable, '-B', str(Path(__file__).resolve()), '--phase', 'worker', '--arm', arm,
               '--train', prep['arms'][arm]['train']['path'], '--validation', prep['arms'][arm]['validation']['path'],
               '--output', str(out)]
        wall = time.perf_counter()
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=min(remaining, P['resources']['worker_seconds']))
        if proc.returncode:
            raise RuntimeError(proc.stderr[-2000:])
        summary = json.loads(proc.stdout.strip().splitlines()[-1])
        summary['worker_seconds'] = time.perf_counter()-wall
        summaries.append(summary)
        print(json.dumps({'arm_complete': arm, 'neural_seconds': summary['neural_fit_validation_seconds'],
                          'validation_RMSSE_F': summary['rmsse']['F']}), flush=True)
    if time.monotonic()-start >= P['resources']['batch_seconds']:
        raise ValueError('Batch hard cap exceeded')
    assert summaries[0]['validation_keys_sha256'] == summaries[1]['validation_keys_sha256']
    assert summaries[0]['samples_seen'] == summaries[1]['samples_seen'] == 18900
    assert summaries[0]['mse']['P'] == summaries[1]['mse']['P']
    parent = json.loads((PARENT / 'CDD_SHRINK_EXPLORATORY_RESULTS_V1_1.json').read_text(encoding='utf-8'))
    old = next(r['fit'] for r in parent['runs'] if r['asset'] == 'ETHUSD' and r['fraction'] == 1 and r['seed'] == 17)
    result = {'protocol_id': P['protocol_id'], 'scope': 'EXPLORATORY VALIDATION-ONLY FEASIBILITY PILOT',
              'finished_at_utc': utc(), 'release_sha256': sha(RELEASE), 'arms': summaries,
              'fresh_control_matches_parent_state': summaries[0]['state_tensor_sha256'] == old['state_tensor_sha256'],
              'fresh_control_matches_parent_validation_MSE': summaries[0]['mse']['F'] == old['validation_mse']['F'],
              'input_x_bytes_ratio': prep['arms']['mixed48']['train']['x_bytes']/prep['arms']['raw96']['train']['x_bytes'],
              'aggregation_seconds': prep['aggregation_seconds'], 'private_bytes': private_bytes(),
              'batch_seconds': time.monotonic()-start, 'total_optimizer_steps': 1200,
              'test_read_or_scored': False, 'independent_review': 'PENDING',
              'limitations': [P['timing_caveat'], P['mixed_time_resolution_caveat'],
                              P['model']['initialization'], P['scope'], P['interpretation']]}
    dump(RESULT, result)
    print(json.dumps({'completed': 2, 'results': str(RESULT)}), flush=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', choices=['synthetic', 'prepare', 'release', 'run', 'worker'], required=True)
    ap.add_argument('--arm', choices=ARMS)
    for key in ('train', 'validation', 'output'):
        ap.add_argument('--'+key, type=Path)
    args = ap.parse_args()
    if args.phase == 'worker':
        if not all((args.arm, args.train, args.validation, args.output)):
            ap.error('Worker train/validation inputs required; test arguments unsupported')
        worker(args.arm, args.train, args.validation, args.output)
    elif args.phase == 'synthetic': synthetic()
    elif args.phase == 'prepare': prepare()
    elif args.phase == 'release': release()
    elif args.phase == 'run': run()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        failure = {'timestamp_utc': utc(), 'exception_type': type(e).__name__, 'reason': str(e), 'runner_sha256': sha(__file__)}
        dump(HERE / ('FAILURE_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json'), failure)
        raise
