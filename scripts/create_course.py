"""Create a new course workspace with the complete original course skills."""
import argparse
import json
import re
import shutil
from pathlib import Path

SKILLS = ('textbook-lecture-notes', 'view-from-text', 'diagram-design',
          'assignment-design', 'assignment-grading', 'assignment-quiz',
          'slides-to-four-panel-comics')


def course_destination(template_root, course_id, destination=None, demo=False):
    """Require an explicit independent location for real courses."""
    source = Path(template_root).resolve()
    if destination is None:
        if demo:
            return source / 'workspace/courses' / course_id
        raise ValueError(
            '正式課程必須用 --destination 指定本專案之外的新目錄，例如 '
            f'"{source.parent / course_id}"；本專案內試跑請明確加 --demo。')
    return Path(destination).expanduser().resolve()


def check_destination(source, target, demo=False):
    if target.exists():
        raise ValueError('Destination already exists; no files were overwritten')
    if source == target or source.is_relative_to(target):
        raise ValueError('Destination cannot contain the template root')
    if demo:
        return
    if target.is_relative_to(source):
        raise ValueError('正式課程目錄必須在本專案之外；請選同層或其他獨立目錄。')
    for parent in target.parents:
        # Both .git directories and worktree/submodule .git files count.
        if (parent / '.git').exists():
            raise ValueError(f'目的地位於既有 Git 工作樹內：{parent}；請另選獨立目錄。')


def write_site_scaffold(source, target, name, site_url, demo):
    """Complete the inputs expected by the preserved upstream site builder."""
    config = (source / 'templates/course/mkdocs.yml').read_text(encoding='utf-8')
    config = config.replace('@@SITE_NAME@@', json.dumps(name, ensure_ascii=False))
    config = config.replace('@@SITE_URL@@', json.dumps(site_url))
    (target / 'mkdocs.yml').write_text(config, encoding='utf-8')
    pages = {
        'README.md': '# '+name+'\n\n課綱、正式時程與教材待教師確認。\n\n'
                     '- [課綱](syllabus.md)\n- [教學時程](schedule.md)\n'
                     '- [作業規範](assignments/README.md)\n',
        'FAQ.md': '# 常見問題\n\n待教師補充。\n',
        'glossary.md': '# 術語表\n\n依實際教材逐步補充。\n',
        'CHANGELOG.md': '# 異動紀錄\n\n新建課程骨架；尚未發布正式政策。\n',
        'CONTRIBUTING.md': '# 協作方式\n\n修改教材前先確認本課規範；個資與答案不入庫。\n',
        'LICENSE': '本課程新增內容的授權條款待教師指定。\n'
                   '內附上游工具及教學資源依 UPSTREAM_LICENSE 保留原授權；'
                   '本文件不替新增內容選定授權。\n',
    }
    for folder, title in (
        ('projects', '專題'), ('exams', '考試與測驗'), ('labs', '實驗'),
        ('notebooks', 'Notebook'), ('references', '參考資料'),
        ('study-guide', '自學指引'),
    ):
        (target / folder).mkdir(exist_ok=True)
        pages[folder+'/README.md'] = '# '+title+'\n\n尚無正式內容。\n'
    for relative, text in pages.items():
        (target / relative).write_text(text, encoding='utf-8')
    if not demo:
        shutil.copy2(source / 'templates/course/GITHUB_SETUP.md', target / 'GITHUB_SETUP.md')
        shutil.copytree(source / 'templates/course/workflows', target / '.github/workflows')


