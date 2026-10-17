"""Independent real-course destinations and runnable GitHub setup artifacts."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import create_course as creator


class CourseSetupTests(unittest.TestCase):
    def setUp(self):
        # Use system temp, outside the checkout, to exercise real repo boundaries.
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()

    def command(self, *args, cwd=None):
        env = dict(os.environ, PYTHONUTF8='1')
        return subprocess.run(list(map(str, args)), cwd=cwd, env=env,
                              capture_output=True, text=True, encoding='utf-8', timeout=60)

    def make_course(self, slug='course'):
        return creator.create_course(ROOT, self.base/slug, 'DEMO', '獨立課程: 測試',
                                     'https://example.invalid/course/')

    def test_formal_cli_requires_destination_and_creates_nothing(self):
        run = self.command(sys.executable, ROOT/'scripts/create_course.py',
                           '--id', 'MISSING-DEST', '--name', 'Test')
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('--destination', run.stderr)
        self.assertFalse((ROOT/'workspace/courses/MISSING-DEST').exists())

    def test_only_demo_has_an_internal_default(self):
        with self.assertRaisesRegex(ValueError, '--destination'):
            creator.course_destination(ROOT, 'DEMO')
        self.assertEqual(creator.course_destination(ROOT, 'DEMO', demo=True),
                         ROOT/'workspace/courses/DEMO')

    def test_formal_course_is_rejected_inside_zip_template_before_mutation(self):
        source = self.base/'zip-template'
        source.mkdir()
        destination = source/'workspace/course'
        with self.assertRaisesRegex(ValueError, '本專案之外'):
            creator.create_course(source, destination, 'DEMO', 'Demo', '')
        self.assertFalse(destination.exists())

    def test_other_git_tree_directory_and_worktree_file_are_rejected(self):
        for kind in ('directory', 'file'):
            with self.subTest(kind=kind):
                repo = self.base/kind
                repo.mkdir()
                marker = repo/'.git'
                if kind == 'directory':
                    marker.mkdir()
                else:
                    marker.write_text('gitdir: elsewhere\n', encoding='utf-8')
                target = repo/'nested'/'course'
                with self.assertRaisesRegex(ValueError, 'Git 工作樹'):
                    creator.create_course(ROOT, target, 'DEMO', 'Demo', '')
                self.assertFalse((repo/'nested').exists())

    def test_symlink_cannot_bypass_template_boundary(self):
        link = self.base/'template-link'
        try:
            link.symlink_to(ROOT, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('Directory symlinks unavailable')
        with self.assertRaisesRegex(ValueError, '本專案之外'):
            creator.create_course(ROOT, link/'forbidden-course', 'DEMO', 'Demo', '')

    def test_cli_external_course_has_workflows_and_truthful_next_steps(self):
        target = self.base/'external-course'
        run = self.command(sys.executable, ROOT/'scripts/create_course.py', '--id', 'DEMO',
                           '--name', '獨立課程', '--destination', target)
        self.assertEqual(run.returncode, 0, run.stderr)
        report = json.loads(run.stdout)
        self.assertEqual(Path(report['course_root']), target)
        self.assertFalse(report['git_initialized'])
        self.assertFalse(report['github_repository_created'])
        self.assertFalse(report['actions_verified'])
        self.assertEqual(Path(report['setup_guide']), target/'GITHUB_SETUP.md')
        self.assertFalse((target/'.git').exists())
        self.assertFalse((target/'lectures/lec01.md').exists())
        for name in ('check-course.yml', 'deploy-site.yml'):
            self.assertTrue((target/'.github/workflows'/name).is_file())

    def test_workflows_keep_checks_and_deployment_separate(self):
        if not importlib.util.find_spec('yaml'):
            self.skipTest('Optional PyYAML unavailable')
        import yaml
        target = self.make_course()
        checks = yaml.safe_load((target/'.github/workflows/check-course.yml').read_text())
        deploy = yaml.safe_load((target/'.github/workflows/deploy-site.yml').read_text())
        self.assertIn('push', checks['on'])
        self.assertIn('pull_request', checks['on'])
        self.assertEqual(checks['permissions'], {'contents': 'read'})
        self.assertEqual(set(deploy['on']), {'workflow_dispatch'})
        self.assertEqual(deploy['jobs']['deploy']['needs'], 'build')
        self.assertEqual(deploy['jobs']['deploy']['permissions'],
                         {'pages': 'write', 'id-token': 'write'})
        build = deploy['jobs']['build']['steps']
        upload = next(s for s in build if s.get('uses', '').startswith('actions/upload-pages-artifact@'))
        self.assertEqual(upload['with']['path'], 'site')

    @unittest.skipUnless(shutil.which('git'), 'Git unavailable')
    def test_generated_course_can_be_its_own_git_root(self):
        target = self.make_course()
        run = self.command('git', '-C', target, 'init', '--initial-branch=main')
        self.assertEqual(run.returncode, 0, run.stderr)
        top = self.command('git', '-C', target, 'rev-parse', '--show-toplevel')
        self.assertEqual(Path(top.stdout.strip()).resolve(), target)
        for relative in ('site/index.html', '.site_src/index.md', '.venv/test'):
            ignored = self.command('git', '-C', target, 'check-ignore', relative)
            self.assertEqual(ignored.returncode, 0, relative)
        # Exercise the guide's actual staging list, including hidden workflows.
        guide = (target/'GITHUB_SETUP.md').read_text(encoding='utf-8')
        command = next(line for line in guide.splitlines() if line.startswith('git add -- '))
        staged = self.command(*shlex.split(command), cwd=target)
        self.assertEqual(staged.returncode, 0, staged.stderr)
        tracked = self.command('git', '-C', target, 'ls-files').stdout.splitlines()
        self.assertIn('.github/workflows/check-course.yml', tracked)
        self.assertIn('.github/workflows/deploy-site.yml', tracked)
        self.assertIn('GITHUB_SETUP.md', tracked)

    @unittest.skipUnless(sys.version_info >= (3, 11) and importlib.util.find_spec('mkdocs')
                         and importlib.util.find_spec('material')
                         and importlib.util.find_spec('pymdownx'), 'Site dependencies unavailable')
    def test_new_formal_course_builds_with_preserved_tools(self):
        target = self.make_course()
        for args in ((sys.executable, target/'scripts/check_slides.py'),
                     (sys.executable, target/'scripts/build_docs.py'),
                     (sys.executable, '-m', 'mkdocs', 'build', '--strict')):
            result = self.command(*args, cwd=target)
            self.assertEqual(result.returncode, 0, result.stdout+'\n'+result.stderr)
        self.assertTrue((target/'site/index.html').is_file())
        self.assertFalse((target/'.site_src/.agents').exists())
        self.assertFalse((target/'.site_src/GITHUB_SETUP.md').exists())
        self.assertFalse((target/'.site_src/references/upstream-assignment-guide.md').exists())


if __name__ == '__main__':
    unittest.main()
