#!/usr/bin/env python3
"""離線檢查 labtube.assignments.v1 匯入檔,並對照 assignments/hwNN/README.md。

用法(只需 Python 3.9+,不需安裝套件):
    python3 .agents/skills/assignment-design/check_assignments.py assignments/labtube-import/assignments_hw02.json

規則與 LabTube 的 services/contracts.py::validate_assignments 相同(那邊才是準):
    FAIL = LabTube 會拒絕整批檔案,或 README 與匯入檔互相矛盾;WARN = 請自行判斷。
退出碼:有 FAIL 為 1,否則 0。
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

SCHEMA = "labtube.assignments.v1"
CODE_RE = re.compile(r"^hw\d{2}$")
ALLOWED = {"code", "title", "unit", "opens_at", "due_at", "rubric_max", "rubric_url", "details"}
REQUIRED_SECTIONS = ("題目", "評分標準")      # 匯入檔的作業說明至少要有這兩段(標題以包含為準)
# assignments/README.md §6.0 的標準配分:面向 -> (優, 可, 待加強)
STANDARD = {"推導正確性": (40, 28, 10), "實驗與圖表": (35, 25, 10), "重現性": (25, 18, 5)}
ROOT = Path(__file__).resolve().parents[3]

results = []


def add(level, where, msg):
    results.append((level, where, msg))


def parse_time(text):
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text.strip(), fmt)
        except ValueError:
            pass
    raise ValueError(text)


def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


MISSING = object()


def check_details(tag, details):
    """作業說明 details:規則同 LabTube 的 validate_details。"""
    if details is MISSING:
        add("WARN", tag, "沒有 details(作業說明);學生在 LabTube 看不到題目與評分標準,請用 build_labtube_import.py 產生")
        return
    if not isinstance(details, dict) or set(details) - {"sections"}:
        add("FAIL", tag, "details 必須是只含 sections 的物件")
        return
    secs = details.get("sections")
    if not isinstance(secs, list) or not secs:
        add("FAIL", tag, "details.sections 必須是非空陣列")
        return
    if len(secs) > 30:
        add("FAIL", tag, f"details.sections 最多 30 段(目前 {len(secs)})")
    titles, total = set(), 0
    for n, sec in enumerate(secs, 1):
        where = f"{tag} 說明第 {n} 段"
        if not isinstance(sec, dict) or set(sec) - {"title", "body"}:
            add("FAIL", where, "必須是只含 title 與 body 的物件")
            continue
        t, b = sec.get("title"), sec.get("body")
        if not isinstance(t, str) or not t.strip() or len(t.strip()) > 100:
            add("FAIL", where, "title 需為 1–100 字")
        elif t.strip() in titles:
            add("FAIL", where, f"標題「{t.strip()}」重複")
        else:
            titles.add(t.strip())
        if not isinstance(b, str) or not b.strip() or len(b) > 30000:
            add("FAIL", where, "body(Markdown)需為 1–30000 字")
        else:
            total += len(b)
            if re.search(r"<\s*(script|iframe|object|embed)\b", b, re.I):
                add("WARN", where, "內容含 script/iframe 等標籤;LabTube 會清除它們,請改用 Markdown")
            if re.search(r"\]\((?!https?:|mailto:|#)[^)\s]+\)", b):
                add("WARN", where, "內容有相對連結;在 LabTube 裡會失效,請用 build_labtube_import.py 轉成完整網址")
    if total > 200000:
        add("FAIL", tag, f"說明全文超過 200000 字(目前 {total})")
    for need in REQUIRED_SECTIONS:
        if not any(need in t for t in titles):
            add("WARN", tag, f"作業說明沒有「{need}」段落")


def check_entry(n, a, seen):
    tag = a.get("code") if isinstance(a, dict) and isinstance(a.get("code"), str) and a.get("code") else f"第 {n} 項"
    if not isinstance(a, dict):
        add("FAIL", tag, "必須是物件")
        return None
    code = a.get("code")
    if not isinstance(code, str) or not CODE_RE.match(code):
        add("FAIL", tag, "code 必須是小寫 hw 加兩位數字,例如 hw01")
    elif code in seen:
        add("FAIL", tag, "code 在檔內重複")
    if isinstance(code, str):
        seen.add(code)
    for key in ("title", "unit"):
        v = a.get(key)
        if not isinstance(v, str) or not v.strip() or len(v.strip()) > 200:
            add("FAIL", tag, f"{key} 需為 1–200 字")
    times = {}
    for key in ("opens_at", "due_at"):
        v = a.get(key)
        if v in (None, ""):
            times[key] = None
        elif not isinstance(v, str):
            add("FAIL", tag, f'{key} 必須是 "YYYY-MM-DD HH:MM" 字串(台北時間)')
        else:
            try:
                times[key] = parse_time(v)
            except ValueError:
                add("FAIL", tag, f'{key} 無法解析 {v!r},格式為 "YYYY-MM-DD HH:MM"')
    if times.get("opens_at") and times.get("due_at") and times["opens_at"] >= times["due_at"]:
        add("FAIL", tag, "opens_at 必須早於 due_at")
    if not times.get("due_at"):
        add("WARN", tag, "沒有 due_at;學生看不到截止時間,Repo 查核也無法判斷遲交")
    rmax = a.get("rubric_max", 100)
    if not is_int(rmax) or rmax < 1:
        add("FAIL", tag, "rubric_max 必須是正整數")
    elif rmax != 100:
        add("WARN", tag, f"rubric_max 是 {rmax};本課程標準是 100(與標準配分表一致)")
    url = a.get("rubric_url")
    if url is not None and (not isinstance(url, str) or len(url) > 300):
        add("FAIL", tag, "rubric_url 必須是 300 字以內的字串")
    elif isinstance(url, str) and url and not url.startswith("https://"):
        add("WARN", tag, "rubric_url 不是 https 網址")
    extra = set(a) - ALLOWED
    if extra:
        add("FAIL", tag, "不認得的欄位:" + ", ".join(sorted(extra)))
    check_details(tag, a.get("details", MISSING))
    return tag, code, a, times


def cell(readme, label):
    m = re.search(r"^\|\s*" + re.escape(label) + r"\s*\|\s*(.*?)\s*\|\s*$", readme, re.M)
    return m.group(1) if m else None


def check_readme(tag, code, a, times):
    path = ROOT / "assignments" / str(code) / "README.md"
    if not path.is_file():
        add("FAIL", tag, f"找不到 {path.relative_to(ROOT)}(匯入檔的作業必須先有說明文件)")
        return
    text = path.read_text(encoding="utf-8")
    where = f"{code}/README.md"

    for label, key in (("發佈日", "opens_at"), ("截止日", "due_at")):
        raw = cell(text, label) or ""
        m = re.search(r"(\d{4})-(\d{2})-(\d{2})", raw)
        if not m:
            add("FAIL" if label == "截止日" else "WARN", where, f"表格的「{label}」沒有絕對日期(YYYY-MM-DD),目前是 {raw!r}")
            continue
        readme_date = m.group(0)
        if times.get(key) and times[key].strftime("%Y-%m-%d") != readme_date:
            add("FAIL", where, f"「{label}」{readme_date} 與匯入檔 {key} {a.get(key)} 的日期不同")
        if key == "due_at" and times.get(key):
            hm = re.search(r"(\d{1,2}):(\d{2})", raw)
            if hm and times[key].strftime("%H:%M") != f"{int(hm.group(1)):02d}:{hm.group(2)}":
                add("FAIL", where, f"「截止日」時間 {hm.group(0)} 與匯入檔 {a.get(key)} 不同")

    if (cell(text, "配分") or "").strip() != "100":
        add("FAIL", where, "表格的「配分」必須是 100")
    for sec in ("題目", "評分標準", "繳交內容", "生成式 AI 使用聲明"):
        if not re.search(r"^##\s*" + sec, text, re.M):
            add("FAIL", where, f"缺少「## {sec}」標題(評分與測驗技能依賴它)")
    for sec in ("學習目標", "操作指引"):
        if not re.search(r"^##\s*" + sec, text, re.M):
            add("WARN", where, f"缺少「## {sec}」(本技能建議的章節)")
    title_line = re.search(r"^#\s+(.+)$", text, re.M)
    if title_line and a.get("title") and str(a["title"]).strip() not in title_line.group(1):
        add("WARN", where, f"README 標題 {title_line.group(1)!r} 沒有包含匯入檔的 title {a['title']!r}")
    unit = cell(text, "對應單元")
    if unit is not None and a.get("unit") and unit.strip() != str(a["unit"]).strip():
        add("FAIL", where, f"「對應單元」{unit!r} 與匯入檔 unit {a['unit']!r} 不同(單元名稱不一致會建出重複單元)")

    # Rubric 點數必須是標準配分表
    for name, pts in STANDARD.items():
        row = re.search(r"^\|\s*" + name + r"\s*\((\d+)\)\s*\|(.*)\|\s*$", text, re.M)
        if not row:
            add("FAIL", where, f"Rubric 缺少面向「{name}」")
            continue
        if int(row.group(1)) != pts[0]:
            add("FAIL", where, f"{name} 的配分是 {row.group(1)},標準為 {pts[0]}")
        got = tuple(int(x) for x in re.findall(r"\*\*(\d+)\*\*", row.group(2)))
        if got != pts:
            add("FAIL", where, f"{name} 的等級點數是 {got},標準為 {pts}")
    # 靜態判斷:Rubric 不該要求執行結果
    rub = text.split("評分標準", 1)[-1]
    for pat in (r"準確率[^。\n]{0,10}(達|超過|≥|>=)", r"可(以)?一鍵(執行|跑)", r"能(夠)?(成功)?執行(並|且)?(得到|產生)"):
        if re.search(pat, rub):
            add("WARN", where, f"Rubric 似乎要求「執行結果」({pat});評分不執行程式,請改成可靜態判斷的描述")
    # 匯入檔的作業說明要和 README 同步(README 是唯一來源)
    if "details" in a:
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            import build_labtube_import as blt
            fresh, _ = blt.build_entry(str(code), blt.site_url())
            if fresh["details"] != a["details"]:
                add("FAIL", where, "匯入檔的 details 和 README 不同步;請重新執行 build_labtube_import.py")
        except SystemExit as exc:
            add("WARN", where, f"無法比對 README 與 details:{exc}")
    # 公開頁面不得含答案
    if re.search(r"(參考解答|標準答案|solution\s*=|## *解答)", text):
        add("WARN", where, "README 內疑似含有解答字樣;作業說明會公開,請確認沒有答案")


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    path = Path(sys.argv[1])
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        print(f"FAIL  {path}: 無法讀取或不是合法 JSON:{exc}")
        return 1
    if not isinstance(data, dict):
        add("FAIL", "檔案", "根層必須是物件")
    else:
        if data.get("schema") != SCHEMA:
            add("FAIL", "schema", f"必須是 {SCHEMA}")
        extra_top = set(data) - {"schema", "course", "assignments"}
        if extra_top:
            add("WARN", "頂層", "LabTube 不使用的欄位:" + ", ".join(sorted(extra_top)))
        if "course" not in data:
            add("WARN", "course", "沒有 course 欄位;匯入時不會檢查課程代號(可省略,但填了更安全)")
        items = data.get("assignments")
        if not isinstance(items, list) or not items:
            add("FAIL", "assignments", "必須是非空陣列")
        else:
            seen = set()
            for n, a in enumerate(items, 1):
                info = check_entry(n, a, seen)
                if info and isinstance(info[1], str) and CODE_RE.match(info[1]):
                    check_readme(*info)
    order = {"FAIL": 0, "WARN": 1}
    for level, where, msg in sorted(results, key=lambda r: order[r[0]]):
        print(f"{level:4}  {where}:{msg}")
    fails = sum(1 for r in results if r[0] == "FAIL")
    warns = len(results) - fails
    print(f"\n結果:{fails} 個 FAIL、{warns} 個 WARN" + ("(可以交給老師審閱)" if not fails else "(請先修正 FAIL)"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
