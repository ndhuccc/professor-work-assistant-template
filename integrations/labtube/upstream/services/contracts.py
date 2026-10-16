"""JSON contracts exchanged with the teacher's machine (see LabTube-實作計畫書.md §5).

Every validator returns ``(parsed, errors)``; **any** error means the whole file must be refused (all-or-nothing).
The server never accepts answer keys or multiple-choice options in a quiz file.
"""
import re

QUIZ_SCHEMA = 'labtube.quiz.v1'
ANSWERS_SCHEMA = 'labtube.answers.v1'
GRADES_SCHEMA = 'labtube.grades.v1'
RUBRIC_SCHEMA = 'labtube.rubric.v1'
ASSIGNMENTS_SCHEMA = 'labtube.assignments.v1'
REPOCHECK_SCHEMA = 'labtube.repocheck.v1'

QTYPES = ['explain', 'change', 'reason']
MAX_PROMPT = 60
MAX_SNIPPET_LINES = 8
MAX_LINE = 48
MAX_ANSWER = 50
MAX_RATIONALE = 300
MAX_FLAGS = 10
SHA_RE = re.compile(r'^[0-9a-f]{7,40}$')
CODE_RE = re.compile(r'^hw\d{2}$')

FORBIDDEN_QUIZ_KEYS = {'answer', 'answers', 'answers_key', 'key', 'reference', 'reference_answer', 'correct',
                       'options', 'choices', 'solution', 'rubric_points', 'key_points'}


def _walk_keys(obj, path=''):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield f'{path}/{k}', k
            yield from _walk_keys(v, f'{path}/{k}')
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk_keys(v, f'{path}[{i}]')


def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


# --------------------------------------------------------------------------- quiz questions
def validate_quiz(data, assignment_code, known_student_ids=None):
    """Returns ({student_id: [question dicts]}, errors, warnings)."""
    errors, warnings, parsed = [], [], {}
    if not isinstance(data, dict):
        return parsed, ['檔案根層必須是物件'], warnings
    if data.get('schema') != QUIZ_SCHEMA:
        errors.append(f'schema 必須是 {QUIZ_SCHEMA}')
    if data.get('assignment') != assignment_code:
        errors.append(f'assignment 必須是 {assignment_code}(檔案內為 {data.get("assignment")!r})')
    for path, key in _walk_keys(data):
        if key.lower() in FORBIDDEN_QUIZ_KEYS:
            errors.append(f'{path}:禁止的欄位(答案或選項不可進入伺服器)')
    students = data.get('students')
    if not isinstance(students, list) or not students:
        errors.append('students 必須是非空陣列')
        return parsed, errors, warnings
    for s in students:
        sid = s.get('student_id') if isinstance(s, dict) else None
        if not isinstance(sid, str) or not sid:
            errors.append('有學生項目缺少 student_id')
            continue
        if sid in parsed:
            errors.append(f'{sid}:學號重複')
            continue
        if known_student_ids is not None and sid not in known_student_ids:
            errors.append(f'{sid}:不在此課程(未註冊、未加入或不在名單)')
            continue
        qs = s.get('questions')
        if not isinstance(qs, list) or [q.get('idx') if isinstance(q, dict) else None for q in qs] != [1, 2, 3]:
            errors.append(f'{sid}:必須恰有 3 題且 idx 依序為 1、2、3')
            continue
        clean = []
        for q in qs:
            tag = f'{sid} Q{q["idx"]}'
            if q.get('qtype') != QTYPES[q['idx'] - 1]:
                errors.append(f'{tag}:qtype 應為 {QTYPES[q["idx"] - 1]}')
            prompt = q.get('prompt')
            if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > MAX_PROMPT:
                errors.append(f'{tag}:prompt 需為 1–{MAX_PROMPT} 字')
            elif len(prompt) > 40:
                warnings.append(f'{tag}:prompt 超過 40 字(目前 {len(prompt)})')
            snippet = q.get('snippet')
            if not isinstance(snippet, str) or not snippet.strip():
                errors.append(f'{tag}:缺少 snippet')
            else:
                lines = snippet.split('\n')
                if len(lines) > MAX_SNIPPET_LINES:
                    errors.append(f'{tag}:snippet 超過 {MAX_SNIPPET_LINES} 行(目前 {len(lines)})')
                for i, ln in enumerate(lines, 1):
                    if len(ln) > MAX_LINE:
                        errors.append(f'{tag}:snippet 第 {i} 行超過 {MAX_LINE} 字元(目前 {len(ln)})')
                        break
            source = q.get('snippet_source')
            if not isinstance(source, str) or not source.strip():
                errors.append(f'{tag}:缺少 snippet_source')
            clean.append({'idx': q['idx'], 'qtype': q.get('qtype'), 'prompt': prompt, 'snippet': snippet,
                          'snippet_source': (source or '')[:200]})
        parsed[sid] = clean
    return parsed, errors, warnings


