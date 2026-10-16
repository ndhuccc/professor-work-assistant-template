#!/usr/bin/env python3
"""Run on the TEACHER'S computer (not on the server): read students' assignment repos with the locally
logged-in GitHub CLI (`gh`) and write a labtube.repocheck.v1 file to upload to LabTube.

    python repo_check.py --roster roster_hw01.json --out C:\\outbox
    (roster_hw01.json is downloaded from LabTube: 作業 → Repo → 下載查核清單)

Why here and not on the server: the server holds no GitHub credentials (design decision D3). `gh` uses the
login you already have; this script never reads or prints a token.

What it collects — metadata only, never file contents:
  * whether the repo is readable by your account, and whether it is private
  * the hwNN-submit tag (and the commit it points to; annotated tags are dereferenced)
  * GitHub's own CreateEvent/PushEvent records for that tag (last 30 days)
  * commits up to the tag, limited to the directory the student registered for this assignment
    (default hwNN/): short SHA, date, first message line, files changed
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from urllib.parse import quote

MAX_COMMITS = 200
TOOL_VERSION = '1.0'


def default_gh(gh_cmd):
    def run(args, timeout=40):
        try:
            p = subprocess.run(list(gh_cmd) + list(args), capture_output=True, text=True, encoding='utf-8',
                               errors='replace', timeout=timeout)
            return p.returncode, p.stdout, p.stderr
        except (OSError, subprocess.TimeoutExpired) as exc:
            return 1, '', f'{type(exc).__name__}: {exc}'
    return run


def api(gh, path, retries=2):
    """GET a GitHub API path through gh. Returns (data|None, http_status|None, error text)."""
    err = ''
    for attempt in range(retries + 1):
        rc, out, stderr = gh(['api', path])
        if rc == 0:
            try:
                return json.loads(out), 200, ''
            except ValueError:
                return None, None, 'invalid JSON from gh'
        err = (stderr or out or '').strip()
        status = None
        for code in (404, 403, 401, 422, 409):
            if f'HTTP {code}' in err or f'({code})' in err:
                status = code
                break
        if status in (404, 403, 401, 409, 422):
            return None, status, err[:300]
        time.sleep(1.5 * (attempt + 1))        # transient (network, 5xx, rate limit): back off and retry
    return None, None, err[:300]


def iso_z(text):
    if not text:
        return None
    dt = datetime.fromisoformat(text.replace('Z', '+00:00')).astimezone(timezone.utc)
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')


def check_one(gh, repo, code, with_files=False, path=None):
    tag_name = f'{code}-submit'
    path = path or code
    result = {'repo': repo, 'path': path}
    info, status, err = api(gh, f'repos/{repo}')
    if info is None:
        result['status'] = 'no_access' if status in (404, 403, 401) else 'error'
        result['error'] = (f'HTTP {status}: Repo 不存在,或沒有與此帳號共用' if status in (404, 403, 401) else err) or 'unknown'
        return result
    result.update({'status': 'ok', 'private': bool(info.get('private'))})

    ref, status, err = api(gh, f'repos/{repo}/git/ref/tags/{quote(tag_name)}')
    tag = {'name': tag_name, 'found': False}
    if ref is not None:
        obj = ref.get('object', {})
        sha = obj.get('sha')
        if obj.get('type') == 'tag':                      # annotated tag → the commit it points to
            deref, _, _ = api(gh, f'repos/{repo}/git/tags/{sha}')
            sha = (deref or {}).get('object', {}).get('sha', sha)
        tag.update({'found': True, 'sha': sha})
    elif status not in (404, 409, None):
        result.update({'status': 'error', 'error': f'標籤查詢失敗:{err}'})
        return result
    elif status is None:
        result.update({'status': 'error', 'error': f'標籤查詢失敗:{err}'})
        return result
    result['tag'] = tag

    events, status, err = api(gh, f'repos/{repo}/events?per_page=100')
    result['events'] = []
    for ev in (events or []):
        payload = ev.get('payload', {})
        if ev.get('type') == 'CreateEvent' and payload.get('ref_type') == 'tag' and payload.get('ref') == tag_name:
            result['events'].append({'type': 'CreateEvent', 'ref': tag_name, 'created_at': iso_z(ev['created_at'])})
        elif ev.get('type') == 'PushEvent' and payload.get('ref') == f'refs/tags/{tag_name}':
            result['events'].append({'type': 'PushEvent', 'ref': tag_name, 'created_at': iso_z(ev['created_at'])})

    result['commits'] = []
    if tag['found']:
        collected, page = [], 1
        while len(collected) < MAX_COMMITS:
            data, st, er = api(gh, f'repos/{repo}/commits?sha={tag["sha"]}&path={quote(path)}&per_page=100&page={page}')
            if not data:
                break
            collected += data
            if len(data) < 100:
                break
            page += 1
        for c in collected[:MAX_COMMITS]:
            files = 0
            if with_files and len(result['commits']) < 50:
                detail, _, _ = api(gh, f'repos/{repo}/commits/{c["sha"]}')
                files = len((detail or {}).get('files', []))
            result['commits'].append({
                'sha': c['sha'], 'date': iso_z(c['commit']['author']['date']),
                'message': (c['commit'].get('message') or '').split('\n', 1)[0][:120], 'files_changed': files})
    return result


def run(roster, gh, observed_at=None, with_files=False, log=print):
    code = roster['assignment']
    repos = []
    for n, item in enumerate(roster['repos'], 1):
        log(f'[{n}/{len(roster["repos"])}] {item["student_id"]}  {item["repo"]}')
        entry = check_one(gh, item['repo'], code, with_files, item.get('path'))
        entry['student_id'] = item['student_id']
        repos.append(entry)
    return {'schema': 'labtube.repocheck.v1', 'assignment': code,
            'observed_at': observed_at or datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'observer': roster.get('observer') or 'teacher-gh', 'tool_version': TOOL_VERSION, 'repos': repos}


def inside_git_repo(path):
    cur = os.path.abspath(path)
    while True:
        if os.path.isdir(os.path.join(cur, '.git')):
            return True
        parent = os.path.dirname(cur)
        if parent == cur:
            return False
        cur = parent


def main(argv=None, gh=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--roster', required=True, help='roster_hwNN.json downloaded from LabTube')
    ap.add_argument('--out', required=True, help='folder for the result file (must NOT be inside a git repository)')
    ap.add_argument('--gh', default='gh', help='path of the GitHub CLI')
    ap.add_argument('--with-files', action='store_true', help='also fetch files-changed per commit (slow)')
    args = ap.parse_args(argv)

    gh = gh or default_gh([args.gh])
    rc, out, err = gh(['auth', 'status'])
    if rc != 0:
        print('gh 尚未登入或登入已失效,請先執行 `gh auth login`;未產生任何檔案。', file=sys.stderr)
        return 2
    if inside_git_repo(args.out):
        print('輸出資料夾位於 git 倉庫內,請改放在倉庫之外(查核結果含學生資料)。', file=sys.stderr)
        return 2
    with open(args.roster, encoding='utf-8') as f:
        roster = json.load(f)
    if not roster.get('repos'):
        print('清單中沒有任何已登記的 Repo。', file=sys.stderr)
        return 1
    doc = run(roster, gh, with_files=args.with_files)
    os.makedirs(args.out, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    path = os.path.join(args.out, f'repocheck_{roster["assignment"]}_{stamp}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    counts = {}
    for r in doc['repos']:
        counts[r['status']] = counts.get(r['status'], 0) + 1
    print(f'完成:{path}\n狀態統計:{counts}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
