#!/usr/bin/env python3
"""依 ``semester.toml`` 把範本中的 ``{{佔位符}}`` 替換成本學期的實際資料。

典型流程(新學期初)::

    # 1. 在 GitHub 以本範本建立新 Repo,並 clone 下來
    # 2. 複製設定範例並填寫
    cp semester.example.toml semester.toml
    # 3. 先預覽(不寫檔),確認無誤再執行
    python scripts/new_semester.py --dry-run
    python scripts/new_semester.py

自動推導的佔位符(不必在設定檔填寫):
    REPO_URL、SITE_URL      由 ``github_user`` 與 ``repo_name`` 組成
    YEAR                    取自 ``start_date``
    W01 ... W18             由 ``start_date`` 起,每週 +7 天(週一開學即每週一的日期)

設定檔 ``[extra]`` 區段可加入任意額外佔位符(例如 ``HW01_DUE``)。

需要 Python >= 3.11(標準函式庫 ``tomllib``)。
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 佔位符格式:{{ABC_123}}(僅限大寫英數與底線,避免誤傷 LaTeX 的雙大括號)
PLACEHOLDER = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")

# 只處理文字檔;.ipynb 為 JSON,直接字串替換可能破壞格式,故不處理
TEXT_SUFFIXES = {".md", ".yml", ".yaml", ".toml", ".txt", ".py", ".json", ".html"}
TEXT_NAMES = {"LICENSE"}

# 不處理的路徑(說明文件本身含有佔位符範例;腳本與設定檔不應被改寫)
SKIP_DIRS = {".git", ".site_src", "site", "__pycache__", ".pytest_cache", ".venv", "scripts"}
SKIP_FILES = {"PLAN.md", "SETUP.md", "semester.toml", "semester.example.toml",
              "AGENTS.md", "CLAUDE.md", "START_HERE.md", "COURSE_STATE.md"}

# 設定檔必填欄位(對應佔位符名稱 -> 設定檔鍵名)
REQUIRED = {
    "COURSE_NAME": "course_name",
    "COURSE_CODE": "course_code",
    "SEMESTER": "semester",
    "UNIVERSITY": "university",
    "DEPARTMENT": "department",
    "INSTRUCTOR": "instructor",
    "EMAIL": "email",
    "GITHUB_USER": "github_user",
    "REPO_NAME": "repo_name",
    "START_DATE": "start_date",
}

# 其餘選填欄位(沒填就保留佔位符,事後在報告中列出)
OPTIONAL = {
    "COURSE_DESCRIPTION": "course_description",
    "CREDITS": "credits",
    "CLASS_TIME_LOCATION": "class_time_location",
    "TA": "ta",
    "OFFICE_HOUR": "office_hour",
    "TEXTBOOK": "textbook",
    "AI_POLICY": "ai_policy",
    "TEAM_SIZE": "team_size",
}

WEEKS = 18


def build_mapping(cfg: dict) -> dict[str, str]:
    """由設定檔建立 佔位符 -> 值 的對照表,並加入自動推導的項目。"""
    missing = [k for k in REQUIRED.values() if not cfg.get(k)]
    if missing:
        sys.exit(f"[錯誤] semester.toml 缺少必填欄位:{', '.join(missing)}")

    mapping: dict[str, str] = {}
    for placeholder, key in {**REQUIRED, **OPTIONAL}.items():
        if cfg.get(key) not in (None, ""):
            mapping[placeholder] = str(cfg[key])

    # 開學日期:TOML 的日期型別或字串皆可
    start = cfg["start_date"]
    if isinstance(start, str):
        start = dt.date.fromisoformat(start)
    mapping["START_DATE"] = start.isoformat()
    mapping["YEAR"] = str(start.year)

    # W01..W18:每週 +7 天
    for i in range(WEEKS):
        mapping[f"W{i + 1:02d}"] = (start + dt.timedelta(weeks=i)).strftime("%m/%d")

    user, repo = cfg["github_user"], cfg["repo_name"]
    mapping["REPO_URL"] = f"https://github.com/{user}/{repo}"
    mapping["SITE_URL"] = f"https://{user}.github.io/{repo}/"

    # 額外自訂佔位符
    for k, v in cfg.get("extra", {}).items():
        mapping[k.upper()] = str(v)
    return mapping


def iter_text_files(root: Path):
    """走訪需處理的文字檔。"""
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts[:-1]):
            continue
        if rel.name in SKIP_FILES:
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name in TEXT_NAMES:
            yield path


def apply(mapping: dict[str, str], dry_run: bool) -> tuple[int, dict[str, set[str]]]:
    """執行替換。回傳 (被修改的檔案數, 未解析的佔位符 -> 出現檔案集合)。"""
    changed = 0
    unresolved: dict[str, set[str]] = {}
    for path in iter_text_files(ROOT):
        text = path.read_text(encoding="utf-8")

        def repl(m: re.Match) -> str:
            name = m.group(1)
            if name in mapping:
                return mapping[name]
            unresolved.setdefault(name, set()).add(str(path.relative_to(ROOT)))
            return m.group(0)  # 沒有對應值就原樣保留

        new = PLACEHOLDER.sub(repl, text)
        if new != text:
            changed += 1
            print(("[預覽] " if dry_run else "[更新] ") + str(path.relative_to(ROOT)))
            if not dry_run:
                path.write_text(new, encoding="utf-8")
    return changed, unresolved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="semester.toml", help="設定檔路徑(預設 semester.toml)")
    parser.add_argument("--dry-run", action="store_true", help="只列出會更動的檔案,不寫入")
    args = parser.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = ROOT / cfg_path
    if not cfg_path.exists():
        sys.exit(f"[錯誤] 找不到 {cfg_path.name};請先 cp semester.example.toml semester.toml 並填寫")

    with cfg_path.open("rb") as f:
        cfg = tomllib.load(f)

    changed, unresolved = apply(build_mapping(cfg), args.dry_run)

    print(f"\n{'將會' if args.dry_run else '已'}更新 {changed} 個檔案。")
    if unresolved:
        print("\n以下佔位符尚未填入(請在設定檔補上,或手動編輯):")
        for name in sorted(unresolved):
            print(f"  {{{{{name}}}}}  →  {', '.join(sorted(unresolved[name]))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
