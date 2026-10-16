# -*- coding: utf-8 -*-
"""Inject a `nav:` block into mkdocs.yml, ordered by schedule.md.

Why: MkDocs sorts pages by file path when no `nav` is given, which puts
`lec02-bayesian-inference.md` before `lec02.md`. The order we want is the order the
materials are listed in `schedule.md` (week, then the order the teacher entered them).

The function is idempotent: it replaces everything from the first `nav:` line to the end of that
block, and leaves the rest of mkdocs.yml untouched.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MK = ROOT / "mkdocs.yml"
NAV_START = "# --- nav(由 build_docs.py 依 schedule.md 產生,請勿手改)---\n"
NAV_END = "# --- nav 結束 ---\n"

# 側邊導覽的固定骨架:標題 -> 檔案或資料夾的 README
FIXED_HEAD = [("首頁 Home", "index.md"), ("課程大綱 Syllabus", "syllabus.md"), ("週次進度表 Schedule", "schedule.md")]
ASSIGNMENTS_GUIDE = ("作業繳交說明 Submission Guide", "assignments/README.md")
FIXED_TAIL = [
    ("專題 Projects", "projects/README.md"),
    ("考試與測驗 Exams & Quizzes", "exams/README.md"),
    ("實驗 Labs", "labs/README.md"),
    ("Notebook", "notebooks/README.md"),
    ("投影片下載 Slides", "slides/README.md"),
    ("參考資料 References", "references/README.md"),
    ("自學指引 Study Guide", "study-guide/README.md"),
    ("常見問題 FAQ", "FAQ.md"),
    ("術語表 Glossary", "glossary.md"),
    ("異動紀錄 Changelog", "CHANGELOG.md"),
    ("貢獻指南 Contributing", "CONTRIBUTING.md"),
    ("授權 License", "LICENSE.md"),
]


def lecture_order() -> list[tuple[str, str, str]]:
    """(週次, 標題, 路徑) for every lecture, in the order schedule.md lists them."""
    text = (ROOT / "schedule.md").read_text(encoding="utf-8")
    rows = re.findall(r"^\|\s*(\d+)\s*\|\s*([0-9/]+)\s*\|([^|]*)\|([^|]*)\|", text, re.M)
    order: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for week, _date, _topic, lec_cell in rows:
        for label, href in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", lec_cell):
            m = re.match(r"^lectures/(lec[0-9A-Za-z._-]*)\.md$", href.strip())
            if not m:
                continue
            slug = m.group(1)
            if slug in seen:
                continue
            seen.add(slug)
            order.append((week, label, f"lectures/{slug}.md"))
    # any lecture not listed in schedule.md is appended, so nothing disappears from the site
    lectures_dir = ROOT / "lectures"
    if lectures_dir.is_dir():
        for p in sorted(lectures_dir.glob("lec*.md")):
            if p.name != "README.md" and p.stem not in seen:
                seen.add(p.stem)
                order.append(("", p.stem, f"lectures/{p.name}"))
    return order


def yq(title: str) -> str:
    """YAML-safe nav title: quoted when it holds characters that could break a plain scalar."""
    if re.search(r"[:#\[\]{}&*!|>'\"%@`,]", title) or title != title.strip():
        return '"' + title.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return title


def assignment_order() -> list[tuple[str, str]]:
    """(標題, 路徑) for every assignments/hwNN/README.md, ascending by hwNN. Title = the README's first heading."""
    items = []
    for p in sorted((ROOT / "assignments").glob("hw[0-9][0-9]/README.md")):
        first = next((ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.startswith("# ")), "")
        title = first[2:].strip() or p.parent.name.upper()
        items.append((title, f"assignments/{p.parent.name}/README.md"))
    return items


