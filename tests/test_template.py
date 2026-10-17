"""Verify setup preservation and failure cases without real accounts or services."""
import copy
import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"scripts/{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


doctor = load_module("doctor")
bootstrap = load_module("bootstrap")


class TemplateTests(unittest.TestCase):
    def setUp(self):
        base = (ROOT / "workspace/test-runs").resolve()
        base.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=base)
        # Confirm recursive cleanup stays inside this test-only workspace.
        assert Path(self.temp.name).resolve().is_relative_to(base)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "download"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(
            ".git", "workspace", "__pycache__", "project.local.json"))

    def test_clean_download_passes(self):
        errors, _ = doctor.audit(self.root, template=True)
        self.assertEqual(errors, [])

    def test_bootstrap_keeps_existing_user_settings(self):
        self.assertTrue(bootstrap.initialize(self.root, "My first project"))
        cfg = self.root / "config/project.local.json"
        data = json.loads(cfg.read_text(encoding="utf-8"))
        data["owner"]["display_name"] = "User-edited name"
        cfg.write_text(json.dumps(data), encoding="utf-8")
        before = cfg.read_bytes()
        self.assertFalse(bootstrap.initialize(self.root, "Replace attempt"))
        self.assertEqual(cfg.read_bytes(), before)

    def test_missing_skill_is_rejected(self):
        (self.root / ".agents/skills/textbook-lecture-notes/SKILL.md").unlink()
        errors, _ = doctor.audit(self.root, template=True)
        self.assertTrue(any("Missing skill" in e for e in errors))

    def test_modified_original_asset_is_rejected(self):
        path=self.root / '.agents/skills/assignment-design/build_labtube_import.py'
        path.write_bytes(path.read_bytes()+b'\n# unrecorded edit\n')
        errors,_=doctor.audit(self.root,template=True)
        self.assertTrue(any('Upstream byte mismatch' in e for e in errors))

    def test_alias_target_must_exist(self):
        path=self.root/'config/workflows.json'
        data=json.loads(path.read_text(encoding='utf-8'))
        data['aliases'][0]['target']='not-installed'
        path.write_text(json.dumps(data),encoding='utf-8')
        errors,_=doctor.audit(self.root,template=True)
        self.assertTrue(any('Invalid compatibility alias' in e for e in errors))

    def test_modified_onlinequiz_adaptation_is_rejected(self):
        path = self.root/'scripts/prepare_onlinequiz_bank.py'
        path.write_bytes(path.read_bytes() + b'\n# unrecorded change\n')
        errors, _ = doctor.audit(self.root, template=True)
        self.assertTrue(any('Unrecorded adaptation: scripts/prepare_onlinequiz_bank.py' in e for e in errors))

    def test_broken_relative_link_is_rejected(self):
        path = self.root / "README.md"
        with path.open("a", encoding="utf-8") as stream:
            stream.write("\n[missing](docs/not-there.md)\n")
        errors, _ = doctor.audit(self.root, template=True)
        self.assertTrue(any("Broken or escaping" in e for e in errors))

    def test_duplicate_workflow_is_rejected(self):
        path = self.root / "config/workflows.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["workflows"].append(copy.deepcopy(data["workflows"][0]))
        path.write_text(json.dumps(data), encoding="utf-8")
        errors, _ = doctor.audit(self.root, template=True)
        self.assertTrue(any("Duplicate workflow" in e for e in errors))

    def test_config_requires_external_write_confirmation(self):
        cfg = json.loads((self.root / "config/project.example.json").read_text(encoding="utf-8"))
        cfg["external_write_policy"] = "always"
        self.assertTrue(any("external_write_policy" in e for e in doctor.config_errors(cfg)))

    def test_malformed_config_is_reported(self):
        (self.root / "config/project.local.json").write_text("[]", encoding="utf-8")
        errors, _ = doctor.audit(self.root)
        self.assertTrue(any("Config must be" in e for e in errors))

    def test_private_output_inside_project_is_rejected(self):
        bootstrap.initialize(self.root)
        path = self.root / "config/project.local.json"
        cfg = json.loads(path.read_text(encoding="utf-8"))
        cfg["outputs"]["private_dir"] = str(self.root / "workspace/private")
        path.write_text(json.dumps(cfg), encoding="utf-8")
        errors, _ = doctor.audit(self.root)
        self.assertTrue(any("Private output is inside" in e for e in errors))

    def test_duplicate_course_id_is_rejected(self):
        cfg = json.loads((self.root / "config/project.example.json").read_text(encoding="utf-8"))
        course = dict(id="DEMO", name="Demo", repository="", branch="main", local_root="", state_file="COURSE_STATE.md", timezone="Asia/Taipei")
        cfg["courses"] = [course, dict(course)]
        self.assertTrue(any("duplicate course" in e for e in doctor.config_errors(cfg)))

    @unittest.skipUnless(shutil.which("git"), "git not installed")
    def test_gitignore_and_forced_sensitive_tracking(self):
        def git(*args):
            return subprocess.run(["git", "-C", str(self.root), *args],
                                  check=True, capture_output=True, text=True)
        git("init", "--initial-branch=main")
        bootstrap.initialize(self.root)
        result = git("check-ignore", "config/project.local.json", "workspace/public")
        self.assertIn("config/project.local.json", result.stdout)
        git("add", "--force", "config/project.local.json")
        errors, _ = doctor.audit(self.root, template=True)
        self.assertTrue(any("local-only path is tracked" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
