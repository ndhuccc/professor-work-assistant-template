#!/usr/bin/env python3
"""preview_deck.py -- APPROXIMATE render of a JianBauDau deck: one PNG per page plus overflow report and contact sheets.

    py .agents/skills/view-from-text/tools/preview_deck.py slides/lec03.jbd.json --out preview_lec03
    py .agents/skills/view-from-text/tools/preview_deck.py draft.jbd.json --out prev --sheets

Text is laid out with the browser (Microsoft Edge through Playwright, or bundled Chromium) and formulas with KaTeX from a CDN
(needs network). It is NOT the JianBauDau renderer: use it to catch text overflow, overlaps, tiny fonts and legends that
cover curves BEFORE the teacher opens the file. Text cards are top-aligned here; JianBauDau may centre them vertically.
Writes <out>/overflow.json and <out>/slack.json (how much spare height every text box has). Exit code 1 on overflow.
Needs:  pip install playwright  (and Pillow for --sheets).
"""
import argparse
import html
import json
import math
import os
import re
import sys

from playwright.sync_api import sync_playwright

PITCH = 1440
CSS = """
html,body{margin:0;background:#151513;}
#page{position:relative;width:1280px;height:720px;overflow:hidden;background:#151513;
  font-family:"Avenir Next","Noto Sans TC","Microsoft JhengHei","Segoe UI",sans-serif;}
.n{position:absolute;box-sizing:border-box;padding:14px 16px;overflow:visible;word-break:break-word;}
.n.plain{padding:0;}
.n b{font-weight:800}
svg.lines{position:absolute;left:0;top:0;width:1280px;height:720px;pointer-events:none;}
.lbl{position:absolute;background:rgba(255,255,255,.94);color:#1c1712;padding:2px 10px;border-radius:8px;font-size:20px;transform:translate(-50%,-50%);white-space:nowrap;}
img.im{position:absolute;object-fit:contain;}
"""
# the doctype matters: KaTeX refuses to run in quirks mode
HEAD = ("<!doctype html><html><head><meta charset='utf-8'><link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css'>"
        f"<style>{CSS}</style></head><body><div id='page'>")
TAIL = ("</div><script src='https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js'></script>"
        "<script src='https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js'></script>"
        "<script>renderMathInElement(document.getElementById('page'),"
        "{delimiters:[{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}],throwOnError:false});"
        "window.__done=true;</script></body></html>")


def md(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t, flags=re.S)
    t = re.sub(r"(?<![*\w])\*(?!\*)([^*\n]+?)\*(?![*\w])", r"<i>\1</i>", t)
    return "".join(p if p.startswith("$$") else p.replace("\n", "<br>") for p in re.split(r"(\$\$.*?\$\$)", t, flags=re.S))


def hook_point(n, hook, ox):
    x, y, w, h = n["transform"]["x"] - ox, n["transform"]["y"], n["width"], n["height"]
    a = hook * math.pi / 8
    dx, dy = math.sin(a), -math.cos(a)
    t = min((w / 2) / abs(dx) if abs(dx) > 1e-6 else 1e9, (h / 2) / abs(dy) if abs(dy) > 1e-6 else 1e9)
    return x + w / 2 + dx * t, y + h / 2 + dy * t


def page_html(N, ids, ox):
    items, svg, labels = [], [], []
    for nid in ids:
        n = N[nid]
        x, y, w, h = n["transform"]["x"] - ox, n["transform"]["y"], n["width"], n["height"]
        st = n["style"]
        if n["type"] in ("text", "shape"):
            bw = st.get("borderWidth", 0)
            border = f"border:{bw}px solid {st['stroke']};" if bw else ""
            cls = "n plain" if st["fill"] == "transparent" and not bw else "n"
            items.append(f"<div class='{cls}' data-id='{nid}' style='left:{x}px;top:{y}px;width:{w}px;height:{h}px;background:{st['fill']};{border}"
                         f"border-radius:{st.get('radius', 0)}px;color:{st['textColor']};font-size:{st['fontSize']}px;font-weight:{st.get('fontWeight', 400)};"
                         f"text-align:{st.get('textAlign', 'left')};line-height:{st.get('lineHeight', 1.4)};'>{md(n['text'])}</div>")
        elif n["type"] == "image":
            items.append(f"<img class='im' src='{n['image']['src']}' style='left:{x}px;top:{y}px;width:{w}px;height:{h}px'>")
        elif n["type"] == "connector":
            c = n["connector"]
            x1, y1 = hook_point(N[c["sourceNodeId"]], c["sourceHook"], ox)
            x2, y2 = hook_point(N[c["targetNodeId"]], c["targetHook"], ox)
            svg.append(f"<line x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}' stroke='{st['stroke']}' stroke-width='3' marker-end='url(#ah)'/>")
            if c.get("label"):
                labels.append(f"<div class='lbl' style='left:{(x1 + x2) / 2}px;top:{(y1 + y2) / 2 - 18}px'>{html.escape(c['label']['text'])}</div>")
    defs = "<defs><marker id='ah' markerWidth='8' markerHeight='8' refX='7' refY='4' orient='auto'><path d='M0,0 L8,4 L0,8 z' fill='#6a9fd6'/></marker></defs>"
    return HEAD + "".join(items) + f"<svg class='lines'>{defs}{''.join(svg)}</svg>" + "".join(labels) + TAIL