# --------------------------------------------------------------------------- answers export
def validate_answers_doc(doc):
    """Sanity check of our own export (also used by tests and the teacher-side tools)."""
    errors = []
    if doc.get('schema') != ANSWERS_SCHEMA:
        errors.append(f'schema 必須是 {ANSWERS_SCHEMA}')
    if 'notice' not in doc:
        errors.append('缺少 notice(資料免責聲明)')
    for path, key in _walk_keys(doc):
        if key.lower() in {'name', 'email', 'student_name'}:
            errors.append(f'{path}:匯出檔不得含姓名或 Email')
    for a in doc.get('attempts', []):
        for ans in a.get('answers', []):
            if len(ans.get('text') or '') > MAX_ANSWER:
                errors.append(f'{a.get("student_id")} Q{ans.get("idx")}:作答超過 {MAX_ANSWER} 字')
    return errors


# --------------------------------------------------------------------------- grades import
def validate_grades(data, assignment_code, valid_keys, locked_keys=frozenset()):
    """valid_keys: {(student_id, idx)} that have an answer row. Returns (list of grade dicts, errors)."""
    errors, rows, seen = [], [], set()
    if not isinstance(data, dict):
        return rows, ['檔案根層必須是物件']
    if data.get('schema') != GRADES_SCHEMA:
        errors.append(f'schema 必須是 {GRADES_SCHEMA}')
    if data.get('assignment') != assignment_code:
        errors.append(f'assignment 必須是 {assignment_code}')
    grades = data.get('grades')
    if not isinstance(grades, list) or not grades:
        return rows, errors + ['grades 必須是非空陣列']
    for g in grades:
        if not isinstance(g, dict):
            errors.append('grades 內有非物件項目')
            continue
        key = (g.get('student_id'), g.get('idx'))
        tag = f'{key[0]} Q{key[1]}'
        if key in seen:
            errors.append(f'{tag}:重複')
            continue
        seen.add(key)
        if key not in valid_keys:
            errors.append(f'{tag}:沒有對應的作答')
            continue
        if key in locked_keys:
            errors.append(f'{tag}:已定案,不可覆寫')
            continue
        if not _is_int(g.get('score')) or g['score'] not in (0, 1, 2):
            errors.append(f'{tag}:score 只能是 0、1、2(目前 {g.get("score")!r})')
            continue
        rationale = g.get('rationale')
        if not isinstance(rationale, str) or not rationale.strip() or len(rationale) > MAX_RATIONALE:
            errors.append(f'{tag}:rationale 需為 1–{MAX_RATIONALE} 字')
            continue
        flags = g.get('flags', [])
        if (not isinstance(flags, list) or len(flags) > MAX_FLAGS
                or any(not isinstance(f, str) or len(f) > 60 for f in flags)):
            errors.append(f'{tag}:flags 必須是字串陣列(最多 {MAX_FLAGS} 項、每項 ≤ 60 字)')
            continue
        needs = g.get('needs_review', False)
        if not isinstance(needs, bool):
            errors.append(f'{tag}:needs_review 必須是 true/false')
            continue
        rows.append({'student_id': key[0], 'idx': key[1], 'score': g['score'], 'rationale': rationale.strip(),
                     'flags': flags, 'needs_review': needs})
    return rows, errors


