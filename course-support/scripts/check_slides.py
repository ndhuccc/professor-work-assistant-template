#!/usr/bin/env python3
"""檢查 slides/ 內的 JianBauDau 投影片(.jbd.json)能否被播放器正確讀取。

用法::

    python scripts/check_slides.py                  # 檢查 slides/*.jbd.json
    python scripts/check_slides.py slides/lec01.jbd.json

只讀取,不修改檔案,只使用標準函式庫。

檢查依據:JianBauDau 的完整匯出格式(PresentationDocumentV3,由編輯器的 Export 產生),
以及 JianBauDau 的 AI_AGENT_FILE_FORMAT_SPEC.md 中「驗證規則」一節。

等級:
    FAIL  播放器會拒絕或無法正確播放,必須修正
    WARN  可以播放,但有隱私、大小或相容性風險,請老師確認
退出碼:有任何 FAIL 時為 1,否則為 0。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLIDES_DIR = ROOT / "slides"

FAIL = "FAIL"
WARN = "WARN"

WARN_SIZE_MB = 20      # 超過此大小提醒(內嵌媒體會讓 JSON 變大)
FAIL_SIZE_MB = 90      # GitHub 單一檔案上限為 100 MB
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
STUDENT_ID_RE = re.compile(r"(?<!\d)\d{9}(?!\d)")
STEP_KINDS = {"scene-overview", "focus-node", "enter-frame", "scene-point"}
EASINGS = {"linear", "easeInOut", "smooth"}
REQUIRED_KEYS = ("schemaVersion", "rootSceneId", "scenes", "nodes", "steps", "metadata")


def _positive(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def _strings(obj):
    """遞迴取出所有字串值。"""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


def check_document(data) -> list[tuple[str, str]]:
    """檢查已解析的文件資料,回傳 (等級, 訊息) 清單。"""
    issues: list[tuple[str, str]] = []

    def fail(msg):
        issues.append((FAIL, msg))

    def warn(msg):
        issues.append((WARN, msg))

    if not isinstance(data, dict):
        fail("頂層不是 JSON 物件")
        return issues

    # 匯入用的 page spec 不是完整簡報,學生無法直接播放
    if "pages" in data and "scenes" not in data:
        fail("這是匯入用的 page spec(含 pages),不是完整簡報;請在編輯器用 Export 重新匯出")
        return issues

    missing = [k for k in REQUIRED_KEYS if k not in data]
    if missing:
        fail(f"缺少必要欄位:{', '.join(missing)}")
        return issues

    if data["schemaVersion"] != 3:
        fail(f"schemaVersion 必須是 3,目前是 {data['schemaVersion']!r}")

    scenes: dict = data["scenes"]
    nodes: dict = data["nodes"]
    steps: list = data["steps"]
    root = data["rootSceneId"]

    if root not in scenes:
        fail(f"rootSceneId {root!r} 不在 scenes 中")
    elif scenes[root].get("parentFrameId") is not None:
        fail("根場景的 parentFrameId 必須是 null")

    # Scene ↔ Node 雙向一致
    owner: dict[str, str] = {}
    for sid, scene in scenes.items():
        if scene.get("id") != sid:
            fail(f"場景 key {sid!r} 與其 id 不一致")
        if not isinstance(scene.get("camera"), dict) or not (scene["camera"].get("zoom", 0) > 0):
            fail(f"場景 {sid!r} 的 camera.zoom 必須大於 0")
        for nid in scene.get("nodeIds", []):
            if nid not in nodes:
                fail(f"場景 {sid!r} 的 nodeIds 含有不存在的節點 {nid!r}")
                continue
            if nodes[nid].get("sceneId") != sid:
                fail(f"節點 {nid!r} 列在場景 {sid!r} 中,但其 sceneId 是 {nodes[nid].get('sceneId')!r}")
            if nid in owner:
                fail(f"節點 {nid!r} 同時屬於場景 {owner[nid]!r} 與 {sid!r}")
            owner[nid] = sid
    for nid in nodes:
        if nid not in owner:
            fail(f"節點 {nid!r} 是孤兒(沒有任何場景的 nodeIds 引用它)")

    # Frame ↔ 子場景 雙向一致
    for nid, node in nodes.items():
        if node.get("type") != "frame":
            continue
        child = (node.get("frame") or {}).get("childSceneId")
        if child not in scenes:
            fail(f"畫框 {nid!r} 指向不存在的子場景 {child!r}")
        elif scenes[child].get("parentFrameId") != nid:
            fail(f"子場景 {child!r} 的 parentFrameId 不等於畫框 {nid!r}")

    # Step
    orders = [s.get("order") for s in steps]
    if len(set(orders)) != len(orders):
        warn("有重複的 step order,播放順序會難以預期")
    notes_count = 0
    for s in steps:
        label = s.get("id", "?")
        target = s.get("target") or {}
        kind = target.get("kind")
        scene_id = target.get("sceneId")
        if kind not in STEP_KINDS:
            fail(f"step {label!r} 的 target.kind 不合法:{kind!r}")
        if scene_id not in scenes:
            fail(f"step {label!r} 的 target.sceneId {scene_id!r} 不存在")
        if kind == "focus-node" and nodes.get(target.get("nodeId"), {}).get("sceneId") != scene_id:
            fail(f"step {label!r} 的 focus-node 節點不在目標場景中")
        if kind == "enter-frame":
            fid = target.get("frameId")
            if nodes.get(fid, {}).get("type") != "frame" or nodes[fid].get("sceneId") != scene_id:
                fail(f"step {label!r} 的 enter-frame 畫框不合法")
            # enter-frame 在 Scene mode 沒有 reticle,時間軸卡片與畫布 reticle 就無法一對一。
            fail(f"step {label!r} 使用 enter-frame:它沒有 reticle;請改成以該 Frame 為中心的 scene-point(見 view-from-text 技能 §4B)")
        if kind == "scene-point":
            # 沒有 referenceViewport 時,zoom 不會隨播放視窗縮放:視窗比 1280x720 大就會露出相鄰頁,
            # 且與編輯器 Scene mode 的 reticle 範圍不一致(見 view-from-text 技能 §4B)。
            ref = target.get("referenceViewport")
            if not (isinstance(ref, dict) and _positive(ref.get("width")) and _positive(ref.get("height"))):
                fail(f"step {label!r} 的 scene-point 缺少 referenceViewport(16:9 請填 1280x720,4:3 請填 960x720)")
        if not (180 <= s.get("durationMs", -1) <= 10000):
            fail(f"step {label!r} 的 durationMs 必須在 180–10000")
        if not (0 <= s.get("holdMs", -1) <= 30000):
            fail(f"step {label!r} 的 holdMs 必須在 0–30000")
        if s.get("easing") not in EASINGS:
            fail(f"step {label!r} 的 easing 不合法:{s.get('easing')!r}")
        reveal = s.get("reveal") or {}
        reveal_items = list(reveal.get("enter", [])) + [{"nodeId": n} for n in reveal.get("exitNodeIds", [])]
        for item in reveal_items:
            rid = item.get("nodeId")
            if nodes.get(rid, {}).get("sceneId") != scene_id:
                fail(f"step {label!r} 的 reveal 節點 {rid!r} 不在目標場景中")
        if (s.get("speakerNotes") or "").strip():
            notes_count += 1
    if notes_count:
        warn(f"{notes_count} 個步驟含講者備註;學生下載的檔案會包含這些備註,請確認可以公開")

    # 含有 Frame 的場景:時間軸上的 step 必須與畫布上的 Frame reticle 一對一。
    # 每個 Frame 恰好由一個 step 聚焦(以該 Frame 為中心的 scene-point,或 focus-node),
    # 且這個場景不得有其他 step(例如開場的 scene-overview、「返回總覽」)。播放時會深度優先:
    # 先播 Frame 內部的頁面,播完自動退回該 Frame 的 reticle 並顯示 Finished,再接下一個 reticle。
    for sid in scenes:
        frames = [nid for nid, n in nodes.items() if n.get("type") == "frame" and n.get("sceneId") == sid]
        if not frames:
            continue
        scene_steps = [s for s in steps if (s.get("target") or {}).get("sceneId") == sid]
        shown: dict[str, list[str]] = {fid: [] for fid in frames}
        for s in scene_steps:
            t = s.get("target") or {}
            hit = None
            if t.get("kind") == "focus-node" and t.get("nodeId") in shown:
                hit = t["nodeId"]
            elif t.get("kind") == "scene-point" and isinstance(t.get("point"), dict):
                px, py = t["point"].get("x"), t["point"].get("y")
                best = None
                for fid in frames:
                    n = nodes[fid]
                    x, y = n["transform"]["x"], n["transform"]["y"]
                    if isinstance(px, (int, float)) and isinstance(py, (int, float)) and x <= px <= x + n["width"] and y <= py <= y + n["height"]:
                        d2 = (px - (x + n["width"] / 2)) ** 2 + (py - (y + n["height"] / 2)) ** 2
                        if best is None or d2 < best[0]:
                            best = (d2, fid)
                hit = best[1] if best else None
            if hit is None:
                fail(f"場景 {sid!r} 的 step {s.get('id', '?')!r}({t.get('kind')})沒有聚焦任何 Frame;"
                     "含 Frame 的場景只能有「每個 Frame 一個 step」,請刪除開場總覽或「返回總覽」")
            else:
                shown[hit].append(s.get("id", "?"))
        for fid, ids in shown.items():
            if not ids:
                fail(f"場景 {sid!r} 的 Frame {fid!r} 沒有對應的 step(reticle),播放時會被略過")
            elif len(ids) > 1:
                fail(f"場景 {sid!r} 的 Frame {fid!r} 有 {len(ids)} 個 step 聚焦它({', '.join(map(repr, ids))});應恰好一個")

    # 伺服器資產參照與媒體來源
    for nid, node in nodes.items():
        for key in ("image", "video"):
            media = node.get(key)
            if isinstance(media, dict):
                src = media.get("src", "")
                if not src:
                    fail(f"節點 {nid!r} 的 {key}.src 是空的")
                elif src.startswith("asset:"):
                    fail(f"節點 {nid!r} 的 {key}.src 是伺服器參照 {src!r},播放器無法讀取;請重新 Export")
                elif not src.startswith(("http://", "https://", "data:")):
                    warn(f"節點 {nid!r} 的 {key}.src 不是網址或內嵌資料,在別台電腦可能讀不到")
    if any(text.startswith("asset:") for text in _strings(nodes)):
        fail("節點含伺服器資產參照(asset:),播放器無法讀取;請重新 Export")

    aspect = (data.get("metadata") or {}).get("aspectRatio")
    if aspect not in ("16:9", "4:3"):
        warn(f"metadata.aspectRatio 應為 16:9 或 4:3,目前是 {aspect!r}")

    # 隱私:電子郵件、疑似學號
    emails: set[str] = set()
    student_ids: set[str] = set()
    for text in _strings(data):
        if text.startswith("data:"):
            continue  # 內嵌圖片是 base64 編碼,不是可讀文字;掃描會因長字串回溯而卡住
        emails.update(EMAIL_RE.findall(text))
        student_ids.update(STUDENT_ID_RE.findall(text))
    if emails:
        warn(f"內容含電子郵件 {sorted(emails)[:3]},請確認可以公開")
    if student_ids:
        warn(f"內容含疑似學號的 9 位數字 {sorted(student_ids)[:3]},請確認不是學生個資")

    return issues


def check_file(path: Path) -> list[tuple[str, str]]:
    """檢查單一 .jbd.json 檔案(含大小與 JSON 語法)。"""
    issues: list[tuple[str, str]] = []
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > FAIL_SIZE_MB:
        issues.append((FAIL, f"檔案 {size_mb:.1f} MB 超過 {FAIL_SIZE_MB} MB,GitHub 可能拒絕推送"))
    elif size_mb > WARN_SIZE_MB:
        issues.append((WARN, f"檔案 {size_mb:.1f} MB,內嵌媒體較多,下載會較慢"))
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        issues.append((FAIL, f"不是有效的 UTF-8 JSON:{exc}"))
        return issues
    issues.extend(check_document(data))
    return issues


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="檢查 JianBauDau 投影片 JSON")
    ap.add_argument("files", nargs="*", help="要檢查的檔案(預設 slides/*.jbd.json)")
    args = ap.parse_args(argv)

    paths = [Path(f) for f in args.files] or sorted(SLIDES_DIR.glob("*.jbd.json"))
    if not paths:
        print("slides/ 中沒有 .jbd.json 檔案,略過。")
        return 0

    worst = 0
    for path in paths:
        issues = check_file(path)
        if not issues:
            print(f"[OK]   {path.name}")
        for level, msg in issues:
            print(f"[{level}] {path.name}: {msg}")
            if level == FAIL:
                worst = 1
    return worst


if __name__ == "__main__":
    sys.exit(main())
