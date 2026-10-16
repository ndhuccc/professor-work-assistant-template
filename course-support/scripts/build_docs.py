#!/usr/bin/env python3
"""把 Repo 內容整理成 MkDocs 網站的原始檔目錄(暫存區 ``.site_src/``)。

為什麼需要這一步?
    * Repo 的目錄結構是為「教學與協作」設計的,不是為網站設計的。
    * 解答(``labs/*/solution/``)只能在 ``release_schedule.toml`` 規定的日期之後
      才出現在網站上,這個判斷集中在這支腳本,不必手動改網站設定。

用法::

    python scripts/build_docs.py              # 以今天日期建置暫存區
    python scripts/build_docs.py --today 2026-11-01   # 模擬某一天(測試用)
    mkdocs build                              # 之後再用 MkDocs 產生 site/

需要 Python >= 3.11(使用標準函式庫 ``tomllib``,無第三方相依)。
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sys
import tomllib
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / ".site_src"

# 要放進網站的根目錄文件(README 會變成首頁 index.md)
ROOT_DOCS = [
    "syllabus.md",
    "schedule.md",
    "FAQ.md",
    "glossary.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
]

# 要整個複製的資料夾(只複製網站會用到的檔案類型)
CONTENT_DIRS = [
    "lectures",
    "labs",
    "assignments",
    "projects",
    "exams",
    "quizzes",
    "references",
    "study-guide",
    "notebooks",
    "slides",
]

# 各資料夾允許的副檔名。注意:labs 只放 .md,因此 starter/solution 的 .py 不會被整包複製。
ALLOWED_SUFFIXES = {".md", ".html", ".pdf", ".png", ".svg", ".jpg", ".jpeg", ".gif"}

# slides/ 另外收錄可下載的投影片格式:JianBauDau 的 JSON 與 PPTX(學生下載用)。
# 其他資料夾不受影響,避免把 JSON 測試資料等整包複製到網站。
SLIDE_SUFFIXES = ALLOWED_SUFFIXES | {".json", ".pptx"}

# MathJax 設定:讓 $...$ 與 $$...$$ 能在網站上渲染
MATHJAX_JS = r"""window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"]],
    processEscapes: true,
    processEnvironments: true
  },
  options: {
    ignoreHtmlClass: ".*|",
    processHtmlClass: "arithmatex"
  }
};