def create_course(template_root, destination, course_id, name, site_url, demo=False):
    source = Path(template_root).resolve()
    target = Path(destination).expanduser().resolve()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', course_id):
        raise ValueError('Course ID may contain letters, digits, underscores and hyphens')
    check_destination(source, target, demo)
    # All mutation below is confined to this new, explicitly selected directory.
    target.mkdir(parents=True, exist_ok=False)
    for slug in SKILLS:
        shutil.copytree(source / '.agents/skills' / slug, target / '.agents/skills' / slug,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for filename in ('LEVELS.md', 'NARRATIVE.md', 'INVENTORY_FORMAT.md'):
        shutil.copy2(source / '.agents/skills' / filename, target / '.agents/skills' / filename)
    support = source / 'course-support'
    shutil.copytree(support / 'scripts', target / 'scripts')
    shutil.copytree(support / 'slides', target / 'slides')
    for req in support.glob('requirements*.txt'):
        shutil.copy2(req, target / req.name)
    shutil.copy2(support / 'LICENSE', target / 'UPSTREAM_LICENSE')
    shutil.copy2(support / 'COURSE_AGENTS.portable.md', target / 'AGENTS.md')
    for name_ in ('lectures', 'assignments', 'assets/figures/src', 'references'):
        (target / name_).mkdir(parents=True, exist_ok=True)
    # Source policies are teacher references, outside the website content tree.
    (target / '.agents/references').mkdir(exist_ok=True)
    shutil.copy2(support / 'assignments/README.md', target / '.agents/references/upstream-assignment-guide.md')
    metadata = {'id': course_id, 'name': name, 'timezone': 'Asia/Taipei',
                'site_url': site_url, 'official_dates': 'not configured',
                'grading_policy': 'requires teacher approval', 'synthetic_demo': bool(demo)}
    (target / 'course.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    write_site_scaffold(source, target, name, site_url, demo)
    (target / 'COURSE_STATE.md').write_text('# 課程狀態\n\n新建工作區；尚無正式課程進度、期限或學生資料。\n',encoding='utf-8')
    (target / 'schedule.md').write_text('# 教學時程\n\n待教師提供；不以範例日期推定正式時程。\n',encoding='utf-8')
    (target / 'syllabus.md').write_text('# 課綱\n\n'+name+'\n\n程度、目標、評分與正式期限待教師確認。\n',encoding='utf-8')
    (target / 'assignments/README.md').write_text('# 作業規範\n\n正式規準由當前教師決定；本檔沒有預先核准的配分或截止日。\n每份作業使用 hwNN，繳交標籤 hwNN-submit；實際前綴與 Repo 規則依教師設定。\n教師評語、成績、測驗與答案只放私人目錄，不能寫入此工作樹。\n',encoding='utf-8')
    (target / '.gitignore').write_text('private/\ninstance/\nuploads/\n.env\n.env.*\n!.env.example\n__pycache__/\n*.pyc\n.venv/\n.site_src/\nsite/\n',encoding='utf-8')
    if demo:
        (target / 'lectures/lec01.md').write_text('# 示範講義（Demo lecture）\n\n> 程度：研究生（grad）／Level: Graduate (grad)\n\n此檔僅示範 Markdown 與 LaTeX：$L(w)=(w-3)^2$。\n\nThis file demonstrates Markdown and LaTeX only.\n',encoding='utf-8')
        shutil.copytree(source / 'examples/course-fixtures/hw01', target / 'assignments/hw01')
    return target


def main():
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--id', required=True)
    p.add_argument('--name', required=True)
    p.add_argument('--destination', type=Path, help='正式課程必填：專案外、非既有 Git 工作樹的新目錄')
    p.add_argument('--site-url', default='https://example.invalid/demo/')
    p.add_argument('--demo', action='store_true', help='僅供合成試跑；可放本專案 workspace，不建立課程 Repo')
    args=p.parse_args()
    root=Path(__file__).resolve().parent.parent
    try:
        destination=course_destination(root,args.id,args.destination,args.demo)
        result=create_course(root,destination,args.id,args.name,args.site_url,args.demo)
    except (OSError,ValueError) as e:
        p.exit(1,f'FAIL: {e}\n')
    print(json.dumps({'course_root':str(result),'original_skills':len(SKILLS),
                      'demo':args.demo,'external_changes':False,
                      'git_initialized':False,'github_repository_created':False,
                      'actions_verified':False,
                      'setup_guide':str(result/'GITHUB_SETUP.md') if not args.demo else None,
                      'next_steps':(['僅合成試跑；正式課程請另選專案外目錄。'] if args.demo else
                                    ['閱讀 GITHUB_SETUP.md，逐步建立獨立 Git 與 GitHub Repo。',
                                     '推送後核對 Course checks；Pages 另行設定及核准部署。'])},ensure_ascii=False))


if __name__=='__main__':
    main()
