"""Create a new, bound two-arm replay attempt without altering frozen artifacts.

Generation and synthetic checks are not execution approval. Preparing roles
requires existing hash-matching private inputs; fitting requires a separate
authorization bound to the generated protocol and current checkout.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PureWindowsPath
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HISTORY = 'research_work/project_management_2026_10_10/compression_pilot_2026_10_13'
SOURCE_FILES = [f'{HISTORY}/run_pilot_v1.py', f'{HISTORY}/PROTOCOL_V1.json',
                f'{HISTORY}/PREPARATION_V1.json', f'{HISTORY}/RESULTS_V1.json',
                'reproduction/analysis/compression_replay.py',
                'reproduction/preprocessing/fixed_ohlc.py',
                'reproduction/preprocessing/__init__.py',
                'models/derefusion/bundle_v3_pin/loader.py',
                'models/derefusion/bundle_v3_pin/BUNDLE_PIN_MANIFEST_V1.json',
                'requirements/torch-cpu.txt', 'requirements/compression-cpu.txt']

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def write_new(path, obj):
    with Path(path).open('x', encoding='utf-8') as f:
        f.write(json.dumps(obj, indent=2, ensure_ascii=False)+'\n')

def resolve_relative(root, path):
    root = Path(root).resolve()
    candidate = Path(path)
    windows = PureWindowsPath(str(path))
    if candidate.is_absolute() or windows.drive or windows.root or '\\' in str(path) or '..' in candidate.parts:
        raise ValueError('Repository-relative path required')
    resolved = (root/candidate).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError('Path escapes repository')
    return resolved

def historical_private_relative(path):
    # Read only from hash-bound historical metadata, never accept this form in
    # new manifests. Cross-machine prefix rebinding is recorded in the new prep.
    parts = PureWindowsPath(str(path)).parts
    if 'data' not in parts:
        raise ValueError('Historical source is outside the declared private data area')
    relative = Path(*parts[parts.index('data'):]).as_posix()
    if not relative.startswith('data/shrink-cdd-20261013-v1/packages_v1_1/ETHUSD_f100/'):
        raise ValueError('Only inherited ETH f100 training/validation inputs are supported')
    return relative

def generate(name, root=ROOT):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', name):
        raise ValueError('Attempt name must contain only letters, digits, underscore or hyphen')
    root = Path(root).resolve()
    attempt = root/'data/compression-replay-attempts'/name
    protocol = copy.deepcopy(load(root/HISTORY/'PROTOCOL_V1.json'))
    protocol['repository'] = str(root)
    protocol['head'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    protocol['branch'] = subprocess.check_output(['git', 'branch', '--show-current'], cwd=root, text=True).strip()
    protocol['protocol_id'] += '-REPLAY-' + name
    protocol['status'] = 'APPROVED_SYNTHETIC_AND_PREPARATION_ONLY; separate execution authorization required'
    protocol['private_storage'] = f'data/compression-replay-attempts/{name}/artifacts'
    protocol['replay'] = {'scope': 'Reproduce the two historical arms; no raw48 or new test assessment',
                          'code_sha256': {p: sha(root/p) for p in SOURCE_FILES},
                          'source_archive': 'models/derefusion/bundle_v3_pin',
                          'environment': {'python': '3.11.15', 'torch': '2.5.1+cpu', 'numpy': '2.1.2'},
                          'paths': 'New preparation paths are repository-relative; do not rewrite historical manifests',
                          'historical_state_targets': {r['arm']: r['state_tensor_sha256']
                              for r in load(root/HISTORY/'RESULTS_V1.json')['arms']},
                          'historical_validation_mse': {r['arm']: r['mse']['F']
                              for r in load(root/HISTORY/'RESULTS_V1.json')['arms']}}
    attempt.mkdir(parents=True, exist_ok=False)
    write_new(attempt/'PROTOCOL_V1.json', protocol)
    wrapper = '''from pathlib import Path
import sys
ROOT = next(p for p in Path(__file__).resolve().parents if (p/'.git').exists())
sys.path.insert(0, str(ROOT))
from reproduction.analysis.compression_replay import attempt_main
if __name__ == '__main__': attempt_main(Path(__file__).resolve().parent, ROOT)
'''
    (attempt/'run_pilot_v1.py').write_text(wrapper, encoding='utf-8')
    write_new(attempt/'EXECUTION_AUTHORIZATION_TEMPLATE.json', {
        'decision': 'NOT_APPROVED', 'scope': 'two-arm-validation-replay',
        'head': protocol['head'], 'protocol_sha256': sha(attempt/'PROTOCOL_V1.json'),
        'decision_owner': None, 'authorization_basis': None,
        'note': 'This template is never execution authorization; issue a separate EXECUTION_AUTHORIZATION.json after review.'})
    return attempt

def configure(attempt, root=ROOT):
    root, attempt = Path(root).resolve(), Path(attempt).resolve()
    if not attempt.is_relative_to(root/'data/compression-replay-attempts'):
        raise ValueError('Replay attempt must be in the new private attempt area')
    protocol = load(attempt/'PROTOCOL_V1.json')
    for path, expected in protocol['replay']['code_sha256'].items():
        if sha(resolve_relative(root, path)) != expected:
            raise ValueError('Replay implementation drift: ' + path)
    frozen = root/HISTORY/'run_pilot_v1.py'
    spec = importlib.util.spec_from_file_location('_frozen_compression_replay_engine', frozen)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT, module.HERE, module.P = root, attempt, protocol
    module.__file__ = str(attempt/'run_pilot_v1.py')
    module.PROTOCOL = attempt/'PROTOCOL_V1.json'
    module.PRIVATE = resolve_relative(root, protocol['private_storage'])
    for attr, filename in [('PREP', 'PREPARATION_V1.json'), ('SYNTH', 'SYNTHETIC_CHECK_V1.json'),
                           ('RELEASE', 'EXECUTION_RELEASE_V1.json'), ('RESULT', 'RESULTS_V1.json')]:
        setattr(module, attr, attempt/filename)
    from models.derefusion.bundle_v3_pin.loader import load_model_class, verify_archive
    from reproduction.preprocessing import fixed_ohlc

    def verify_sources():
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
        if head != protocol['head']:
            raise ValueError('Replay HEAD drift; generate a fresh attempt')
        for path, expected in protocol['replay']['code_sha256'].items():
            if sha(resolve_relative(root, path)) != expected:
                raise ValueError('Replay implementation drift: ' + path)
        for filename, key in [('SHRINK_CDD_EXPLORATORY_PROTOCOL_V0.2.json', 'parent_protocol_sha256'),
                              ('CDD_PREPARATION_MANIFEST_V1_1.json', 'parent_preparation_sha256'),
                              ('CDD_SHRINK_EXPLORATORY_RESULTS_V1_1.json', 'parent_results_sha256')]:
            if sha(module.PARENT/filename) != protocol[key]:
                raise ValueError('Historical parent drift')
        verify_archive(root/protocol['replay']['source_archive'])
        import platform
        actual = {'python': platform.python_version(), 'torch': module.torch.__version__, 'numpy': module.np.__version__}
        if actual != protocol['replay']['environment']:
            raise ValueError('Replay environment version mismatch: ' + json.dumps(actual))

    def model(arm):
        verify_sources()
        module.torch.set_num_threads(2)
        module.torch.use_deterministic_algorithms(True)
        module.torch.manual_seed(protocol['model']['seed'])
        module.np.random.seed(protocol['model']['seed'])
        config = dict(protocol['model']['configuration'], seq_len=protocol['arms'][arm]['seq_len'])
        return load_model_class(root/protocol['replay']['source_archive'])(module.SimpleNamespace(**config)).float()

    plan = fixed_ohlc.AggregationPlan(96, 4, 16, 32)
    module.verify_sources, module.model = verify_sources, model
    module.aggregate = lambda x: fixed_ohlc.aggregate_ohlc(x, plan)

    def prepare():
        verify_sources()
        historical = load(root/HISTORY/'PREPARATION_V1.json')
        result = {'result': 'PASS', 'timestamp_utc': module.utc(), 'protocol_sha256': sha(module.PROTOCOL),
                  'runner_sha256': sha(module.__file__), 'arms': {a: {} for a in module.ARMS},
                  'aggregation_seconds': 0.0, 'historical_source_rebinding': {},
                  'position_spans_days': {'raw96': [1]*96, 'mixed48': plan.position_spans_days()}}
        for role in ('train', 'validation'):
            h = historical['arms']['raw96'][role]
            relative = historical_private_relative(h['path'])
            source = resolve_relative(root, relative)
            if sha(source) != h['sha256'] or sha(source.with_suffix('.keys.json')) != h['manifest_sha256']:
                raise ValueError('Inherited private source binding drift')
            x, y, keys, sd, scale = module.read_role(source, role, 96)
            start = module.time.perf_counter(); xc = module.aggregate(x)
            result['aggregation_seconds'] += module.time.perf_counter()-start
            dest = module.PRIVATE/'mixed48'/(role+'.npz')
            buf = module.io.BytesIO()
            module.np.savez(buf, role=module.np.array(role), x=xc, y=y, keys=module.np.array(keys),
                            close_output_std=module.np.array(sd), rmsse_denominator=module.np.array(scale))
            module.bounded_write(dest, buf.getvalue())
            module.dump(dest.with_suffix('.keys.json'), {'role': role, 'expected_keys': keys, 'payload_sha256': sha(dest)})
            result['historical_source_rebinding'][role] = {'old_path': h['path'], 'new_relative_path': relative, 'sha256': sha(source)}
            for arm, path, values in [('raw96', source, x), ('mixed48', dest, xc)]:
                result['arms'][arm][role] = {'path': path.relative_to(root).as_posix(), 'sha256': sha(path),
                    'manifest_sha256': sha(path.with_suffix('.keys.json')), 'keys_count': len(keys),
                    'keys_sha256': hashlib.sha256('\n'.join(keys).encode()).hexdigest(), 'x_bytes': values.nbytes,
                    'y_bytes': y.nbytes, 'shape': list(values.shape), 'close_output_std': sd, 'rmsse_denominator': scale}
            assert sha(dest) == historical['arms']['mixed48'][role]['sha256'], 'Derived payload does not reproduce historical pin'
        module.dump(module.PREP, result)
        print(json.dumps({'preparation': 'PASS', 'path_format': 'repository-relative'}))

    old_verify_release = module.verify_release
    def verify_release():
        release = old_verify_release()
        if sha(attempt/'EXECUTION_AUTHORIZATION.json') != release['authorization_sha256']:
            raise ValueError('Execution authorization changed')
        return release

    def release():
        verify_sources()
        authorization = load(attempt/'EXECUTION_AUTHORIZATION.json')
        if (authorization.get('decision') != 'APPROVED' or authorization.get('head') != protocol['head']
            or authorization.get('protocol_sha256') != sha(module.PROTOCOL)
            or authorization.get('scope') != 'two-arm-validation-replay'
            or not authorization.get('decision_owner') or not authorization.get('authorization_basis')):
            raise ValueError('Missing exact-bound execution authorization')
        synthetic, prepared = load(module.SYNTH), load(module.PREP)
        assert synthetic['result'] == prepared['result'] == 'PASS'
        assert synthetic['protocol_sha256'] == prepared['protocol_sha256'] == sha(module.PROTOCOL)
        assert synthetic['runner_sha256'] == prepared['runner_sha256'] == sha(module.__file__)
        module.dump(module.RELEASE, {'decision': 'APPROVED', 'timestamp_utc': module.utc(),
            'protocol_sha256': sha(module.PROTOCOL), 'runner_sha256': sha(module.__file__),
            'preparation_sha256': sha(module.PREP), 'synthetic_sha256': sha(module.SYNTH),
            'authorization_sha256': sha(attempt/'EXECUTION_AUTHORIZATION.json'),
            'head': protocol['head'], 'code_sha256': protocol['replay']['code_sha256'],
            'resources': protocol['resources'], 'scope': 'two-arm-validation-replay'})

    module.prepare, module.release, module.verify_release = prepare, release, verify_release
    return module

def attempt_main(attempt, root=ROOT):
    module = configure(attempt, root)
    previous = Path.cwd()
    try:
        os.chdir(root)  # All new manifest and worker CLI paths are rooted here.
        module.main()
    except Exception as exc:
        module.dump(Path(attempt)/('FAILURE_'+module.datetime.now(module.timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json'),
                    {'reason': str(exc), 'exception_type': type(exc).__name__, 'timestamp_utc': module.utc()})
        raise
    finally: os.chdir(previous)

def main():
    ap = argparse.ArgumentParser(description='Generate a new unapproved private replay attempt; no training is launched.')
    ap.add_argument('--name', required=True)
    args = ap.parse_args()
    print(generate(args.name))

if __name__ == '__main__': main()
