"""Offline structural checks. Does not authenticate, publish, or render artifacts."""
import argparse
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

REQUIRED = (
    "AGENTS.md", "README.md", "docs/WORKFLOWS.md", "docs/SETUP.md",
    "docs/CAPABILITIES.md", "docs/QUALITY.md", "docs/PRIVACY.md",
    "docs/PUBLISHING.md", "docs/PROVENANCE.md", "config/workflows.json",
    "config/project.example.json", "templates/task-record.md",
    "templates/course-state.md", "templates/validation-report.md",
    "examples/demo-source.md", "examples/START-HERE.md",
    "scripts/bootstrap.py", "scripts/doctor.py", ".gitignore", ".gitattributes",
    "scripts/create_course.py", "scripts/verify_bundle.py", "scripts/validate_labtube.py",
    "config/source-bundle.json", "docs/PORTABILITY.md", "THIRD_PARTY_NOTICES.md",
    "scripts/prepare_onlinequiz_bank.py", "scripts/validate_onlinequiz_bank.py",
    "workflows/onlinequiz-question-bank.md", "integrations/onlinequiz/README.md",
    "docs/ONLINEQUIZ-INTEGRATION.md",
    "scripts/read_workflow.py",
    "docs/NEW-COURSE.md", "templates/course/GITHUB_SETUP.md",
    "templates/course/mkdocs.yml", "templates/course/workflows/check-course.yml",
    "templates/course/workflows/deploy-site.yml",
)
ALLOWED_INTEGRATIONS = {"available", "unavailable", "unverified"}


