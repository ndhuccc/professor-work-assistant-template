"""Workflow loading and route failures, using real process documents and skills."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import doctor
import read_workflow


class WorkflowRouteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT/'workflows', self.root/'workflows')
        (self.root/'config').mkdir()
        (self.root/'docs').mkdir()
        self.manifest = json.loads((ROOT/'config/workflows.json').read_text(encoding='utf-8'))
        self.index = (ROOT/'docs/WORKFLOWS.md').read_text(encoding='utf-8')
        for item in self.manifest['workflows']:
            target = self.root/item['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT/item['path'], target)
        self.save()

    def save(self):
        (self.root/'config/workflows.json').write_text(json.dumps(self.manifest), encoding='utf-8')
        (self.root/'docs/WORKFLOWS.md').write_text(self.index, encoding='utf-8')

    def errors(self):
        return doctor.workflow_errors(self.root, self.manifest['workflows'], self.index)

    def test_all_ids_skills_and_aliases_load_complete_documents_in_order(self):
        self.assertEqual(self.errors(), [])
        selectors = [w['id'] for w in self.manifest['workflows']]
        selectors += [w['skill'] for w in self.manifest['workflows']]
        selectors += [a['skill'] for a in self.manifest['aliases']]
        self.assertEqual(len(set(w['workflow_path'] for w in self.manifest['workflows'])), 7)
        for selector in selectors:
            with self.subTest(selector=selector):
                loaded = read_workflow.load_workflow(ROOT, selector)
                item = next(w for w in self.manifest['workflows'] if w['id'] == loaded['workflow_id'])
                self.assertEqual(loaded['read_order'], [item['workflow_path'], item['path']])
                self.assertEqual(loaded['workflow_document']['content'], (ROOT/item['workflow_path']).read_text(encoding='utf-8'))
                self.assertEqual(loaded['skill_document']['content'], (ROOT/item['path']).read_text(encoding='utf-8'))
                self.assertFalse(loaded['executed'])

    def test_cli_alias_reads_both_bodies_without_executing_work(self):
        command = [sys.executable, str(ROOT/'scripts/read_workflow.py')]
        run = subprocess.run(command+['lecture-notes','--json'], capture_output=True, text=True, encoding='utf-8', check=True)
        result = json.loads(run.stdout)
        self.assertEqual(result['workflow_id'], 'W02')
        self.assertEqual(result['skill'], 'textbook-lecture-notes')
        self.assertIn('W02', result['workflow_document']['content'])
        self.assertIn('audit_lecture.py', result['skill_document']['content'])
        self.assertFalse(result['executed'])
        unknown = subprocess.run(command+['W99'], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(unknown.returncode, 2)

    def test_missing_route_path_is_rejected(self):
        del self.manifest['workflows'][0]['workflow_path']
        self.assertTrue(any('Invalid workflow path' in e for e in self.errors()))

    def test_missing_document_stops_reader(self):
        path = self.manifest['workflows'][0]['workflow_path']
        (self.root/path).unlink()
        self.assertTrue(any('Missing or unsafe workflow document' in e for e in self.errors()))
        with self.assertRaises(ValueError):
            read_workflow.load_workflow(self.root, 'W01')

    def test_escaping_document_path_is_rejected(self):
        self.manifest['workflows'][0]['workflow_path'] = '../outside.md'
        self.assertTrue(any('Invalid workflow path' in e for e in self.errors()))

    def test_document_must_identify_registered_route(self):
        path = self.root/self.manifest['workflows'][0]['workflow_path']
        path.write_text(path.read_text(encoding='utf-8').replace('W01','W99'), encoding='utf-8')
        self.assertTrue(any('lacks route id: W01' in e for e in self.errors()))

    def test_document_must_link_its_original_primary_skill(self):
        item = self.manifest['workflows'][0]
        path = self.root/item['workflow_path']
        original = '../'+item['path']
        path.write_text(path.read_text(encoding='utf-8').replace(original, '../AGENTS.md'), encoding='utf-8')
        self.assertTrue(any('lacks primary skill link: W01' in e for e in self.errors()))

    def test_catalog_must_link_every_referenced_document(self):
        self.index = self.index.replace('../workflows/research-review.md', '../AGENTS.md')
        self.assertTrue(any('catalog lacks document link: W10' in e for e in self.errors()))

    def test_orphan_document_is_reported(self):
        (self.root/'workflows/unregistered.md').write_text('# Unregistered workflow', encoding='utf-8')
        self.assertTrue(any('Unindexed workflow document' in e for e in self.errors()))


if __name__ == '__main__':
    unittest.main()