MEASURE = """() => [...document.querySelectorAll('.n')].map(e => {
  const r = document.createRange(); r.selectNodeContents(e); const b = r.getBoundingClientRect(); const cs = getComputedStyle(e);
  const inner = e.clientHeight - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom);
  return {id: e.dataset.id, h: Math.round(e.clientHeight), content: Math.round(b.height), slack: Math.round(inner - b.height),
          overflowH: e.scrollHeight > e.clientHeight + 3, overflowW: e.scrollWidth > e.clientWidth + 3};
})"""


def sheets(outdir):
    from PIL import Image
    files = sorted([f for f in os.listdir(outdir) if re.match(r".+_p\d+\.png$", f)], key=lambda f: (f.rsplit("_p", 1)[0], int(re.search(r"_p(\d+)", f).group(1))))
    for k in range(0, len(files), 6):
        sheet = Image.new("RGB", (1290, 3 * 370), "#333")
        for j, f in enumerate(files[k:k + 6]):
            sheet.paste(Image.open(os.path.join(outdir, f)).resize((640, 360)), ((j % 2) * 650, (j // 2) * 370))
        out = os.path.join(outdir, f"sheet_{k // 6 + 1}.png")
        sheet.save(out)
        print("contact sheet:", out, [f[:-4] for f in files[k:k + 6]])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("--out", default="deck_preview")
    ap.add_argument("--sheets", action="store_true", help="also write 2x3 contact sheets (needs Pillow)")
    args = ap.parse_args()
    doc = json.load(open(args.deck, encoding="utf-8"))
    S, N = doc["scenes"], doc["nodes"]
    os.makedirs(args.out, exist_ok=True)
    overflow, slack, errors = {}, {}, []
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="msedge")
        except Exception:
            browser = p.chromium.launch()
        pg = browser.new_page(viewport={"width": 1280, "height": 720})
        pg.on("pageerror", lambda e: errors.append(str(e)[:100]))
        for sid, sc in S.items():
            if sid == doc["rootSceneId"]:
                continue
            groups = {}
            for nid in sc["nodeIds"]:
                n = N[nid]
                key = N[n["connector"]["sourceNodeId"]] if n["type"] == "connector" else n
                idx = int((key["transform"]["x"] + (0 if n["type"] == "connector" else key["width"] / 2)) // PITCH)
                groups.setdefault(idx, []).append(nid)
            for idx, ids in sorted(groups.items()):
                pg.set_content(page_html(N, ids, idx * PITCH), wait_until="load")
                try:
                    pg.wait_for_function("window.__done===true", timeout=20000)
                except Exception:
                    errors.append(f"KaTeX did not finish on {sid}#{idx + 1} (network?)")
                pg.wait_for_timeout(200)
                name = f"{sid}_p{idx + 1}"
                meas = pg.evaluate(MEASURE)
                slack[name] = meas
                bad = [m for m in meas if m["overflowH"] or m["overflowW"]]
                if bad:
                    overflow[name] = bad
                pg.screenshot(path=os.path.join(args.out, name + ".png"))
        browser.close()
    json.dump(slack, open(os.path.join(args.out, "slack.json"), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(overflow, open(os.path.join(args.out, "overflow.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"pages rendered: {len(slack)}  -> {args.out}")
    print(f"overflowing boxes: {sum(len(v) for v in overflow.values())}")
    for k, v in overflow.items():
        print("  ", k, [(m['id'].rsplit('-', 1)[-1], m['content'], m['h']) for m in v])
    if errors:
        print("page errors:", errors[:3])
    if args.sheets:
        sheets(args.out)
    return 1 if overflow else 0


if __name__ == "__main__":
    sys.exit(main())
