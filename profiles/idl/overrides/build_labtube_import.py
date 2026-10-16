#!/usr/bin/env python3
"""把 assignments/hwNN/README.md 轉成 LabTube 的匯入檔(labtube.assignments.v1),含完整的作業說明 details。

README 是唯一的內容來源;匯入檔由本程式產生,不要手改(改 README 後重新執行即可)。

用法(只需 Python 3.9+):
    python3 .agents/skills/assignment-design/build_labtube_import.py hw01
    python3 .agents/skills/assignment-design/build_labtube_import.py hw01 hw02 --course <LabTube課程代號>

對應關係:
    # HW 01 — 作業名稱         -> title
    | 發佈日 | 2026-10-12 |     -> opens_at(00:00,台北時間)
    | 截止日 | 2026-10-25(23:59,台北時間) | -> due_at
    | 對應單元 | 單元名稱 |      -> unit
    | 配分 | 100 |             -> rubric_max
    每個 "## 標題" 段落          -> details.sections[](內容保持 Markdown;相對連結改成課程網站的完整網址)
    <site_url>assignments/hwNN/ -> rubric_url(site_url 取自 mkdocs.yml)
"""
import argparse
import json
import posixpath
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCHEMA = "labtube.assignments.v1"
LINK = re.compile(r"(!?\[[^\]]*\]\()([^)\s]+)((?:\s+\"[^\"]*\")?\))")


def site_url():
    text = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    m = re.search(r'^site_url:\s*"?([^"\n]+?)"?\s*$', text, re.M)
    if not m:
        raise SystemExit("mkdocs.yml 沒有 site_url,無法產生完整連結")
    return m.group(1).rstrip("/") + "/"


def absolute(target, hw_dir, base):
    """Relative link inside the repo -> absolute URL on the course site (mkdocs directory URLs)."""
    if re.match(r"^([a-z][a-z0-9+.-]*:|#|//)", target, re.I):
        return target
    path, _, frag = target.partition("#")
    repo_path = posixpath.normpath(posixpath.join(hw_dir, path))
    if repo_path.startswith(".."):
        return target
    if repo_path.endswith("/README.md") or repo_path == "README.md":
        url = repo_path[: -len("README.md")]
    elif repo_path.endswith(".md"):
        url = repo_path[:-3] + "/"
    else:
        url = repo_path
    return base + url + (("#" + frag) if frag else "")


def fix_links(body, hw_dir, base):
    out, fenced = [], False
    for line in body.split("\n"):
        if line.lstrip().startswith("```"):
            fenced = not fenced
        out.append(line if fenced else LINK.sub(lambda m: m.group(1) + absolute(m.group(2), hw_dir, base) + m.group(3), line))
    return "\n".join(out)


def cell(text, label):
    m = re.search(r"^\|\s*" + re.escape(label) + r"\s*\|\s*(.*?)\s*\|\s*$", text, re.M)
    return m.group(1) if m else None


def split_sections(text):
    """[(title, body)] for each '## ' heading outside code fences; text before the first one is the header."""
    sections, cur, fenced = [], None, False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            fenced = not fenced
        m = None if fenced else re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            cur = [m.group(1), []]
            sections.append(cur)
        elif cur is not None:
            cur[1].append(line)
    return [(t, "\n".join(b).strip("\n")) for t, b in sections]


def build_entry(code, base):
    """Returns (entry dict, problems list) for assignments/<code>/README.md."""
    problems = []
    path = ROOT / "assignments" / code / "README.md"
    if not path.is_file():
        raise SystemExit(f"找不到 {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    h1 = re.search(r"^#\s+HW\s*0*\d+\s*[—–\-:：]\s*(.+?)\s*$", text, re.M)
    if not h1:
        problems.append("標題要寫成「# HW 01 — 作業名稱」,才能取得 title")
    entry = {"code": code, "title": h1.group(1) if h1 else "", "unit": (cell(text, "對應單元") or "").strip()}
    if not entry["unit"]:
        problems.append("表格缺少「對應單元」")
    opens = re.search(r"(\d{4}-\d{2}-\d{2})", cell(text, "發佈日") or "")
    if opens:
        entry["opens_at"] = opens.group(1) + " 00:00"
    due_cell = cell(text, "截止日") or ""
    due = re.search(r"(\d{4}-\d{2}-\d{2})", due_cell)
    if due:
        hm = re.search(r"(\d{1,2}):(\d{2})", due_cell)
        entry["due_at"] = f"{due.group(1)} {int(hm.group(1)):02d}:{hm.group(2)}" if hm else due.group(1) + " 23:59"
    else:
        problems.append("表格的「截止日」沒有 YYYY-MM-DD 日期")
    points = re.search(r"\d+", cell(text, "配分") or "")
    entry["rubric_max"] = int(points.group(0)) if points else 100
    entry["rubric_url"] = f"{base}assignments/{code}/"
    sections = [{"title": t, "body": fix_links(b, f"assignments/{code}", base)}
                for t, b in split_sections(text) if b.strip()]
    info = [f"- {label}:{value.strip()}" for label in ("預計花費", "繳交方式")
            if (value := cell(text, label))]
    if info:                      # the facts LabTube does not already show (due date, unit, points are shown by LabTube)
        sections.insert(0, {"title": "作業資訊", "body": fix_links("\n".join(info), f"assignments/{code}", base)})
    entry["details"] = {"sections": sections}
    if not entry["details"]["sections"]:
        problems.append("README 沒有任何「## 標題」段落")
    return entry, problems


def build(codes, course=None):
    base = site_url()
    doc = {"schema": SCHEMA}
    if course:
        doc["course"] = course
    doc["assignments"], problems = [], []
    for code in codes:
        entry, probs = build_entry(code, base)
        doc["assignments"].append(entry)
        problems += [f"{code}: {p}" for p in probs]
    return doc, problems


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("codes", nargs="+", help="作業代號,例如 hw01 hw02")
    ap.add_argument("--course", help="LabTube 的課程代號(選填;填了匯入時會檢查是否相符)")
    ap.add_argument("--out", help="輸出檔(預設 assignments/labtube-import/assignments_<hwNN 或 hwNN-hwMM>.json)")
    args = ap.parse_args()
    for c in args.codes:
        if not re.fullmatch(r"hw\d{2}", c):
            raise SystemExit(f"代號格式錯誤:{c}(必須是 hw 加兩位數字)")
    doc, problems = build(args.codes, args.course)
    for p in problems:
        print("WARN ", p)
    name = args.codes[0] if len(args.codes) == 1 else f"{args.codes[0]}-{args.codes[-1]}"
    out = Path(args.out) if args.out else ROOT / "assignments" / "labtube-import" / f"assignments_{name}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    n = sum(len(a["details"]["sections"]) for a in doc["assignments"])
    print(f"已寫入 {out}:{len(doc['assignments'])} 份作業、共 {n} 段說明")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