def config_errors(data: object) -> list[str]:
    errors = []
    if not isinstance(data, dict):
        return ["Config must be a JSON object"]
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    for key in ("project_name", "locale", "timezone"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            errors.append(f"{key} must be a nonempty string")
    if data.get("external_write_policy") != "confirm-concrete-change":
        errors.append("external_write_policy must be confirm-concrete-change")
    outputs = data.get("outputs")
    if not isinstance(outputs, dict):
        errors.append("outputs must be an object")
    else:
        if not isinstance(outputs.get("public_dir"), str) or not outputs["public_dir"]:
            errors.append("outputs.public_dir must be a nonempty string")
        if not isinstance(outputs.get("private_dir"), str):
            errors.append("outputs.private_dir must be a string; empty is allowed")
    courses = data.get("courses")
    if not isinstance(courses, list):
        errors.append("courses must be an array")
    else:
        ids = set()
        for index, course in enumerate(courses):
            if not isinstance(course, dict):
                errors.append(f"courses[{index}] must be an object")
                continue
            cid = course.get("id")
            if not isinstance(cid, str) or not cid.strip():
                errors.append(f"courses[{index}].id must be a nonempty string")
            elif cid in ids:
                errors.append(f"duplicate course id: {cid}")
            else:
                ids.add(cid)
            for key in ("name", "repository", "branch", "local_root", "state_file", "timezone"):
                if not isinstance(course.get(key), str):
                    errors.append(f"courses[{index}].{key} must be a string")
            repo = course.get("repository")
            if repo and (not isinstance(repo, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo)):
                errors.append(f"courses[{index}].repository must be owner/repo or empty")
    integrations = data.get("integrations")
    if not isinstance(integrations, dict) or not all(isinstance(v, str) and v in ALLOWED_INTEGRATIONS for v in integrations.values()):
        errors.append("integrations values must be available, unavailable, or unverified")
    logging = data.get("logging")
    if not isinstance(logging, dict) or logging.get("backend") not in ("local", "external"):
        errors.append("logging.backend must be local or external")
    elif not isinstance(logging.get("external_destination"), str):
        errors.append("logging.external_destination must be a string")
    elif logging["backend"] == "external" and not logging["external_destination"].strip():
        errors.append("external logging requires an explicit destination")
    return errors


def run_git(path: Path, *args: str) -> subprocess.CompletedProcess | None:
    if not shutil.which("git"):
        return None
    try:
        return subprocess.run(["git", "-C", str(path), *args], capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None


def tracked_paths(root: Path) -> set[str]:
    result = run_git(root, "ls-files", "-z", "--", ".")
    return set(result.stdout.split("\0")) - {""} if result and result.returncode == 0 else set()


def markdown_links(text: str) -> list[str]:
    # Strip fenced and inline code so illustrative paths do not become links.
    clean = re.sub(r"```.*?```", "", text, flags=re.S)
    clean = re.sub(r"`[^`\n]+`", "", clean)
    return re.findall(r"!?\[[^\]\n]*\]\(([^\s)]+)\)", clean)


def workflow_errors(root: Path, entries: list, index_text: str) -> list[str]:
    """Check every route's process document, primary skill and catalog link."""
    root = Path(root).resolve()
    errors, registered = [], set()
    index_links = set(markdown_links(index_text))
    for entry in entries:
        if not isinstance(entry, dict):
            continue  # The manifest validator reports malformed entries.
        wid, slug, rel = entry.get('id'), entry.get('skill'), entry.get('workflow_path')
        if not isinstance(rel, str) or not re.fullmatch(r'workflows/[a-z0-9]+(?:-[a-z0-9]+)*\.md', rel):
            errors.append(f'Invalid workflow path: {wid}: {rel}')
            continue
        registered.add(rel)
        target = root / rel
        if not target.is_file() or target.is_symlink() or not target.resolve().is_relative_to(root / 'workflows'):
            errors.append(f'Missing or unsafe workflow document: {wid}: {rel}')
            continue
        body = target.read_text(encoding='utf-8')
        if not isinstance(wid, str) or not re.search(r'(?<![A-Z0-9])' + re.escape(wid) + r'(?![A-Z0-9])', body):
            errors.append(f'Workflow document lacks route id: {wid}: {rel}')
        expected = f'../.agents/skills/{slug}/SKILL.md'
        if expected not in markdown_links(body):
            errors.append(f'Workflow document lacks primary skill link: {wid}: {rel}')
        if '../' + rel not in index_links:
            errors.append(f'Workflow catalog lacks document link: {wid}: {rel}')
    actual = {p.relative_to(root).as_posix() for p in (root / 'workflows').glob('*.md') if p.is_file()}
    for path in sorted(actual - registered):
        errors.append('Unindexed workflow document: ' + path)
    return errors


def audit(root: Path, template: bool = False) -> tuple[list[str], list[str]]:
    root = root.resolve()
    errors, warnings = [], []
    for rel in REQUIRED:
        if not (root / rel).is_file():
            errors.append(f"Missing required file: {rel}")
    manifest_path = root / "config/workflows.json"
    manifest = {}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict) or not isinstance(manifest.get("workflows"), list):
            raise ValueError("workflows must be an array")
    except (OSError, ValueError) as exc:
        errors.append(f"Invalid workflow manifest: {exc}")
    entries = manifest.get("workflows", []) if isinstance(manifest, dict) else []
    if not entries:
        errors.append("No workflows registered")
    seen_ids, seen_skills, registered = set(), set(), set()
    index_text = (root / "docs/WORKFLOWS.md").read_text(encoding="utf-8") if (root / "docs/WORKFLOWS.md").exists() else ""
    for item in entries:
        if not isinstance(item, dict):
            errors.append("Workflow must be an object")
            continue
        wid, slug, rel = item.get("id"), item.get("skill"), item.get("path")
        if not isinstance(wid, str) or not re.fullmatch(r"W\d{2}", wid):
            errors.append(f"Invalid workflow id: {wid}")
        if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            errors.append(f"Invalid skill name: {slug}")
        if wid in seen_ids or slug in seen_skills:
            errors.append(f"Duplicate workflow id or skill: {wid}/{slug}")
        seen_ids.add(wid)
        seen_skills.add(slug)
        expected = f".agents/skills/{slug}/SKILL.md"
        if rel != expected:
            errors.append(f"Unexpected skill path: {rel}; expected {expected}")
            continue
        registered.add(rel)
        target = root / rel
        if not target.is_file() or target.is_symlink():
            errors.append(f"Missing skill or unsupported symlink: {rel}")
            continue
        body = target.read_text(encoding="utf-8")
        front = re.match(r"\A---\n(.*?)\n---\n", body, re.S)
        if not front:
            errors.append(f"Invalid skill frontmatter: {rel}")
        else:
            fields = {}
            for line in front.group(1).splitlines():
                key, sep, value = line.partition(":")
                if not sep:
                    errors.append(f"Invalid frontmatter field: {rel}")
                fields[key.strip()] = value.strip()
            if set(fields) != {"name", "description"} or fields.get("name") != slug or not fields.get("description"):
                errors.append(f"Invalid skill metadata: {rel}")
        if ("TODO" in body or len(body.splitlines()) > 500) and not (root / "vendor/original-entries" / slug / "SOURCE.md").exists():
            errors.append(f"Unfinished or overlong skill: {rel}")
        if f"| {wid} |" not in index_text or slug not in index_text:
            errors.append(f"Workflow index out of sync: {wid}")
        if not (target.parent / "agents/openai.yaml").is_file():
            errors.append(f"Missing agent UI metadata: {slug}")
    errors.extend(workflow_errors(root, entries, index_text))
    for alias in manifest.get("aliases", []):
        slug, target, rel = alias.get("skill"), alias.get("target"), alias.get("path")
        expected = f".agents/skills/{slug}/SKILL.md"
        if target not in seen_skills or slug in seen_skills or rel != expected or not (root/expected).is_file():
            errors.append(f"Invalid compatibility alias: {slug}")
        else:
            registered.add(rel)
    actual = {p.relative_to(root).as_posix() for p in (root / ".agents/skills").glob("*/SKILL.md")}
    if actual != registered:
        errors.append("Registered workflows and skill directories differ")
    for path in root.rglob("*.md"):
        rel = path.relative_to(root)
        if any(part in {".git", "workspace", "inputs", "outputs", "private", "vendor", "course-support", "integrations", "profiles"} for part in rel.parts):
            continue
        # Full upstream examples contain documented external/optional links. Their
        # bytes and local presence are checked by verify_bundle, not rewritten here.
        if rel.parts[:2] == (".agents", "skills") and len(rel.parts)>3:
            if rel.parts[2] in {"diagram-design", "view-from-text", "textbook-lecture-notes", "assignment-design", "assignment-grading", "assignment-quiz", "slides-to-four-panel-comics"}:
                continue
        body = path.read_text(encoding="utf-8")
        if re.search(r"skill://(?:user|plugin)[^\s)]*|C:\\\\Users\\\\|libfile_[a-f0-9]+", body):
            errors.append(f"Nonportable private resource reference: {rel}")
        for link in markdown_links(body):
            parsed = urlsplit(link)
            if parsed.scheme or not parsed.path:
                continue
            dest = (path.parent / unquote(parsed.path)).resolve()
            if not dest.is_relative_to(root) or not dest.exists():
                errors.append(f"Broken or escaping Markdown link: {rel} -> {link}")
    for rel in ("config/project.example.json", "config/project.local.json"):
        path = root / rel
        if not path.exists():
            if rel.endswith("local.json") and not template:
                warnings.append("Local config absent: run python scripts/bootstrap.py")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            errors.extend(f"{rel}: {e}" for e in config_errors(data))
            if not template and rel.endswith("local.json"):
                if not data.get("courses"):
                    warnings.append("No course configured; local source tasks remain available")
                private = data.get("outputs", {}).get("private_dir", "")
                if not private:
                    warnings.append("Private output not configured; required before sensitive review")
                else:
                    private_path = Path(private).expanduser()
                    if not private_path.is_absolute():
                        errors.append("Private output must be an absolute path")
                    else:
                        resolved = private_path.resolve()
                        known_roots = [root]
                        for course in data.get("courses", []):
                            course_root = course.get("local_root", "")
                            if course_root:
                                cp = Path(course_root).expanduser()
                                known_roots.append((cp if cp.is_absolute() else root / cp).resolve())
                        if any(resolved.is_relative_to(base) for base in known_roots):
                            errors.append("Private output is inside a known project/course tree")
                        for parent in (resolved, *resolved.parents):
                            if (parent / ".git").exists():
                                errors.append("Private output is inside a Git working tree")
                                break
                        warnings.append("Private destination still needs user approval and access/privacy verification")
                tz = data.get("timezone")
                if isinstance(tz, str):
                    try:
                        ZoneInfo(tz)
                    except ZoneInfoNotFoundError:
                        warnings.append(f"Timezone unavailable locally: {tz}; verify on agent platform")
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            errors.append(f"Invalid config {rel}: {exc}")
    tracked = tracked_paths(root)
    for rel in tracked:
        p = Path(rel)
        if rel == "config/project.local.json" or (p.parts and p.parts[0] in {"workspace", "inputs", "outputs", "private"}) or p.name.startswith(".env") or p.suffix in {".pem", ".key"}:
            errors.append(f"Sensitive/local-only path is tracked: {rel}")
    if not (root / "LICENSE").exists():
        warnings.append("LICENSE not selected; choose terms before distribution")
    bundle_checker=root/"scripts/verify_bundle.py"
    if bundle_checker.is_file():
        try:
            spec=importlib.util.spec_from_file_location("bundle_check",bundle_checker)
            module=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            bundle_errors,_=module.verify(root)
            errors.extend(bundle_errors)
        except (OSError,ValueError,KeyError) as exc:
            errors.append(f"Cannot verify original source bundle: {exc}")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", action="store_true", help="Validate distributable template; local setup is optional")
    parser.add_argument("--capabilities", action="store_true", help="Report local optional modules; never authenticate or install")
    args = parser.parse_args()
    if sys.version_info < (3, 10):
        print("FAIL: Python 3.10 or newer required")
        return 1
    errors, warnings = audit(Path(__file__).resolve().parent.parent, args.template)
    if args.capabilities:
        for name in ('PIL','numpy','matplotlib','yaml','pypdf','playwright','pydantic'):
            print(f"MODULE {name}: " + ('available' if importlib.util.find_spec(name) else 'not installed'))
        if sys.version_info < (3,11):
            warnings.append('Python 3.11+ is needed by original semester/site utilities using tomllib')
    for item in errors:
        print(f"FAIL: {item}")
    for item in warnings:
        print(f"WARN: {item}")
    if not errors:
        print("PASS: offline structure, references, manifest, and config checks")
    print("NOT TESTED: external authentication, rendering, grading correctness, publishing")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
