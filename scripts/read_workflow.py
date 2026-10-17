"""Read the selected workflow and its original primary skill; execute nothing."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from doctor import workflow_errors

ROOT = Path(__file__).resolve().parents[1]


def load_workflow(root: Path, selector: str) -> dict:
    root = Path(root).resolve()
    manifest = json.loads((root / 'config/workflows.json').read_text(encoding='utf-8'))
    if not isinstance(manifest, dict) or not isinstance(manifest.get('workflows'), list):
        raise ValueError('Invalid workflow manifest')
    entries = manifest['workflows']
    errors = workflow_errors(root, entries, (root / 'docs/WORKFLOWS.md').read_text(encoding='utf-8'))
    if errors:
        raise ValueError('; '.join(errors))
    aliases = {a['skill']: a['target'] for a in manifest.get('aliases', [])}
    canonical = aliases.get(selector, selector)
    selected = [x for x in entries if x.get('id') == canonical or x.get('skill') == canonical]
    if len(selected) != 1:
        raise ValueError(f'Unknown or ambiguous workflow: {selector}')
    entry = selected[0]
    skill_path = f".agents/skills/{entry['skill']}/SKILL.md"
    if entry.get('path') != skill_path:
        raise ValueError('Primary skill path disagrees with manifest')
    skill = root / skill_path
    if not skill.is_file() or skill.is_symlink() or not skill.resolve().is_relative_to(root / '.agents/skills'):
        raise ValueError('Missing or unsafe primary skill')
    return {'requested': selector, 'workflow_id': entry['id'], 'skill': entry['skill'],
            'template_version': manifest['template_version'],
            'read_order': [entry['workflow_path'], skill_path],
            'workflow_document': {'path': entry['workflow_path'], 'content': (root / entry['workflow_path']).read_text(encoding='utf-8')},
            'skill_document': {'path': skill_path, 'content': skill.read_text(encoding='utf-8')},
            'executed': False}


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('selector', help='Workflow ID, canonical skill name, or compatibility alias')
    parser.add_argument('--json', action='store_true', help='Include both complete documents in structured output')
    args = parser.parse_args()
    try:
        result = load_workflow(ROOT, args.selector)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"# 已讀入 {result['workflow_id']}：{result['skill']}")
        print('先依根目錄 AGENTS.md，再依下列 workflow 與原技能執行；歷史授權不代表本次授權。')
        for key in ('workflow_document', 'skill_document'):
            doc = result[key]
            print(f"\n---\n# {doc['path']}\n\n{doc['content']}")
        print('\n---\n已讀入兩份完整文件；請按流程繼續讀必要參考資料。此工具未執行工作、未連線或寫入外部服務。')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
