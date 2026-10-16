#!/usr/bin/env python3
"""audit_deck.py -- automatic audit of a JianBauDau deck (slides/lecNN.jbd.json) for the checks a program can do.

    py .agents/skills/view-from-text/tools/audit_deck.py slides/lec03.jbd.json            # bilingual course deck (default)
    py .agents/skills/view-from-text/tools/audit_deck.py slides/lec03.jbd.json --monolingual
    py .agents/skills/view-from-text/tools/audit_deck.py slides/lec03.jbd.json --lecture lectures/lec03.md --speaker-notes

Covers AUDIT_CHECKLIST.md: A (format), B (cameras, connector colours, FRAME STYLE), E10 (contrast incl. frame titles),
D (fonts, titles), H5 (step / reticle structure), G14 (image alt), L (bilingual layout),
N3 (results without a visible derivation), P (speaker notes) and, with --lecture,
O1 (every lecture figure is used or explicitly excluded) and N6 (lecture formulas / numbers missing from the slides).
It does NOT replace the visual checks: run preview_deck.py and look at the contact sheets, then open the deck in JianBauDau.
Exit code 1 when there is any FAIL.

Conventions the checks rely on (SKILL.md 4F, 3B):
  * an image redrawn from a lecture figure carries the figure id in its node "name", e.g.  "fig:lec02-mixture-em-stages";
  * a page whose numbers come from a program run (iteration tables etc.) says so on the page: "〔程式計算〕" / "(computed)".
"""
import argparse
import json
import math
import re
import sys

W, H, HEADROOM, PITCH = 1280, 720, 100, 1440
STD_FRAME_STYLE = {"fill": "transparent", "stroke": "transparent", "textColor": "#f2ede4", "fontSize": 22, "radius": 0}
STD_FRAME_KEYS = {"childSceneId", "previewMode", "padding", "clip"}
CJK = re.compile(r"[㐀-鿿豈-﫿]")
MATH = re.compile(r"\$\$.*?\$\$|\$[^$]*\$", re.S)


def en_words(text):
    """Number of English words (2+ letters) outside formulas. A text block counts as bilingual with at least 3."""
    return len(re.findall(r"[A-Za-z]{2,}", MATH.sub(" ", text)))


NUM3 = re.compile(r"(?<![\d.])-?\d+\.\d{3,}(?![\d])")          # results usually carry 3+ decimals
NUM2 = re.compile(r"(?<![\d.\w])-?\d+\.\d{2,}(?![\d])")
_OPS = r"(\\times|×|\+|−|\\frac|\\dfrac|/|\\sum|\\cdot|\\sqrt|\^|\||\d\s*-\s*\d|\(\s*-?\d)"
DERIV = re.compile(r"=.*" + _OPS + "|" + _OPS + r".*=")   # a line with "=" and some arithmetic
COMPUTED = re.compile(r"〔程式計算〕|\(computed\)|程式計算|computed (by|with)")


def norm_tex(s):
    """Normalise a TeX string for coverage comparison (spacing, sizing and delimiters do not matter)."""
    s = re.sub(r"\\(left|right|bigl|bigr|Bigl|Bigr|biggl|biggr|big|Big|textstyle|displaystyle|,|;|!|quad|qquad|:)", "", s)
    s = re.sub(r"\\mathbf\{\\Theta\}", r"\\Theta", s)
    s = re.sub(r"[\s{}]", "", s)
    return s.strip(".,;。，")


def lecture_inventory(path):
    text = open(path, encoding="utf-8").read()
    figs = re.findall(r"\*\*圖說 `([^`]+)`\*\*", text)
    formulas = []
    for block in re.findall(r"\$\$(.*?)\$\$", text, re.S):
        for piece in re.split(r",\s*\\qquad|\\qquad|,\s*\\quad", block):
            p = norm_tex(piece)
            if len(p) >= 8: formulas.append((piece.strip(), p))
    # numbers from the Chinese paragraphs only (the English ones repeat them)
    zh = "\n".join(ln for ln in text.split("\n") if CJK.search(ln) and not ln.lstrip().startswith(("**Caption", "**Example", "**Plain", "**Formal", "`[Added]`")))
    numbers = sorted(set(NUM2.findall(zh)), key=lambda v: float(v))
    return figs, formulas, numbers