document$.subscribe(() => {
  MathJax.startup.output.clearCache();
  MathJax.typesetClear();
  MathJax.texReset();
  MathJax.typesetPromise();
});
"""


def load_release_dates(today_tz: str | None = None) -> tuple[dict[str, dt.date], ZoneInfo]:
    """讀取 ``release_schedule.toml``,回傳 (實驗代號 -> 釋出日期, 時區)。"""
    path = ROOT / "release_schedule.toml"
    if not path.exists():
        return {}, ZoneInfo(today_tz or "UTC")
    with path.open("rb") as f:
        data = tomllib.load(f)
    tz = ZoneInfo(data.get("timezone", "UTC"))
    dates = {k: v for k, v in data.get("solutions", {}).items() if isinstance(v, dt.date)}
    return dates, tz


def copy_content(stage: Path) -> int:
    """複製文件與資源到暫存區,回傳複製的檔案數。"""
    count = 0

    # 首頁:README.md -> index.md
    shutil.copyfile(ROOT / "README.md", stage / "index.md")
    count += 1

    # 授權:LICENSE 沒有副檔名,MkDocs 不會處理,故包成 Markdown 頁面
    lic = ROOT / "LICENSE"
    if lic.exists():
        (stage / "LICENSE.md").write_text(
            "# 授權\n\n```text\n" + lic.read_text(encoding="utf-8") + "\n```\n", encoding="utf-8"
        )
        count += 1

    for name in ROOT_DOCS:
        src = ROOT / name
        if src.exists():
            shutil.copyfile(src, stage / name)
            count += 1

    for folder in CONTENT_DIRS:
        base = ROOT / folder
        if not base.exists():
            continue
        for src in base.rglob("*"):
            if folder == "slides" and src.name == "FORMATS.md":
                continue  # 老師用的格式說明,不放進學生網站
            allowed = SLIDE_SUFFIXES if folder == "slides" else ALLOWED_SUFFIXES
            if not src.is_file() or src.suffix.lower() not in allowed:
                continue
            dest = stage / src.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)
            count += 1

    # 圖片素材
    figures = ROOT / "assets" / "figures"
    if figures.exists():
        for src in figures.rglob("*"):
            if src.is_file() and src.suffix.lower() in ALLOWED_SUFFIXES:
                dest = stage / src.relative_to(ROOT)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dest)
                count += 1
    count += write_slides_index(stage)
    return count


SLIDE_FORMATS = {
    "jbd.json": "JianBauDau 投影片(JSON,需用 JianBauDau 播放器或編輯器開啟)",
    "pptx": "PowerPoint(PPTX)",
    "pdf": "PDF(可列印)",
    "html": "網頁(HTML,可離線開啟)",
}


# JianBauDau 播放器(Windows 執行檔)的下載位置。換版時改這一行即可。
PLAYER_URL = "https://github.com/ndhuccc/IDL115/releases/download/player-v1.0.1/JianBauDau-Player-1.0.1.exe"


SLIDE_SHORT = {"jbd.json": "JianBauDau", "pptx": "PowerPoint", "pdf": "PDF", "html": "HTML"}


def lecture_title(stem: str) -> str:
    """講義(lectures/<stem>.md)第一個標題,去掉「第N週」開頭;找不到回傳空字串。"""
    p = ROOT / "lectures" / f"{stem}.md"
    if not p.exists():
        return ""
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return re.sub(r"^第\s*\d+\s*週\s*", "", line[2:].strip())
    return ""


def write_slides_index(stage: Path) -> int:
    """產生網站的投影片下載頁(取代 slides/README.md),依週次列出各格式的檔案。

    檔名規則:``lecNN.<格式>``(該週正課)或 ``lecNN-<slug>.<格式>``(該週的補充/自主學習教材)。
    """

    base = ROOT / "slides"
    if not base.exists():
        return 0
    lecture_re = re.compile(r"^(lec\d{2})(?:-([a-z0-9][a-z0-9-]*))?\.(jbd\.json|pptx|pdf|html)$")
    weeks: dict[str, dict[str, list[tuple[str, str]]]] = {}
    others: list[str] = []
    for p in sorted(base.iterdir()):
        if not p.is_file() or p.name in ("README.md", "FORMATS.md"):
            continue
        m = lecture_re.match(p.name)
        if m:
            week, slug, fmt = m.group(1), m.group(2) or "", m.group(3)
            weeks.setdefault(week, {}).setdefault(slug, []).append((fmt, p.name))
        else:
            others.append(p.name)

    lines = ["# 投影片下載(Slides)", "",
             "每週的投影片可依需要下載。JianBauDau 格式請用 JianBauDau 播放器開啟;"
             "PPTX、PDF、HTML 可直接用一般軟體開啟。", "",
             "同一週可以有多份教材:沒有後綴的是該週正課,"
             "有後綴的(例如 `lec02-parameter-estimation`)是補充或自主學習教材。", ""]
    lines += ["## JianBauDau 播放器", "",
              f"- [下載 JianBauDau 播放器 1.0.1(Windows,.exe)]({PLAYER_URL})",
              "- 開啟方式:執行播放器後按 Ctrl+O 選擇 `.jbd.json` 檔,或把檔案拖進視窗。",
              "- 第一次執行時 Windows 可能出現安全性提示,請確認下載來源是本頁連結。", ""]
    if not weeks and not others:
        lines.append("目前尚無投影片。")
    if weeks:
        # 一週一個頁籤、一個頁籤一張表(pymdownx.tabbed);週次多、檔案多時不會擠成一張大表。
        lines += ["同一週的所有教材在該週的頁籤裡,請點選週次。", ""]
        for lec in sorted(weeks):
            num = int(lec[3:])
            lines += [f'=== "第 {num} 週"', "", "    | 教材 | 格式 | 下載 |", "    |---|---|---|"]
            for slug in sorted(weeks[lec]):
                stem = lec if slug == "" else f"{lec}-{slug}"
                label = "本週正課" if slug == "" else lecture_title(stem) or slug
                for fmt, name in sorted(weeks[lec][slug], key=lambda t: t[0]):
                    lines.append(f"    | {label} | {SLIDE_SHORT.get(fmt, fmt)} | [{name}]({name}) |")
            lines.append("")
    if others:
        lines += ["## 其他檔案", ""] + [f"- [{name}]({name})" for name in others] + [""]

    dest = stage / "slides" / "README.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 1


def rewrite_links(stage: Path) -> None:
    """修正「在 GitHub 上正常、在網站上失效」的連結。

    * 資料夾連結 ``](labs/)``  ->  ``](labs/README.md)``(GitHub 會顯示資料夾,MkDocs 不會)
    * ``](LICENSE)``           ->  ``](LICENSE.md)``(對應上面包裝後的授權頁)
    """
    for md in stage.rglob("*.md"):
        text = md.read_text(encoding="utf-8")
        new = text
        for folder in CONTENT_DIRS:
            new = new.replace(f"]({folder}/)", f"]({folder}/README.md)")
            new = new.replace(f"](./{folder}/)", f"](./{folder}/README.md)")
        new = new.replace("](LICENSE)", "](LICENSE.md)")
        if new != text:
            md.write_text(new, encoding="utf-8")


def publish_due_solutions(stage: Path, today: dt.date, dates: dict[str, dt.date]) -> list[str]:
    """對「日期已到」的實驗,產生 ``labs/<lab>/solution.md``,回傳已釋出的代號。"""
    released: list[str] = []
    for lab, due in sorted(dates.items()):
        if today < due:
            continue
        sol_dir = ROOT / "labs" / lab / "solution"
        if not sol_dir.is_dir():
            print(f"[警告] release_schedule.toml 列出 {lab},但找不到 {sol_dir}")
            continue
        parts = [f"# {lab} 參考解答\n", f"> 釋出日期:{due.isoformat()}\n"]
        for py in sorted(sol_dir.glob("*.py")):
            parts.append(f"\n## `{py.name}`\n\n```python\n{py.read_text(encoding='utf-8')}\n```\n")
        out = stage / "labs" / lab / "solution.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(parts), encoding="utf-8")
        released.append(lab)
    return released


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--today", help="模擬今天日期(YYYY-MM-DD),預設為設定時區的今天")
    args = parser.parse_args()

    dates, tz = load_release_dates()
    today = dt.date.fromisoformat(args.today) if args.today else dt.datetime.now(tz).date()

    # 每次都從乾淨的暫存區開始,避免殘留已撤回的內容
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)

    n = copy_content(STAGE)
    rewrite_links(STAGE)
    released = publish_due_solutions(STAGE, today, dates)

    # 側邊導覽的順序:依 schedule.md 的週次與輸入順序(MkDocs 預設會按檔名排序)
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import sync_nav
        sync_nav.main()
    except Exception as exc:  # 導覽順序失敗不應擋住建置
        print(f"[警告] 無法更新 mkdocs.yml 的 nav:{exc}")

    js = STAGE / "javascripts"
    js.mkdir(exist_ok=True)
    (js / "mathjax.js").write_text(MATHJAX_JS, encoding="utf-8")

    print(f"今天:{today}｜複製 {n} 個檔案｜已釋出解答:{released or '無'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
