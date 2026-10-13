"""Check publication paths without reading data values or changing Git state."""
import argparse
from fnmatch import fnmatchcase
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT/'docs/DRF_ARTIFACT_BOUNDARY_V1_2026-10-13.json'

def violations(paths, policy):
    denied = [r for r in policy['rules'] if r['disposition'] == 'local-only']
    def matches(path, rule):
        path, pattern = path.casefold(), rule['path_glob'].casefold()
        return fnmatchcase(path, pattern) or (pattern.startswith('**/') and fnmatchcase(path, pattern[3:]))
    return {p: [r['basis'] for r in denied if matches(p, r)]
            for p in paths if any(matches(p, r) for r in denied)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--baseline', help='Check added/modified paths in HEAD relative to a verified baseline')
    args = ap.parse_args()
    cmd = ['git', 'diff', '--name-only', '-z', '--diff-filter=ACMR']
    cmd += [args.baseline, 'HEAD'] if args.baseline else ['--cached']
    paths = [p for p in subprocess.check_output(cmd, cwd=ROOT).decode().split('\0') if p]
    policy = json.loads(POLICY.read_text(encoding='utf-8'))
    bad = violations(paths, policy)
    print(json.dumps({'scope': 'HEAD changes' if args.baseline else 'staged changes',
                      'checked_paths': len(paths), 'violations': bad, 'passed': not bad}, indent=2))
    raise SystemExit(1 if bad else 0)

if __name__ == '__main__': main()