# --------------------------------------------------------------------------- rubric scores import
def validate_rubric(data, assignment_code, rubric_max, known_shas=None):
    """known_shas: {student_id: accepted tag SHA or None}. Returns (rows, errors)."""
    errors, rows, seen = [], [], set()
    if not isinstance(data, dict):
        return rows, ['檔案根層必須是物件']
    if data.get('schema') != RUBRIC_SCHEMA:
        errors.append(f'schema 必須是 {RUBRIC_SCHEMA}')
    if data.get('assignment') != assignment_code:
        errors.append(f'assignment 必須是 {assignment_code}')
    if data.get('rubric_max') != rubric_max:
        errors.append(f'rubric_max 必須是 {rubric_max}(與作業設定一致)')
    scores = data.get('scores')
    if not isinstance(scores, list) or not scores:
        return rows, errors + ['scores 必須是非空陣列']
    for sc in scores:
        sid = sc.get('student_id') if isinstance(sc, dict) else None
        if not isinstance(sid, str) or sid in seen:
            errors.append(f'{sid!r}:學號缺少或重複')
            continue
        seen.add(sid)
        total = sc.get('total')
        if not isinstance(total, (int, float)) or isinstance(total, bool) or not 0 <= total <= rubric_max:
            errors.append(f'{sid}:total 需介於 0 與 {rubric_max}')
            continue
        items = sc.get('items')
        if items is not None:
            try:
                item_sum = sum(float(i['score']) for i in items)
            except (TypeError, KeyError, ValueError):
                errors.append(f'{sid}:items 格式不正確')
                continue
            if abs(item_sum - total) > 0.01:
                errors.append(f'{sid}:items 分數合計 {item_sum} 與 total {total} 不一致')
                continue
        sha = sc.get('evaluated_sha')
        if known_shas is not None:
            expected = known_shas.get(sid)
            if sid not in known_shas:
                errors.append(f'{sid}:不在此課程')
                continue
            if expected and (not isinstance(sha, str) or not (expected.startswith(sha) or sha.startswith(expected))):
                errors.append(f'{sid}:evaluated_sha ({sha!r}) 與記錄的繳交版本 ({expected}) 不符')
                continue
        rows.append({'student_id': sid, 'total': float(total), 'evaluated_sha': sha if isinstance(sha, str) else None})
    return rows, errors


# --------------------------------------------------------------------------- repo check import
REPO_STATUSES = {'ok', 'not_found', 'no_access', 'error'}
FORBIDDEN_REPOCHECK_KEYS = {'content', 'patch', 'diff', 'files', 'code', 'source', 'blob', 'text', 'body'}
MAX_COMMITS = 200


def validate_repocheck(data, assignment_code, registered, paths=None):
    """registered: {student_id: repo_full_name}; paths (optional): {student_id: registered directory}.
    Returns (observed_at, observer, rows, errors).

    Only metadata is accepted (no file contents). Whole file is refused when anything is wrong.
    """
    from services.timeutil import parse_iso_z
    errors, rows, seen = [], [], set()
    if not isinstance(data, dict):
        return None, None, rows, ['檔案根層必須是物件']
    if data.get('schema') != REPOCHECK_SCHEMA:
        errors.append(f'schema 必須是 {REPOCHECK_SCHEMA}')
    if data.get('assignment') != assignment_code:
        errors.append(f'assignment 必須是 {assignment_code}')
    try:
        observed_at = parse_iso_z(data.get('observed_at'))
    except ValueError as exc:
        observed_at = None
        errors.append(f'observed_at:{exc}')
    observer = data.get('observer') if isinstance(data.get('observer'), str) else None
    if not observer:
        errors.append('缺少 observer')
    for path, key in _walk_keys(data):
        if key.lower() in FORBIDDEN_REPOCHECK_KEYS and 'commits' not in path.split('/')[-1:]:
            errors.append(f'{path}:查核檔只能包含中繼資料,不可含程式或檔案內容')
    repos = data.get('repos')
    if not isinstance(repos, list) or not repos:
        return observed_at, observer, rows, errors + ['repos 必須是非空陣列']
    tag_name = f'{assignment_code}-submit'
    for r in repos:
        sid = r.get('student_id') if isinstance(r, dict) else None
        if not isinstance(sid, str) or sid in seen:
            errors.append(f'{sid!r}:學號缺少或重複')
            continue
        seen.add(sid)
        if sid not in registered:
            errors.append(f'{sid}:此學生尚未在 LabTube 登記 Repo')
            continue
        if paths is not None and r.get('path') is not None and r.get('path') != paths.get(sid):
            errors.append(f'{sid}:path ({r.get("path")!r}) 與登記的目錄 ({paths.get(sid)!r}) 不一致(查核清單可能過期)')
            continue
        repo = r.get('repo')
        if not isinstance(repo, str) or repo.lower() != registered[sid].lower():
            errors.append(f'{sid}:repo ({repo!r}) 與登記的 ({registered[sid]}) 不一致')
            continue
        status = r.get('status')
        if status not in REPO_STATUSES:
            errors.append(f'{sid}:status 必須是 {sorted(REPO_STATUSES)}')
            continue
        row = {'student_id': sid, 'repo': registered[sid], 'status': status, 'error': str(r.get('error', ''))[:300],
               'private': r.get('private') if isinstance(r.get('private'), bool) else None,
               'tag_found': None, 'tag_sha': None, 'events': [], 'commits': []}
        if status == 'ok':
            tag = r.get('tag')
            if not isinstance(tag, dict) or tag.get('name') != tag_name or not isinstance(tag.get('found'), bool):
                errors.append(f'{sid}:tag 必須包含 name={tag_name} 與 found(true/false)')
                continue
            row['tag_found'] = tag['found']
            if tag['found']:
                sha = tag.get('sha')
                if not isinstance(sha, str) or not SHA_RE.match(sha.lower()):
                    errors.append(f'{sid}:tag.sha 格式不正確')
                    continue
                row['tag_sha'] = sha.lower()
            bad = False
            for ev in r.get('events', []) or []:
                try:
                    if ev.get('ref') != tag_name or ev.get('type') not in ('CreateEvent', 'PushEvent'):
                        continue
                    row['events'].append({'type': ev['type'], 'created_at': parse_iso_z(ev.get('created_at'))})
                except (ValueError, AttributeError):
                    errors.append(f'{sid}:events 格式不正確')
                    bad = True
                    break
            if bad:
                continue
            commits = r.get('commits', []) or []
            if not isinstance(commits, list) or len(commits) > MAX_COMMITS:
                errors.append(f'{sid}:commits 必須是最多 {MAX_COMMITS} 筆的陣列')
                continue
            for c in commits:
                try:
                    sha = c['sha'].lower()
                    msg = str(c.get('message', ''))
                    files = c.get('files_changed', 0)
                    if not SHA_RE.match(sha) or len(msg) > 200 or not _is_int(files) or files < 0:
                        raise ValueError
                    row['commits'].append({'sha': sha[:7], 'date': parse_iso_z(c['date']), 'message': msg[:120],
                                           'files_changed': files})
                except (KeyError, ValueError, TypeError, AttributeError):
                    errors.append(f'{sid}:commits 內有格式不正確的項目')
                    row['commits'] = []
                    break
        rows.append(row)
    return observed_at, observer, rows, errors