def render_nav() -> str:
    lines = ["nav:", *[f"  - {t}: {p}" for t, p in FIXED_HEAD]]
    lectures = lecture_order()
    if lectures:
        lines.append("  - 講義 Lectures:")
        groups: dict[str, list[tuple[str, str]]] = {}
        for week, t, p in lectures:
            groups.setdefault(week, []).append((t, p))
        for week, items in groups.items():
            lines.append(f"      - 第 {week} 週 Week {week}:" if week else "      - 其他 Others:")
            lines += [f"          - {t}: {p}" for t, p in items]
    lines.append("  - 作業 Assignments:")
    lines.append(f"      - {yq(ASSIGNMENTS_GUIDE[0])}: {ASSIGNMENTS_GUIDE[1]}")
    if (ROOT / "assignments/ai-agent-prompt.md").exists():
        lines.append(f"      - {yq('請 AI agent 協助 AI Agent Prompt')}: assignments/ai-agent-prompt.md")
    lines += [f"      - {yq(t)}: {p}" for t, p in assignment_order()]
    # 沒有對應資料夾的項目(例如課程不設實驗而刪除 labs/)就不列入導覽,避免 mkdocs 警告
    lines += [f"  - {t}: {p}" for t, p in FIXED_TAIL if (ROOT / p).parent.exists()]
    return NAV_START + "\n".join(lines) + "\n" + NAV_END


# 講義標題格式(AGENTS.md §5.12 第 6 項):知識點講義寫 `KPNN 標題`,不用冒號、不加「(試做)」之類標註、不附英文
_KP_SLUG = re.compile(r"-kp(\d{2})(?:-|$)")
_KP_TITLE = re.compile(r"^KP(\d{2}) \S")
_NOTE_WORDS = re.compile(r"[（(\[【][^）)\]】]*(試做|草稿|待驗收|暫定|製作中|TODO|WIP|DRAFT)[^）)\]】]*[）)\]】]", re.I)
_TRAILING_EN = re.compile(r"[（(][^）)]*[A-Za-z]{3,}[^）)]*[）)]\s*$")


def check_titles(order: list[tuple[str, str, str]]) -> list[str]:
    """Return human-readable problems with the lecture titles that become the left-hand menu entries."""
    problems: list[str] = []
    for week, title, path in order:
        where = f"{path}(標題「{title}」)"
        if not week:
            problems.append(f"{where}:沒有列入 schedule.md,選單會歸到「其他」(§5.12 第 4 項)")
        m = _KP_SLUG.search(path)
        t = _KP_TITLE.match(title)
        if not t:
            problems.append(f"{where}:所有講義的標題都應為「KPNN 標題」(KP、兩位數編號、一個半形空格、標題,不用冒號)")
        elif m and t.group(1) != m.group(1):
            problems.append(f"{where}:標題的編號 KP{t.group(1)} 與檔名的 kp{m.group(1)} 不一致")
        if _NOTE_WORDS.search(title):
            problems.append(f"{where}:標題不要加「(試做)」「(草稿)」之類的標註")
        if _TRAILING_EN.search(title):
            problems.append(f"{where}:標題不要附英文括號")
    # 每一週的編號從 KP01 起依進度表順序遞增(檔名自帶 kpNN 的講義,以檔名編號為準,允許跳號)
    by_week: dict[str, list[tuple[str, str]]] = {}
    for week, title, path in order:
        if week:
            by_week.setdefault(week, []).append((title, path))
    for week, items in by_week.items():
        nums = [int(m.group(1)) for title, _ in items if (m := _KP_TITLE.match(title))]
        if len(nums) == len(items) and nums != sorted(set(nums)):
            problems.append(f"第 {week} 週:講義標題的編號重複或順序不對({', '.join(f'KP{n:02d}' for n in nums)}),應從 KP01 依進度表順序遞增")
        elif len(nums) == len(items) and not any(_KP_SLUG.search(p) for _, p in items) and nums != list(range(1, len(nums) + 1)):
            problems.append(f"第 {week} 週:講義標題的編號應為 KP01 起連續遞增,目前是 {', '.join(f'KP{n:02d}' for n in nums)}")
    return problems



def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--strict", action="store_true", help="標題格式有問題時以非 0 結束(預設只列出警告)")
    args, _ = ap.parse_known_args()
    problems = check_titles(lecture_order())
    for p in problems:
        print(f"[警告] 講義標題格式:{p}")
    text = MK.read_text(encoding="utf-8")
    block = render_nav()
    if NAV_START in text and NAV_END in text:
        start = text.index(NAV_START)
        end = text.index(NAV_END, start) + len(NAV_END)
        new = text[:start] + block + text[end:]
    else:
        new = text.rstrip("\n") + "\n\n" + block
    if new != text:
        MK.write_text(new, encoding="utf-8")
        print("mkdocs.yml nav updated")
    else:
        print("mkdocs.yml nav already up to date")
    if problems and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
