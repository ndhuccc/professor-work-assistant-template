"""Synthetic fixtures; no live site, real exam questions, or database writes."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import prepare_onlinequiz_bank as prep
import validate_onlinequiz_bank as native


def demo_questions():
    return [dict(node='示意 (Demo)', question_type='Knowledge', format='Single Choice',
                 question='[測試題一 (Synthetic item one)]', options=['[甲 (Alpha)]', '[乙 (Beta)]'],
                 correct_answer='A', explanation='格式示意，並非正式教材或試題。'),
            dict(node='示意 (Demo)', question_type='Analysis', format='Multiple Choice',
                 question='[測試題二 (Synthetic item two)]', options=['[甲]', '[乙]', '[丙]'],
                 correct_answer='CA', explanation='合成格式測試；答案集合為甲與丙。')]


class OnlineQuizTests(unittest.TestCase):
    def test_array_preserves_positions_and_canonical_answer_set(self):
        source = demo_questions()
        before = copy.deepcopy(source)
        bank, warnings = prep.prepare(source, name='Synthetic-v1', seconds=150, expected_count=2)
        self.assertEqual(source, before)
        self.assertEqual(bank['questions'][1]['options'], ['甲', '乙', '丙'])
        self.assertEqual(bank['questions'][1]['correct_answer'], 'AC')
        self.assertEqual(bank['default_timer_seconds'], 150)
        self.assertEqual(warnings, [])

    def test_legacy_prefix_must_match_array_position(self):
        source = demo_questions()
        source[0]['options'] = ['[A. first]', '[B. second]']
        bank, _ = prep.prepare(source, name='Legacy')
        self.assertEqual(bank['questions'][0]['options'], ['first', 'second'])
        source[0]['options'].reverse()
        with self.assertRaisesRegex(ValueError, 'mismatches position'):
            prep.prepare(source, name='Bad')

    def test_bad_answer_sets_are_rejected(self):
        for answer in ('C', 'AA', 'a', 'A,C', 'AB'):
            with self.subTest(answer=answer):
                source = demo_questions()
                source[0]['correct_answer'] = answer
                with self.assertRaises(ValueError):
                    prep.prepare(source, name='Bad')

    def test_dropped_metadata_or_per_question_policy_is_rejected(self):
        for field in ('points', 'timer_seconds', 'quality_report'):
            source = demo_questions()
            source[0][field] = 5
            with self.assertRaisesRegex(ValueError, 'unsupported fields'):
                prep.prepare(source, name='Bad')

    def test_duplicates_count_and_typed_policy_are_rejected(self):
        source = demo_questions()
        source[1]['question'] = source[0]['question']
        with self.assertRaisesRegex(ValueError, 'duplicate normalized'):
            prep.prepare(source, name='Bad')
        with self.assertRaisesRegex(ValueError, 'differs from expected'):
            prep.prepare(demo_questions(), name='Bad', expected_count=3)
        for args in ({'seconds': True}, {'points': float('nan')}, {'points': float('inf')}, {'seconds': 4}):
            with self.assertRaises(ValueError):
                prep.prepare(demo_questions(), name='Bad', **args)

    def test_position_dependent_items_require_review(self):
        source = demo_questions()
        source[0]['options'][1] = '以上皆是 (All of the above)'
        _, warnings = prep.prepare(source, name='Review')
        self.assertTrue(any('shuffled delivery' in w for w in warnings))

    def test_cli_sha_utf8_not_imported_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            src, out = p/'input.json', p/'bank.json'
            src.write_text(json.dumps(demo_questions(), ensure_ascii=False), encoding='utf-8')
            cmd = [sys.executable, '-X', 'utf8', str(ROOT/'scripts/prepare_onlinequiz_bank.py'), str(src), '--name', 'Synthetic-v1', '--seconds', '150', '--expected-count', '2', '--output', str(out)]
            run = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', check=True)
            report = json.loads(run.stdout)
            before = out.read_bytes()
            self.assertEqual(report['output_sha256'], hashlib.sha256(before).hexdigest())
            self.assertFalse(report['imported'])
            self.assertIn('測試題一', before.decode())
            if importlib.util.find_spec('pydantic'):
                checked = subprocess.run([sys.executable, '-X', 'utf8', str(ROOT/'scripts/validate_onlinequiz_bank.py'), str(out), '--expected-count', '2'], capture_output=True, text=True, encoding='utf-8', check=True)
                native_report = json.loads(checked.stdout)
                self.assertFalse(native_report['imported'])
                self.assertEqual(native_report['input_sha256'], report['output_sha256'])
            again = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(again.returncode, 2)
            self.assertEqual(out.read_bytes(), before)

    def test_cli_rejects_duplicate_keys_without_creating_output(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            (p/'bad.json').write_text('{"name":"a","name":"b"}', encoding='utf-8')
            run = subprocess.run([sys.executable, str(ROOT/'scripts/prepare_onlinequiz_bank.py'), str(p/'bad.json'), '--output', str(p/'out.json')], capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertFalse((p/'out.json').exists())

    @unittest.skipUnless(importlib.util.find_spec('pydantic'), 'Optional Pydantic unavailable')
    def test_original_schema_and_row_functions_accept_prepared_bank(self):
        bank, _ = prep.prepare(demo_questions(), name='Synthetic-v1', seconds=150)
        report = native.validate(bank, expected_count=2)
        self.assertEqual(report['status'], 'pinned_native_format_valid')
        self.assertEqual(report['question_count'], 2)
        self.assertFalse(report['imported'])
        schema, row_check = native.load_validators()
        bank['questions'][0]['correct_answer'] = 'J'
        model = schema.model_validate(bank)
        with self.assertRaisesRegex(ValueError, '不存在'):
            row_check(model.questions[0])

    def test_source_package_and_native_assets_match_recorded_blobs(self):
        manifest = json.loads((ROOT/'config/source-bundle.json').read_text())
        items = [x for x in manifest['files'] if x['source_repository'] in ('ndhuccc/OnlineQuiz-v2', 'ndhuccc/claude-skills-pipelines')]
        self.assertEqual(len(items), 6)
        for item in items:
            raw = (ROOT/item.get('preserved_source', item['destination'])).read_bytes()
            digest = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            self.assertEqual(digest, item['source_blob_sha'])
        package = ROOT/'integrations/onlinequiz/source-package'
        self.assertEqual(len([p for p in package.rglob('*') if p.is_file()]), 8)
        self.assertEqual((ROOT/'scripts/prepare_onlinequiz_bank.py').read_bytes(), (package/'scripts/prepare_onlinequiz_bank.py').read_bytes())


if __name__ == '__main__':
    unittest.main()