# --------------------------------------------------------------------------- assignment definitions
MAX_SECTIONS = 30
MAX_SECTION_TITLE = 100
MAX_SECTION_BODY = 30000
MAX_DETAILS_TOTAL = 200000
ASSIGNMENT_KEYS = {'code', 'title', 'unit', 'opens_at', 'due_at', 'rubric_max', 'rubric_url', 'details'}


def validate_details(details, tag):
    """The assignment brief: {"sections": [{"title", "body"}]}, body is Markdown. Returns (normalized or None, errors)."""
    errors = []
    if not isinstance(details, dict):
        return None, [f'{tag}:details 必須是物件(含 sections 陣列)']
    extra = set(details) - {'sections'}
    if extra:
        errors.append(f'{tag}:details 不認得的欄位 {", ".join(sorted(extra))}')
    sections = details.get('sections')
    if not isinstance(sections, list) or not sections:
        return None, errors + [f'{tag}:details.sections 必須是非空陣列']
    if len(sections) > MAX_SECTIONS:
        errors.append(f'{tag}:details.sections 最多 {MAX_SECTIONS} 段(目前 {len(sections)})')
    clean, titles, total = [], set(), 0
    for n, sec in enumerate(sections, 1):
        where = f'{tag} 說明第 {n} 段'
        if not isinstance(sec, dict):
            errors.append(f'{where}:必須是物件')
            continue
        extra = set(sec) - {'title', 'body'}
        if extra:
            errors.append(f'{where}:不認得的欄位 {", ".join(sorted(extra))}')
        title, body = sec.get('title'), sec.get('body')
        if not isinstance(title, str) or not title.strip() or len(title.strip()) > MAX_SECTION_TITLE:
            errors.append(f'{where}:title 需為 1–{MAX_SECTION_TITLE} 字')
            continue
        if title.strip() in titles:
            errors.append(f'{where}:標題「{title.strip()}」重複')
        titles.add(title.strip())
        if not isinstance(body, str) or not body.strip() or len(body) > MAX_SECTION_BODY:
            errors.append(f'{where}:body(Markdown 文字)需為 1–{MAX_SECTION_BODY} 字')
            continue
        total += len(body)
        clean.append({'title': title.strip(), 'body': body.strip('\n')})
    if total > MAX_DETAILS_TOTAL:
        errors.append(f'{tag}:說明全文超過 {MAX_DETAILS_TOTAL} 字(目前 {total})')
    return ({'sections': clean} if not errors else None), errors