# (max display-formula blocks per page, max Chinese body characters per page) -- .agents/skills/LEVELS.md section 3
LEVEL_LIMITS = {"public": (0, 80), "highschool": (1, 100), "undergrad": (2, 120), "grad": (2, 120), "pro": (2, 120)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("--monolingual", action="store_true", help="skip the bilingual checks (only when the teacher asked for Chinese only)")
    ap.add_argument("--lecture", help="the lecture the deck was made from: checks figure coverage (O1) and formula/number coverage (N6)")
    ap.add_argument("--exclude-fig", action="append", default=[], help="lecture figure id the teacher agreed to leave out (repeatable)")
    ap.add_argument("--speaker-notes", action="store_true", help="every content page must carry speaker notes (P1)")
    ap.add_argument("--minutes", type=float, help="class-time budget for the main line (LEVELS.md section 7): warns when the estimate exceeds it (T1); pages whose step label starts with the extension marker are not counted")
    ap.add_argument("--max-pages-per-kp", type=int, default=6, help="hard cap on the pages of one unit (one knowledge point), extension and continuation pages included (U1)")
    ap.add_argument("--source", action="append", default=[], help="source text file(s): O2 warns when pages repeat long runs of the source (14+ identical CJK characters)")
    ap.add_argument("--narrative", action="store_true", help="require a bridge node (name contains 'bridge') on every content page and speaker notes that link to the previous and next page (R1, R3); see .agents/skills/NARRATIVE.md")
    ap.add_argument("--outline", action="store_true", help="print the title chain and bridge line of every page, per unit, for the reading test (NARRATIVE.md section 5)")
    ap.add_argument("--kps", type=int, help="number of knowledge points; with --minutes, prints the per-KP budget")
    ap.add_argument("--level", choices=sorted(LEVEL_LIMITS), help="teaching level (see .agents/skills/LEVELS.md): warns when a page exceeds the level's display-formula and body-text budget (Q1, Q2)")
    args = ap.parse_args()
    doc = json.load(open(args.deck, encoding="utf-8"))
    S, N, ST = doc["scenes"], doc["nodes"], doc["steps"]
    fails, warns = [], []
    F = lambda code, msg: fails.append(f"{code} {msg}")
    Wn = lambda code, msg: warns.append(f"{code} {msg}")

    # ------------------------------------------------------------ A: format
    root = doc.get("rootSceneId")
    if doc.get("schemaVersion") != 3: F("A1", "schemaVersion must be 3")
    if root not in S or S[root].get("parentFrameId") is not None: F("A1", "root scene")
    claimed = {}
    for sid, sc in S.items():
        if sc["id"] != sid: F("A3", f"scene id mismatch {sid}")
        cam = sc["camera"]
        if not (cam["zoom"] > 0 and all(math.isfinite(cam[k]) for k in ("x", "y", "rotation"))): F("A2", sid)
        for nid in sc["nodeIds"]:
            if nid not in N: F("A3", f"{sid} lists missing node {nid}"); continue
            if N[nid]["sceneId"] != sid: F("A3", f"{nid}.sceneId != {sid}")
            if nid in claimed: F("A4", f"{nid} listed by two scenes")
            claimed[nid] = sid
    for nid, n in N.items():
        if nid not in claimed: F("A4", f"orphan node {nid}")
        t = n["transform"]
        if not all(math.isfinite(t[k]) for k in ("x", "y", "scaleX", "scaleY", "rotation")) or t["scaleX"] == 0 or t["scaleY"] == 0: F("A5", nid)
        if not (n["width"] > 0 and n["height"] > 0): F("A5", f"{nid} size")
        if n["type"] == "frame":
            cs = n["frame"]["childSceneId"]
            if cs not in S or S[cs]["parentFrameId"] != nid: F("A6", f"frame {nid}")
        if n["type"] == "image" and not n.get("image", {}).get("src"): F("A7", nid)
        if n["type"] == "connector":
            c = n["connector"]
            a, b = c["sourceNodeId"], c["targetNodeId"]
            if a not in N or b not in N or N[a]["sceneId"] != n["sceneId"] or N[b]["sceneId"] != n["sceneId"] or a == b \
                    or N[a]["type"] == "connector" or N[b]["type"] == "connector":
                F("A8", f"connector {nid}")
            for hk in (c["sourceHook"], c["targetHook"]):
                if not (isinstance(hk, int) and 0 <= hk <= 15): F("A8", f"hook {nid}")
            if n["style"]["textColor"].lower() != "#1c1712": F("B1", f"connector label colour {nid}")
            if n["style"].get("stroke") in (None, "transparent") or n["style"].get("borderWidth", 0) < 3: F("B8", f"connector stroke/width {nid}")
    seen_ids = set()
    for i, s in enumerate(ST):
        if s["id"] in seen_ids: F("A10", f"duplicate step id {s['id']}")
        seen_ids.add(s["id"])
        if s["order"] != i: F("K8", "step order must be 0..n-1")
        if not (180 <= s["durationMs"] <= 10000 and 0 <= s["holdMs"] <= 30000 and s["easing"] in ("linear", "easeInOut", "smooth")): F("A10", s["id"])
        if len(s["label"]) > 20: Wn("D3", f"step label longer than 20 chars: {s['label']!r}")
        if re.match(r"^\s*\d+[\s.、)]", s["label"]): F("D3", f"step label starts with a number: {s['label']!r}")
        t = s["target"]
        if args.speaker_notes and t["sceneId"] != root:
            notes = s.get("speakerNotes", "")
            if len(re.sub(r"\s", "", notes)) < 60: F("P1", f"page step {s['id']} has no (or too short) speaker notes")
            elif re.search(r"[\w.+-]+@[\w-]+\.[\w.]+|\b\d{9}\b", notes): F("P3", f"speaker notes of {s['id']} look like they contain an e-mail or a student number")
        if t["sceneId"] not in S: F("A11", s["id"])
        if t["kind"] in ("enter-frame", "scene-overview"): F("H5", f"{t['kind']} must not be used ({s['id']})")
        if t["kind"] == "scene-point" and t.get("referenceViewport") != {"width": W, "height": H}: F("B5", f"referenceViewport {s['id']}")
    if doc["metadata"].get("aspectRatio") != "16:9": Wn("B4", "aspectRatio is not 16:9 (check pitch/zoom constants)")

    # ------------------------------------------------------------ H5 structure + cameras
    frames = {n["id"]: n for n in N.values() if n["type"] == "frame"}
    root_steps = [s for s in ST if s["target"]["sceneId"] == root]
    if len(root_steps) != len(frames): F("H5", f"root scene has {len(root_steps)} steps for {len(frames)} frames")
    for fid, fr in frames.items():
        cx, cy = fr["transform"]["x"] + fr["width"] / 2, fr["transform"]["y"] + fr["height"] / 2
        m = [s for s in root_steps if abs(s["target"]["point"]["x"] - cx) < 1 and abs(s["target"]["point"]["y"] - cy) < 1]
        if len(m) != 1: F("H5", f"frame {fid} has {len(m)} steps (must be exactly 1)")
        pages = [s for s in ST if s["target"]["sceneId"] == fr["frame"]["childSceneId"]]
        if len(pages) < 2: Wn("C5", f"{fr['frame']['childSceneId']} has only {len(pages)} page(s)")
    for s in ST:
        t = s["target"]
        if t["sceneId"] != root and t["kind"] == "scene-point":
            idx = round((t["point"]["x"] - W / 2) / PITCH)
            if abs(t["point"]["x"] - (idx * PITCH + W / 2)) > 0.5 or abs(t["point"]["y"] - (H / 2 - HEADROOM / 2)) > 0.5 or abs(t["zoom"] - H / (H + HEADROOM)) > 1e-6:
                F("B6", f"camera of {s['id']} does not follow the page formula")
    for sid, sc in S.items():
        if sid == root: continue
        for nid in sc["nodeIds"]:
            n = N[nid]
            if n["type"] == "connector": continue
            y, h = n["transform"]["y"], n["height"]
            if y < 0: F("B6", f"{nid} sits in the title-bar headroom (y<0)")
            if y + h > H + 1: F("B3", f"{nid} extends below the page ({y + h:.0f}>720)")
            x = n["transform"]["x"] % PITCH
            if x + n["width"] > W + 1: F("B3", f"{nid} extends past the page width")

    # ------------------------------------------------------------ B9 frame style (the legibility rule)
    for fid, fr in frames.items():
        st = fr["style"]
        std = {k: st.get(k) for k in STD_FRAME_STYLE}
        if {k: (v.lower() if isinstance(v, str) else v) for k, v in std.items()} != STD_FRAME_STYLE or set(st) - set(STD_FRAME_STYLE):
            F("B9", f"frame {fid} style differs from the standard (transparent fill/stroke, textColor #f2ede4, fontSize 22, radius 0): {st}")
        extra = set(fr["frame"]) - STD_FRAME_KEYS
        if extra: F("B9", f"frame {fid} sets {sorted(extra)}; do not set title colours/sizes (the title bar background is not under our control)")
        if "\n" in fr["text"] or len(fr["text"]) > 16: Wn("B9", f"frame title should be one short line (<=16 chars): {fr['text']!r}")

    # ------------------------------------------------------------ E10 contrast
    def parse(c):
        if c == "transparent": return None
        m = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)", c)
        if m: return (int(m[1]), int(m[2]), int(m[3]), float(m[4]) if m[4] else 1.0)
        h = c.lstrip("#")
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 1.0)

    def over(fg, bg):
        a = fg[3]
        return tuple(round(fg[i] * a + bg[i] * (1 - a)) for i in range(3)) + (1.0,)

    def lum(c):
        f = lambda v: (v / 255 / 12.92) if v / 255 <= 0.03928 else ((v / 255 + 0.055) / 1.055) ** 2.4
        return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])

    def cr(a, b):
        la, lb = sorted((lum(a), lum(b)), reverse=True)
        return (la + 0.05) / (lb + 0.05)

    canvas = parse("#151513")
    for nid, n in N.items():
        if n["type"] not in ("text", "shape", "frame"): continue
        st = n["style"]
        bg = canvas
        f = parse(st["fill"])
        if f: bg = over(f, canvas)
        r = cr(parse(st["textColor"]), bg)
        if r < 4.5: F("E10", f"contrast {r:.2f} on {nid}")
        if st["fontSize"] < 16: F("D4", f"font {st['fontSize']}px on {nid}")

    # ------------------------------------------------------------ pages: titles, fonts, bilingual layout
    pages = {}
    for sid, sc in S.items():
        if sid == root: continue
        for nid in sc["nodeIds"]:
            n = N[nid]
            if n["type"] == "connector": continue
            pages.setdefault((sid, int((n["transform"]["x"] + n["width"] / 2) // PITCH)), []).append(n)
    no_en_nodes = total_nodes = 0
    for (sid, idx), ns in sorted(pages.items()):
        tag = f"{sid}#p{idx + 1}"
        title = [n for n in ns if n["type"] == "text" and n["style"]["fontSize"] >= 40 and n["transform"]["y"] < 120]
        if len(title) != 1: Wn("D2", f"{tag}: expected one page title (font >= 40, y < 120), found {len(title)}"); continue
        t = title[0]
        if "$" in t["text"]: F("D2", f"{tag}: math in the page title (KaTeX line height makes it collide with the subtitle): {t['text']!r}")
        if not (6 <= len(re.sub(r"\s", "", t["text"])) <= 26): Wn("D2", f"{tag}: title length: {t['text']!r}")
        if args.level:
            max_blocks, max_chars = LEVEL_LIMITS[args.level]
            blocks = sum(n["text"].count("$$") // 2 for n in ns if n["type"] in ("text", "shape"))
            if blocks > max_blocks: Wn("Q1", f"{tag}: {blocks} display formulas; level {args.level} allows {max_blocks}")
            body = sum(len(CJK.findall(re.sub(r"\$[^$]*\$", "", n["text"]))) for n in ns
                       if n["type"] in ("text", "shape") and n["style"]["fontSize"] < 40 and n["transform"]["y"] >= 130)
            if max_chars and body > max_chars: Wn("Q2", f"{tag}: {body} Chinese body characters; level {args.level} allows {max_chars}")
        if not args.monolingual:
            sub = [n for n in ns if n["type"] == "text" and n["style"]["fontSize"] < 40 and n["transform"]["y"] < 130 and n is not t
                   and not CJK.search(n["text"]) and en_words(n["text"]) >= 3]
            if not sub: F("L1", f"{tag}: no English subtitle under the page title")
        for n in ns:
            if n["type"] not in ("text", "shape") or n is t: continue
            fs = n["style"]["fontSize"]
            if fs < 22 and CJK.search(n["text"]): Wn("D4", f"{tag}: body text {fs}px < 22 ({n['id']})")
            if not args.monolingual and len(CJK.findall(re.sub(r"\$[^$]*\$", "", n["text"]))) >= 8:
                total_nodes += 1
                if en_words(n["text"]) < 3:
                    no_en_nodes += 1
                    Wn("L1", f"{tag}: no English line in {n['id']}: {n['text'][:24]!r}")
                else:
                    if "*" not in n["text"]:
                        Wn("L2", f"{tag}: English line is not italic (*...*) in {n['id']}")
                    cjk = len(CJK.findall(MATH.sub("", n["text"])))
                    if cjk >= 12 and en_words(n["text"]) < 0.3 * cjk:
                        Wn("L3", f"{tag}: English is a keyword fragment, not a full translation ({en_words(n['text'])} words for {cjk} Chinese chars) in {n['id']}")
    if not args.monolingual and total_nodes and no_en_nodes / total_nodes > 0.1:
        F("L1", f"{no_en_nodes}/{total_nodes} text blocks have no English line (more than 10%)")
    alts = {}
    for nid, n in N.items():
        if n["type"] == "image":
            if len(n["image"]["alt"].strip()) < 12: F("G14", f"image alt too short: {nid}")
            if n["image"].get("fit") != "contain": F("G14", f"image fit must be 'contain': {nid}")
            if len(n["image"]["src"]) > 340_000: F("G13", f"embedded SVG too large: {nid}")
            alts.setdefault(n["image"]["alt"].strip(), []).append(nid)
    for a, ids in alts.items():
        if len(ids) > 1 and len({N[i]["image"]["src"] for i in ids}) > 1:
            Wn("G14", f"{len(ids)} different images share one generic alt text {a[:40]!r}: describe what each one shows")

    # ------------------------------------------------------------ G3 formulas must be LaTeX ($...$), not Unicode look-alikes
    UMATH = re.compile("[⁰-₟ᵀᵢⱼ̂‖Σ∑∫∂∇]")   # sub/superscripts, T, hat, double bar, Sigma, integral, partial, nabla
    for (sid, idx), ns in pages.items():
        hits = []
        for n in ns:
            if n["type"] in ("text", "shape") and n["style"].get("fontSize", 0) < 40:
                hits += UMATH.findall(re.sub(r"\$\$.*?\$\$|\$[^$\n]*\$", "", n.get("text", ""), flags=re.S))
        if hits:
            Wn("G3", f"{sid}#p{idx}: {len(hits)} Unicode math symbol(s) outside $...$ (e.g. {''.join(sorted(set(hits)))[:12]!r}): write formulas in LaTeX, vectors \mathbf{{}}, norms \|\cdot\| (AUDIT_CHECKLIST G3, G4)")

    # ------------------------------------------------------------ N3 results that appear without a derivation
    page_text = {}
    for (sid, idx), ns in pages.items():
        page_text[(sid, idx)] = "\n".join(n.get("text", "") for n in ns if n["type"] in ("text", "shape"))
    lines = [ln for txt in page_text.values() for ln in txt.split("\n")]
    derived = set()
    for ln in lines:
        if DERIV.search(ln):
            derived.update(v.lstrip("-") for v in NUM3.findall(ln))
    for key, txt in sorted(page_text.items()):
        if COMPUTED.search(txt): continue
        for v in sorted(set(x.lstrip("-") for x in NUM3.findall(txt))):
            if v not in derived:
                Wn("N3", f"{key[0]}#p{key[1] + 1}: {v} appears with no derivation line anywhere in the deck (write the steps, or mark the page 〔程式計算〕)")

    # ------------------------------------------------------------ S/V/P2/R quality checks (NARRATIVE.md, VISUAL guide 1.5)
    from collections import Counter
    FOOT = re.compile(r"^\s*(KP|U)\d+\s*[·•]")
    GENERIC = ("備註不代替正文", "本頁英文與中文對應", "這張視覺休息頁", "讀者應能指出本頁的輸入條件")
    PREV_W = ("上一頁", "前一頁", "前面", "剛才", "回顧", "承接", "上一步")
    NEXT_W = ("下一頁", "接下來", "接著", "下一步", "下一個", "預告", "之後", "下一單元")

    def body_nodes(ns):
        return [n for n in ns if n["type"] in ("text", "shape") and n.get("text", "").strip()
                and n["transform"]["y"] >= 130 and not FOOT.match(n["text"])]

    def page_of(t):
        tg = t["target"]
        return tg["sceneId"], round((tg["point"]["x"] - W / 2) / PITCH)

    content_steps = [t for t in ST if t["target"]["sceneId"] != root]
    label_count = Counter(t["label"] for t in content_steps)
    for lab, c in label_count.items():
        if c > 2: Wn("S2", f"step label {lab!r} appears {c} times: merge or retitle (filler pages)")
    note_keys = Counter(re.sub(r"\s", "", t.get("speakerNotes", ""))[:80] for t in content_steps if t.get("speakerNotes"))
    for key, c in note_keys.items():
        if c > 1: Wn("S3", f"{c} pages share the same speaker notes ({key[:30]!r}...): notes must be specific to the page")
    prev_scene, run, run_sig = None, 0, None
    for i, t in enumerate(content_steps):
        key = page_of(t)
        ns = pages.get(key, [])
        tag = f"{key[0]}#p{key[1] + 1}"
        body = body_nodes(ns)
        chars = sum(len(re.sub(r"[\s$]", "", n["text"])) for n in body)
        ids = {n["id"] for n in ns}
        has_img = any(n["type"] == "image" for n in ns)
        has_conn = any(N[j]["type"] == "connector" and N[j]["connector"]["sourceNodeId"] in ids for j in S[key[0]]["nodeIds"])
        if chars < 100 and not has_img and not has_conn:
            F("S1", f"{tag}: empty page ({chars} body characters, no figure or connector): {t['label']!r}")
        notes = t.get("speakerNotes", "")
        if notes:
            if any(g in notes for g in GENERIC): Wn("S3", f"{tag}: speaker notes contain boilerplate text")
            ptxt = "".join(n["text"] for n in ns if n["type"] in ("text", "shape"))
            bigrams = lambda x: {x[k:k + 2] for k in range(len(x) - 1) if CJK.match(x[k]) and CJK.match(x[k + 1])}
            if len(bigrams(notes) & bigrams(ptxt)) < 6: Wn("P2", f"{tag}: speaker notes share almost no wording with the page; they look generic")
        sig = tuple(sorted((n["type"], round((n["transform"]["x"] % PITCH) / 60), round(n["transform"]["y"] / 60), round(n["width"] / 60), round(n["height"] / 60))
                           for n in ns if not (n["transform"]["y"] < 130)))
        if key[0] == prev_scene and sig == run_sig:
            run += 1
            if run == 4: Wn("V1", f"{tag}: 4 consecutive pages share the same layout; vary the layout (VISUAL guide 3.4)")
        else:
            run = 1
        prev_scene, run_sig = key[0], sig
        if args.narrative and i > 0 and not t["label"].endswith("(續)") and not t["label"].endswith("(續)"):
            if not any("bridge" in n.get("name", "").lower() for n in ns):
                F("R1", f"{tag}: no bridge node (name containing 'bridge') linking this page to the previous one: {t['label']!r}")
            if notes and not (any(w in notes for w in PREV_W) and any(w in notes for w in NEXT_W)):
                Wn("R3", f"{tag}: speaker notes should say how this page follows the previous one and leads to the next")
    for fid, fr in frames.items():
        sc = S.get(fr["frame"]["childSceneId"])
        if sc and sc["name"] != fr["text"] and sc["name"].startswith(fr["text"]) and len(sc["name"]) > len(fr["text"]):
            F("S4", f"frame title {fr['text']!r} is a truncated copy of {sc['name']!r}: write a short title instead of cutting")
    if args.outline:
        cur = None
        for t in content_steps:
            key = page_of(t)
            if key[0] != cur:
                cur = key[0]
                print(f"\n== {S[cur]['name']}")
            br = [n["text"].split("\n")[0] for n in pages.get(key, []) if "bridge" in n.get("name", "").lower()]
            print(f"  {t['label']}" + (f"   <- {br[0][:60]}" if br else ""))
        print()

    # ------------------------------------------------------------ U1 pages per knowledge point, O2 originality
    per_scene = Counter(sid for (sid, _idx) in pages)
    for sid, c in per_scene.items():
        if c > args.max_pages_per_kp:
            F("U1", f"{S[sid]['name']!r} has {c} pages; a knowledge point may use at most {args.max_pages_per_kp} (move detail to the lecture)")
    if args.source:
        stream = lambda t: "".join(CJK.findall(re.sub(r"\$[^$]*\$", "", t)))
        grams = set()
        for sp in args.source:
            st = stream(open(sp, encoding="utf-8").read())
            grams |= {st[i:i + 14] for i in range(len(st) - 13)}
        flagged = 0
        for (sid, idx), ns in sorted(pages.items()):
            pt = stream("".join(n.get("text", "") for n in ns if n["type"] in ("text", "shape")))
            hits = sum(1 for i in range(len(pt) - 13) if pt[i:i + 14] in grams)
            if hits >= 10:
                flagged += 1
                Wn("O2", f"{sid}#p{idx + 1}: {hits} positions repeat the source verbatim; rewrite in your own words")
        if flagged > 3: Wn("O2", f"{flagged} pages repeat the source verbatim: the deck is not freshly written")

    # ------------------------------------------------------------ T1 class-time estimate (LEVELS.md section 7.4)
    if args.minutes:
        core = ext = 0
        total = 0.0
        for t in ST:
            tg = t["target"]
            if tg["sceneId"] == root: continue
            idx = int((tg["point"]["x"]) // PITCH)
            ns = pages.get((tg["sceneId"], idx), [])
            if t["label"].startswith(("延伸:", "延伸:")):
                ext += 1
                continue
            text = "\n".join(n.get("text", "") for n in ns if n["type"] in ("text", "shape"))
            heavy = any(n["type"] == "image" for n in ns) or t["label"].startswith("練習") or text.count("$") >= 6
            total += 4.0 if heavy else 2.5
            core += 1
        per = f"; per-KP budget {args.minutes / args.kps:.1f} min ({args.kps} KPs)" if args.kps else ""
        print(f"time estimate: main line {core} pages ~{total:.0f} min, extension pages {ext} (not counted); budget {args.minutes:.0f} min{per}")
        if ext > core: Wn("T2", f"{ext} extension pages exceed the {core} main-line pages: merge extension content into whole-idea pages (LEVELS.md 7.3)")
        if total > args.minutes: Wn("T1", f"main line ~{total:.0f} min exceeds the {args.minutes:.0f} min budget: move pages to the extension group (label starts with 延伸:) or trim")

    # ------------------------------------------------------------ lecture coverage: O1 figures, N6 formulas and numbers
    if args.lecture:
        figs, formulas, numbers = lecture_inventory(args.lecture)
        names = " ".join(n.get("name", "") + " " + n.get("image", {}).get("alt", "") for n in N.values() if n["type"] == "image")
        for f in figs:
            if f in args.exclude_fig: continue
            if f"fig:{f}" not in names:
                F("O1", f"lecture figure {f} is not used (redraw it with the same data and name the image node 'fig:{f}', "
                        f"or get the teacher's OK and pass --exclude-fig {f})")
        alltex = norm_tex("\n".join(page_text.values()))
        miss = [raw for raw, p in formulas if p not in alltex]
        for raw in miss:
            Wn("N6", f"lecture formula not on any slide: {raw[:70]!r}")
        plain = "\n".join(page_text.values())
        missing_nums = [v for v in numbers if not re.search(r"(?<![\d.])" + re.escape(v) + r"(?!\d)", plain)]
        if missing_nums:
            Wn("N6", f"{len(missing_nums)}/{len(numbers)} numbers of the lecture are not on any slide: {', '.join(missing_nums[:30])}"
                     + (" ..." if len(missing_nums) > 30 else ""))
        print(f"lecture: {args.lecture} | figures {len(figs)} (missing {sum(1 for f in figs if f not in args.exclude_fig and f'fig:{f}' not in names)}, "
              f"excluded {len(args.exclude_fig)})  formulas {len(formulas)} (missing {len(miss)})  numbers {len(numbers)} (missing {len(missing_nums)})")

    print(f"audit_deck: {args.deck}  | scenes {len(S)}  nodes {len(N)}  steps {len(ST)}  frames {len(frames)}  pages {len(pages)}  "
          f"{'monolingual' if args.monolingual else 'bilingual'}")
    print(f"FAIL {len(fails)}")
    for x in fails: print("  FAIL", x)
    print(f"WARN {len(warns)}")
    for x in warns[:40]: print("  WARN", x)
    if len(warns) > 40: print(f"  ... {len(warns) - 40} more")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
