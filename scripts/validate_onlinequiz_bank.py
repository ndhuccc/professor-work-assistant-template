"""Run pinned OnlineQuiz schema and pure row validators without ORM or network."""
from __future__ import annotations

import __future__
import argparse
import ast
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace

from prepare_onlinequiz_bank import no_duplicate_keys, prepare

ROOT = Path(__file__).resolve().parents[1]
PROFILE = 'ndhuccc/OnlineQuiz-v2@5f81609e0fb9ebaa1536384f6e4d58c9f2d90f17'
PURE_FUNCTIONS = {'normalize_option_text', 'parse_option_line', 'parse_correct_letters', 'validate_question_row'}
PURE_CONSTANTS = {'LEGACY_LETTER_PREFIX_RE', 'FORMAT_TO_TYPE'}


def load_validators(root=ROOT):
    """Execute only the original schema and whitelisted pure validation nodes."""
    upstream = Path(root) / 'integrations/onlinequiz/upstream'
    manifest = json.loads((Path(root) / 'config/source-bundle.json').read_text(encoding='utf-8'))
    for name in ('schemas.py', 'import_json.py'):
        relative = f'integrations/onlinequiz/upstream/{name}'
        expected = next(x['source_blob_sha'] for x in manifest['files'] if x['destination'] == relative)
        raw = (upstream / name).read_bytes()
        actual = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if actual != expected:
            raise ValueError(f'Pinned source mismatch: {relative}')
    spec = importlib.util.spec_from_file_location('onlinequiz_pinned_schema', upstream / 'schemas.py')
    schema = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(schema)
    source = ast.parse((upstream / 'import_json.py').read_text(encoding='utf-8'))
    nodes = []
    selected = set()
    for node in source.body:
        if isinstance(node, ast.FunctionDef) and node.name in PURE_FUNCTIONS:
            nodes.append(node)
            selected.add(node.name)
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in PURE_CONSTANTS:
            nodes.append(node)
            selected.add(node.targets[0].id)
    if selected != PURE_FUNCTIONS | PURE_CONSTANTS:
        raise ValueError('Pinned row validator structure changed')
    # Type tags only; no Django model is imported or instantiated.
    context = {'re': re, 'Question': SimpleNamespace(Type=SimpleNamespace(SINGLE='single', MULTIPLE='multiple'))}
    module = ast.Module(body=nodes, type_ignores=[])
    exec(compile(module, str(upstream / 'import_json.py'), 'exec', flags=__future__.annotations.compiler_flag), context)
    return schema.ImportPayload, context['validate_question_row']


def validate(data, *, expected_count=None, root=ROOT):
    bank, warnings = prepare(data, expected_count=expected_count)
    payload_type, validate_row = load_validators(root)
    payload = payload_type.model_validate(bank)
    for question in payload.questions:
        validate_row(question)
    return {'status': 'pinned_native_format_valid', 'profile': PROFILE,
            'question_count': len(payload.questions), 'warnings': warnings,
            'scope': 'Original schema and pure row code; isolated type tags; no ORM',
            'not_verified': ['live server compatibility', 'answer correctness', 'Bloom levels',
                             'KaTeX rendering', 'database import', 'database answer readback'],
            'imported': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--expected-count', type=int)
    args = parser.parse_args()
    try:
        raw = args.input.read_bytes()
        data = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=no_duplicate_keys,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f'Invalid JSON constant: {value}')))
        report = validate(data, expected_count=args.expected_count)
        report['input_sha256'] = hashlib.sha256(raw).hexdigest()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except ImportError:
        message = 'Native validation not executed: Pydantic 2 is required; see integrations/onlinequiz/requirements.txt'
    except (ValueError, OSError, TypeError, StopIteration) as exc:
        message = str(exc)
    print(json.dumps({'status': 'failed', 'error': message, 'imported': False}, ensure_ascii=False), file=sys.stderr)
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