def validate_assignments(data, course_code, existing_codes=frozenset(), allow_existing=False):
    """Assignment definitions to create (or, with ``allow_existing``, to update). Returns (rows, errors).

    Rows carry naive-UTC datetimes and ``exists``. By default a code that already exists in the course is an error:
    importing only creates. ``details`` (the brief) is optional; ``details`` = None in a row means "not in the file".
    """
    from services.timeutil import parse_taipei_local
    errors, rows, seen = [], [], set()
    if not isinstance(data, dict):
        return rows, ['檔案根層必須是物件']
    if data.get('schema') != ASSIGNMENTS_SCHEMA:
        errors.append(f'schema 必須是 {ASSIGNMENTS_SCHEMA}')
    if data.get('course') not in (None, course_code):
        errors.append(f'course 必須是 {course_code}(檔案內為 {data.get("course")!r});此欄位可省略')
    items = data.get('assignments')
    if not isinstance(items, list) or not items:
        return rows, errors + ['assignments 必須是非空陣列']
    for n, a in enumerate(items, 1):
        if not isinstance(a, dict):
            errors.append(f'第 {n} 項:必須是物件')
            continue
        code = a.get('code')
        tag = code if isinstance(code, str) and code else f'第 {n} 項'
        exists = False
        if not isinstance(code, str) or not CODE_RE.match(code):
            errors.append(f'{tag}:code 必須是小寫 hw 加兩位數字,例如 hw01')
        elif code in seen:
            errors.append(f'{tag}:code 在檔案內重複')
        elif code in existing_codes:
            if allow_existing:
                exists = True
            else:
                errors.append(f'{tag}:此課程已有這個代號(匯入只能新增;要更新請勾選「更新已存在的作業」)')
        if isinstance(code, str):
            seen.add(code)
        title, unit = a.get('title'), a.get('unit')
        if not isinstance(title, str) or not title.strip() or len(title.strip()) > 200:
            errors.append(f'{tag}:title 需為 1–200 字')
        if not isinstance(unit, str) or not unit.strip() or len(unit.strip()) > 200:
            errors.append(f'{tag}:unit(所屬單元名稱)需為 1–200 字')
        times = {}
        for key in ('opens_at', 'due_at'):
            val = a.get(key)
            if val in (None, ''):
                times[key] = None
            elif not isinstance(val, str):
                errors.append(f'{tag}:{key} 必須是 "YYYY-MM-DD HH:MM" 字串(台北時間)')
            else:
                try:
                    times[key] = parse_taipei_local(val)
                except ValueError:
                    errors.append(f'{tag}:{key} 無法解析 {val!r},格式為 "YYYY-MM-DD HH:MM"(台北時間)')
        if times.get('opens_at') and times.get('due_at') and times['opens_at'] >= times['due_at']:
            errors.append(f'{tag}:opens_at 必須早於 due_at')
        rmax = a.get('rubric_max', 100)
        if not _is_int(rmax) or rmax < 1:
            errors.append(f'{tag}:rubric_max 必須是正整數(預設 100)')
        url = a.get('rubric_url')
        if url is not None and (not isinstance(url, str) or len(url) > 300):
            errors.append(f'{tag}:rubric_url 必須是 300 字以內的字串')
        details = None
        if 'details' in a:
            details, derrs = validate_details(a['details'], tag)
            errors.extend(derrs)
        extra = set(a) - ASSIGNMENT_KEYS
        if extra:
            errors.append(f'{tag}:不認得的欄位 {", ".join(sorted(extra))}')
        rows.append({'code': code, 'title': (title or '').strip(), 'unit': (unit or '').strip(),
                     'opens_at': times.get('opens_at'), 'due_at': times.get('due_at'),
                     'rubric_max': rmax if _is_int(rmax) else 100, 'rubric_url': (url or '').strip() or None,
                     'details': details, 'exists': exists,
                     'fields': {k for k in ('opens_at', 'due_at', 'rubric_max', 'rubric_url') if k in a}})
    return rows, errors
