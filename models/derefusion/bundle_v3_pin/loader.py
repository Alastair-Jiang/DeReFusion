"""Load archived sources with private dependency bindings, without sys.path edits.

The three archival files retain their exact executed bytes. Only their two
absolute project imports are redirected in a module-local builtins mapping.
Global ``layers`` modules and user model files are never replaced.
"""
import builtins
import hashlib
import json
from pathlib import Path
from types import ModuleType

HERE = Path(__file__).resolve().parent
PINS = {
    'DeReFusion.py': '468a861d4e616a414ec603df87128ebe55bafe5f296502b54aef8aed23e5b091',
    'derefusion_components.py': '91ae3bce16f8d758be71987672144fe400dd5f6a65352bf040c90c678ccd0a33',
    'RevIN.py': 'a7dc201d7ce2604bbdc19262d7c9ba8073a665e70f7cb734543d640c63bcf5cc',
    '__init__.py': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
}

def verify_archive(directory=HERE):
    directory = Path(directory)
    observed = {}
    for name, expected in PINS.items():
        digest = hashlib.sha256((directory/name).read_bytes()).hexdigest()
        if digest != expected:
            raise ValueError('Archived source drift: ' + name)
        observed[name] = digest
    manifest = json.loads((directory/'BUNDLE_PIN_MANIFEST_V1.json').read_text(encoding='utf-8'))
    if manifest['files'] != observed:
        raise ValueError('Archive manifest drift')
    return observed

def load_model_class(directory=HERE):
    """Return the frozen Model class; checkpoints must serialize state_dict only."""
    directory = Path(directory)
    verify_archive(directory)
    deps = {}
    original_import = builtins.__import__

    def private_import(name, globals=None, locals=None, fromlist=(), level=0):
        if level == 0 and name in deps:
            if not fromlist:
                raise ImportError('Pinned dependencies require explicit from-import')
            return deps[name]
        return original_import(name, globals, locals, fromlist, level)

    def load(filename, suffix):
        module = ModuleType('_derefusion_bundle_v3_' + suffix)
        module.__file__ = str(directory/filename)
        module.__dict__['__builtins__'] = dict(vars(builtins), __import__=private_import)
        exec(compile((directory/filename).read_bytes(), module.__file__, 'exec'), module.__dict__)
        return module

    deps['layers.RevIN'] = load('RevIN.py', 'revin')
    deps['layers.derefusion_components'] = load('derefusion_components.py', 'components')
    return load('DeReFusion.py', 'model').Model
