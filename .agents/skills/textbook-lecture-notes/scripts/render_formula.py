"""把 LaTeX 公式用 KaTeX 渲染成 PNG(透明底),供講義或投影片使用。

用法:
  python render_formula.py --latex "\\mathbf{w}^\\top\\mathbf{x}+b=0" --out assets/figures/formula_plane.png
  python render_formula.py --latex "x+y" --inline --out out.png
  python render_formula.py --batch formulas.json      # [{"latex": "...", "out": "...", "display": true}, ...]

需求:
  pip install -r requirements-lecture.txt
  python -m playwright install chromium
KaTeX 由 CDN 載入,渲染時需要網路。

為什麼不用 Canvas:幾何、函數、統計圖請用 Matplotlib(座標由解析式計算,比例與軸線更容易精準);
本工具只負責「公式本身」的排版。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

KATEX_VERSION = "0.16.11"
CSS_URL = f"https://cdn.jsdelivr.net/npm/katex@{KATEX_VERSION}/dist/katex.min.css"
JS_URL = f"https://cdn.jsdelivr.net/npm/katex@{KATEX_VERSION}/dist/katex.min.js"


def page_html(latex: str, display: bool, font_px: int, color: str) -> str:
    # json.dumps 產生安全的 JS 字串字面值(處理反斜線與引號)
    return f"""<!doctype html>
<html><head><meta charset="utf-8">
<link rel="stylesheet" href="{CSS_URL}">
<style>
  body {{ margin: 0; background: transparent; }}
  #f {{ display: inline-block; padding: 6px 10px; font-size: {font_px}px; color: {color}; }}
</style>
</head><body>
<span id="f"></span>
<script src="{JS_URL}"></script>
<script>
  katex.render({json.dumps(latex)}, document.getElementById("f"),
               {{ displayMode: {str(display).lower()}, throwOnError: true }});
</script>
</body></html>"""


def render_all(items: list[dict], font_px: int, color: str, scale: float) -> None:
    errors: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(device_scale_factor=scale)
        page = context.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        for item in items:
            latex, out = item["latex"], Path(item["out"])
            display = item.get("display", True)
            errors.clear()
            page.set_content(page_html(latex, display, font_px, color), wait_until="networkidle")
            page.evaluate("document.fonts.ready")
            if errors:
                browser.close()
                raise RuntimeError(f"KaTeX 無法渲染 {latex!r}:{errors[0]}")
            out.parent.mkdir(parents=True, exist_ok=True)
            page.locator("#f").screenshot(path=str(out), omit_background=True)
            print(f"[完成] {out}")
        browser.close()


def main() -> int:
    ap = argparse.ArgumentParser(description="KaTeX 公式 → PNG")
    ap.add_argument("--latex", help="單一公式(LaTeX 字串,不含外層 $)")
    ap.add_argument("--out", help="輸出 PNG 路徑(與 --latex 搭配)")
    ap.add_argument("--inline", action="store_true", help="行內排版(預設為區塊)")
    ap.add_argument("--batch", help="JSON 檔,內容為 [{latex, out, display?}, ...]")
    ap.add_argument("--font-px", type=int, default=32, help="字級(px),預設 32")
    ap.add_argument("--color", default="#171918", help="字色,預設 #171918")
    ap.add_argument("--scale", type=float, default=2.0, help="解析度倍率,預設 2")
    args = ap.parse_args()

    if args.batch:
        items = json.loads(Path(args.batch).read_text(encoding="utf-8"))
    elif args.latex and args.out:
        items = [{"latex": args.latex, "out": args.out, "display": not args.inline}]
    else:
        ap.error("請提供 --latex 與 --out,或 --batch")

    render_all(items, args.font_px, args.color, args.scale)
    return 0


if __name__ == "__main__":
    sys.exit(main())
