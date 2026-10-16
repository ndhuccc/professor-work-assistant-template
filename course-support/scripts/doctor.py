#!/usr/bin/env python3
"""檢查課程 Repo 的目前狀態,並告訴 AI agent(或老師)下一步該做什麼。

用法::

    python scripts/doctor.py            # 人類可讀的報告
    python scripts/doctor.py --json     # 機器可讀(給 agent 解析)

只讀取,不會修改任何檔案。需要 Python >= 3.11,無第三方相依。

狀態判斷(``state`` 欄位):
    template     這是「範本 Repo」本身 —— 不應在此建立課程,請先用範本建立學期 Repo
    unconfigured 學期 Repo,但 ``{{佔位符}}`` 尚未被 new_semester.py 替換
    configured   已套用學期設定,可進入日常經營

退出碼:有任何 FAIL 時為 1,否則為 0。
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

OK, INFO, WARN, FAIL = "OK", "INFO", "WARN", "FAIL"
results: list[dict] = []


def add(level: str, title: str, detail: str = "", next_step: str = "") -> None:
    """記錄一項檢查結果。"""
    results.append({"level": level, "title": title, "detail": detail, "next": next_step})


def run(cmd: list[str], timeout: int = 20) -> tuple[int, str]:
    """執行外部命令,失敗或逾時回傳 (非 0, 空字串),不丟例外。"""
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
        return p.returncode, (p.stdout or "").strip()
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""


def load_new_semester():
    """以路徑載入 new_semester.py,重用它的佔位符規則與檔案掃描邏輯。"""
    spec = importlib.util.spec_from_file_location("new_semester", ROOT / "scripts" / "new_semester.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def find_placeholders(ns) -> dict[str, set[str]]:
    """掃描尚未替換的 {{佔位符}},回傳 名稱 -> 出現檔案集合。"""
    found: dict[str, set[str]] = {}
    for path in ns.iter_text_files(ROOT):
        text = path.read_text(encoding="utf-8", errors="replace")
        for m in ns.PLACEHOLDER.finditer(text):
            found.setdefault(m.group(1), set()).add(str(path.relative_to(ROOT)))
    return found


def check_environment() -> None:
    v = sys.version_info
    if v >= (3, 11):
        add(OK, "Python 版本", f"{v.major}.{v.minor}.{v.micro}")
    else:
        add(FAIL, "Python 版本過舊", f"{v.major}.{v.minor}(需要 3.11 以上)",
            "請安裝 Python 3.11 以上;Windows 可用 `py` 指令確認版本")
    add(OK if shutil.which("git") else WARN, "git", "已安裝" if shutil.which("git") else "找不到 git",
        "" if shutil.which("git") else "若 agent 需要推送,請安裝 git;否則可改用 GitHub 網頁上傳")


def check_gh() -> None:
    """檢查 GitHub 命令列工具(gh):已登入代表 agent 可走全自動流程(AGENTS.md 2-A / 7-A)。"""
    if not shutil.which("gh"):
        add(INFO, "未安裝 gh(GitHub 命令列工具)", "",
            "無法全自動建立課程資料夾與開啟網站;走 AGENTS.md 的 2-B / 7-B 手動流程,或徵得老師同意後安裝 gh")
        return
    code, _ = run(["gh", "auth", "status"])
    if code == 0:
        add(OK, "gh 已登入", "可走全自動流程(AGENTS.md 2-A / 7-A)")
    else:
        add(INFO, "gh 尚未登入或登入已失效", "",
            "請老師執行 `gh auth login --web`(會自動開瀏覽器,按『授權』即可);若環境不允許,走 2-B / 7-B 手動流程")


def check_git() -> tuple[str | None, str | None]:
    """檢查 git 狀態,回傳 (owner, repo)(解析不出則為 None)。"""
    if not (ROOT / ".git").exists():
        add(INFO, "不是 git 倉庫", "目前資料夾沒有 .git(可能是下載的壓縮檔)",
            "若要上傳到 GitHub,需先 clone 學期 Repo 或使用網頁上傳")
        return None, None
    code, url = run(["git", "remote", "get-url", "origin"])
    if code != 0 or not url:
        add(WARN, "沒有設定遠端 origin", "", "請老師提供 Repo 網址後設定 remote")
        return None, None
    m = re.search(r"github\.com[:/]([^/]+)/([^/.]+?)(?:\.git)?/?$", url)
    owner, repo = (m.group(1), m.group(2)) if m else (None, None)
    add(OK, "遠端 Repo", f"{owner}/{repo}" if owner else url)
    _, branch = run(["git", "branch", "--show-current"])
    _, dirty = run(["git", "status", "--porcelain"])
    n = len([ln for ln in dirty.splitlines() if ln.strip()])
    add(INFO if n else OK, "本機未提交變更", f"{n} 個檔案" if n else "無", "提交並推送後才會出現在 GitHub" if n else "")
    add(INFO, "目前分支", branch or "(未知)")
    return owner, repo


def check_visibility(owner: str | None, repo: str | None, has_solutions: bool) -> bool | None:
    """用 gh 查詢 Repo 是否私有;查不到回傳 None。"""
    if not (owner and repo) or not shutil.which("gh"):
        return None
    code, out = run(["gh", "api", f"repos/{owner}/{repo}", "--jq", ".private"])
    if code != 0 or out not in ("true", "false"):
        add(INFO, "無法判斷 Repo 是否公開", "gh 未登入或環境不允許查詢",
            "請老師到 Repo 頁面確認標籤是 Public 或 Private")
        return None
    private = out == "true"
    if private:
        add(OK, "Repo 可見度", "私有(Private)")
    elif has_solutions:
        add(FAIL, "Repo 是公開的,且含有 labs/*/solution/",
            "任何人都能看到參考解答(含 Git 歷史)",
            "請依 AGENTS.md §4 處理:改為私有,或改用不含解答的公開版 Repo。不要只刪檔案,歷史仍會保留")
    else:
        add(OK, "Repo 可見度", "公開(Public),且未含 solution/")
    return private


def check_files() -> None:
    required = ["README.md", "syllabus.md", "schedule.md", "mkdocs.yml", "requirements.txt",
                "release_schedule.toml", "scripts/new_semester.py", "scripts/build_docs.py",
                ".github/workflows/deploy-site.yml", ".github/workflows/autograde.yml"]
    missing = [f for f in required if not (ROOT / f).exists()]
    if missing:
        add(FAIL, "缺少必要檔案", ", ".join(missing), "請從範本復原這些檔案,不要自行重寫")
    else:
        add(OK, "必要檔案齊全")


def check_release_schedule(labs: list[str]) -> None:
    path = ROOT / "release_schedule.toml"
    if not path.exists():
        return
    data = tomllib.loads(path.read_text(encoding="utf-8")).get("solutions", {})
    unset = [k for k, v in data.items() if isinstance(v, dt.date) and v.year >= 2090]
    unlisted = [lab for lab in labs if lab not in data and (ROOT / "labs" / lab / "solution").is_dir()]
    if unset:
        add(WARN, "解答釋出日仍是佔位值(2099)", ", ".join(unset),
            "詢問老師各實驗的作業截止日,填入 release_schedule.toml;不填則網站永遠不會釋出解答")
    if unlisted:
        add(WARN, "有 solution/ 但未列入釋出時間表", ", ".join(unlisted), "在 release_schedule.toml 補上")
    if not unset and not unlisted:
        add(OK, "解答釋出時間表")


def check_privacy() -> None:
    """找出疑似成績/名單檔案(只看檔名,不讀內容)。"""
    code, out = run(["git", "ls-files"])
    names = out.splitlines() if code == 0 else [str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file()]
    # grade(s) 必須是獨立單字(前後為路徑/底線/連字號/點),避免誤判 autograde.yml
    pattern = re.compile(r"(成績|名單|學號|roster|(^|[/_-])grades?([/_.-]|$))", re.I)
    safe_prefixes = (".git/", ".github/", "scripts/", "AGENTS", "START_HERE", "PLAN", "SETUP", "COURSE_STATE")
    risky = [n for n in names if pattern.search(n) and not n.startswith(safe_prefixes)]
    if risky:
        add(FAIL, "疑似含有成績或學生名單的檔案", ", ".join(risky[:5]),
            "成績與名單不可放在 Repo。請老師確認後移出並從 Git 歷史清除(需要時請教專人)")
    else:
        add(OK, "隱私檢查", "未發現疑似成績/名單檔名(僅檢查檔名)")


def load_check_slides():
    """以路徑載入 check_slides.py,重用它的 JianBauDau 投影片檢查規則。"""
    spec = importlib.util.spec_from_file_location("check_slides", ROOT / "scripts" / "check_slides.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check_slides() -> None:
    """投影片:檔名慣例、JianBauDau JSON 的結構檢查,以及尚未提供投影片的講義。"""
    base = ROOT / "slides"
    skip = {"README.md", "FORMATS.md"}
    files = sorted(p for p in base.iterdir() if p.is_file() and p.name not in skip) if base.exists() else []
    if not files:
        add(INFO, "投影片", "尚未提供投影片", "可依 slides/FORMATS.md 放入 JianBauDau JSON、PPTX、PDF 或 HTML")
        return
    name_re = re.compile(r"^lec\d{2}(?:-[a-z0-9][a-z0-9-]*)?\.(jbd\.json|pptx|pdf|html)$")
    odd = [p.name for p in files if not name_re.match(p.name)]
    if odd:
        add(WARN, "投影片檔名不符合慣例", ", ".join(odd),
            "請改為 lecNN.<格式> 或 lecNN-<補充教材代號>.<格式>,例如 lec02.jbd.json")
    checker = load_check_slides()
    for p in files:
        if not p.name.endswith(".jbd.json"):
            continue
        for level, msg in checker.check_file(p):
            if level == checker.FAIL:
                add(FAIL, f"投影片 {p.name}", msg, "依 slides/FORMATS.md 修正")
            else:
                add(WARN, f"投影片 {p.name}", msg, "請老師確認")
    weeks_with = {m.group(1) for p in files if (m := re.match(r"^(lec\d{2})(?:-|\.)", p.name))}
    lectures = {p.stem for p in (ROOT / "lectures").glob("lec[0-9][0-9].md")} if (ROOT / "lectures").exists() else set()
    lectures |= {m.group(1) for p in (ROOT / "lectures").glob("lec[0-9][0-9]-*.md")
                 if (m := re.match(r"^(lec\d{2})-", p.name))}
    missing = sorted(lectures - weeks_with)
    if missing:
        add(INFO, "尚未提供投影片的講義", ", ".join(missing))
    else:
        add(OK, "投影片", f"{len(files)} 個檔案,每週講義都有對應投影片")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", action="store_true", help="輸出 JSON")
    args = parser.parse_args()
    # Windows 主控台常用 cp950,印不出 emoji 會丟 UnicodeEncodeError;改成無法編碼的字元以 ? 取代
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    check_environment()
    check_gh()
    ns = load_new_semester()
    placeholders = find_placeholders(ns)
    owner, repo = check_git()
    check_files()

    # ---- 判斷狀態 ----
    is_template_name = (repo or "").lower() == "course-template"
    has_toml = (ROOT / "semester.toml").exists()
    # 「核心」佔位符 = 必填欄位 + 自動推導項目。選填欄位(助教、教科書…)老師可以略過,
    # 不應讓整個 Repo 一直被判為「尚未設定」。
    core = set(ns.REQUIRED) | {"REPO_URL", "SITE_URL", "YEAR"} | {f"W{i:02d}" for i in range(1, ns.WEEKS + 1)}
    core_left = set(placeholders) & core
    optional_left = set(placeholders) - core
    if core_left and is_template_name:
        state = "template"
    elif core_left:
        state = "unconfigured"
    else:
        state = "configured"

    if state == "template":
        add(WARN, "這是範本 Repo 本身", f"仍有 {len(core_left)} 種必填佔位符",
            "不要在這裡建立課程。請老師用 Use this template 建立學期 Repo(AGENTS.md §3 Step 2)")
    elif state == "unconfigured":
        add(WARN, "尚未套用學期設定", f"仍有 {len(core_left)} 種必填佔位符;semester.toml "
            + ("已存在" if has_toml else "不存在"),
            "進行 AGENTS.md §3 的訪談,填寫 semester.toml,再執行 scripts/new_semester.py")
    else:
        add(OK, "學期設定", "必填欄位皆已套用")

    if optional_left and state != "template":
        add(INFO, "選填欄位尚未填寫", ", ".join(sorted(optional_left)),
            "老師想補時,寫進 semester.toml(或 [extra] 區段)後重新執行 scripts/new_semester.py;不補也不影響運作")

    labs = sorted(p.name for p in (ROOT / "labs").glob("lab*") if p.is_dir())
    has_solutions = any((ROOT / "labs" / lab / "solution").is_dir() for lab in labs)
    if labs:
        add(INFO, "實驗(Labs)", ", ".join(labs))
    if has_solutions:
        add(INFO, "含有參考解答", "labs/*/solution/ 存在", "請務必確認 Repo 可見度(見下一項)")
    private = check_visibility(owner, repo, has_solutions)
    if has_solutions and private is None and state != "template":
        add(WARN, "含 solution/ 但未確認可見度", "", "請老師確認 Repo 是 Private;若是 Public 請依 AGENTS.md §4 處理")

    check_release_schedule(labs)
    check_privacy()
    check_slides()

    state_file = ROOT / "COURSE_STATE.md"
    add(OK if state_file.exists() else WARN, "COURSE_STATE.md",
        "存在" if state_file.exists() else "不存在", "" if state_file.exists() else "請從範本復原")

    payload = {"state": state, "repo": f"{owner}/{repo}" if owner else None,
               "date": dt.date.today().isoformat(), "checks": results}

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        icon = {OK: "✅", INFO: "ℹ️ ", WARN: "⚠️ ", FAIL: "❌"}
        print(f"狀態:{state}｜Repo:{payload['repo'] or '(未知)'}｜{payload['date']}\n")
        for r in results:
            line = f"{icon[r['level']]} {r['title']}"
            if r["detail"]:
                line += f" — {r['detail']}"
            print(line)
            if r["next"] and r["level"] in (WARN, FAIL, INFO):
                print(f"     → {r['next']}")
    return 1 if any(r["level"] == FAIL for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
