"""Create a new course workspace with the complete original course skills."""
import argparse
import json
import re
import shutil
from pathlib import Path

SKILLS = ('textbook-lecture-notes', 'view-from-text', 'diagram-design',
          'assignment-design', 'assignment-grading', 'assignment-quiz',
          'slides-to-four-panel-comics')


def create_course(template_root, destination, course_id, name, site_url, demo=False):
    source = Path(template_root).resolve()
    target = Path(destination).resolve()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', course_id):
        raise ValueError('Course ID may contain letters, digits, underscores and hyphens')
    if target.exists():
        raise ValueError('Destination already exists; no files were overwritten')
    if source == target or source.is_relative_to(target):
        raise ValueError('Destination cannot contain the template root')
    # All mutation below is confined to this new, explicitly selected directory.
    target.mkdir(parents=True)
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
    shutil.copy2(support / 'assignments/README.md', target / 'references/upstream-assignment-guide.md')
    metadata = {'id': course_id, 'name': name, 'timezone': 'Asia/Taipei',
                'site_url': site_url, 'official_dates': 'not configured',
                'grading_policy': 'requires teacher approval', 'synthetic_demo': bool(demo)}
    (target / 'course.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (target / 'mkdocs.yml').write_text('site_name: '+json.dumps(name,ensure_ascii=False)+'\nsite_url: '+json.dumps(site_url)+'\n',encoding='utf-8')
    (target / 'COURSE_STATE.md').write_text('# 課程狀態\n\n新建工作區；尚無正式課程進度、期限或學生資料。\n',encoding='utf-8')
    (target / 'schedule.md').write_text('# 教學時程\n\n待教師提供；不以範例日期推定正式時程。\n',encoding='utf-8')
    (target / 'syllabus.md').write_text('# 課綱\n\n'+name+'\n\n程度、目標、評分與正式期限待教師確認。\n',encoding='utf-8')
    (target / 'assignments/README.md').write_text('# 作業規範\n\n正式規準由當前教師決定；本檔沒有預先核准的配分或截止日。\n每份作業使用 hwNN，繳交標籤 hwNN-submit；實際前綴與 Repo 規則依教師設定。\n教師評語、成績、測驗與答案只放私人目錄，不能寫入此工作樹。\n',encoding='utf-8')
    (target / 'lectures/lec01.md').write_text('# 示範講義（Demo lecture）\n\n> 程度：研究生（grad）／Level: Graduate (grad)\n\n此檔僅示範 Markdown 與 LaTeX：$L(w)=(w-3)^2$。\n\nThis file demonstrates Markdown and LaTeX only.\n',encoding='utf-8')
    (target / '.gitignore').write_text('private/\ninstance/\nuploads/\n.env\n__pycache__/\n*.pyc\n',encoding='utf-8')
    if demo:
        shutil.copytree(source / 'examples/course-fixtures/hw01', target / 'assignments/hw01')
    return target


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--id', required=True)
    p.add_argument('--name', required=True)
    p.add_argument('--destination', type=Path)
    p.add_argument('--site-url', default='https://example.invalid/demo/')
    p.add_argument('--demo', action='store_true', help='Include a clearly synthetic assignment')
    args=p.parse_args()
    root=Path(__file__).resolve().parent.parent
    destination=args.destination or root/'workspace/courses'/args.id
    try:
        result=create_course(root,destination,args.id,args.name,args.site_url,args.demo)
    except (OSError,ValueError) as e:
        p.exit(1,f'FAIL: {e}\n')
    print(json.dumps({'course_root':str(result),'original_skills':len(SKILLS),
                      'demo':args.demo,'external_changes':False},ensure_ascii=False))


if __name__=='__main__':
    main()
