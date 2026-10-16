"""jbd_figure.py -- helper for drawing precise, zoom-safe figures for JianBauDau page specs.

Usage pattern
-------------
    from jbd_figure import *
    use_jbd_style()
    fig, ax = new_figure(560, 560)            # node size in JianBauDau px
    ...draw with matplotlib (analytic coordinates, mathtext labels)...
    node = image_node("hp1-fig", "示意圖", 60, 160, 560, 560, svg_data_uri(fig),
                      alt="牆 x1+x2-0.5=0 與法向量 w，點 A 在正側、點 B 在負側")
    page.nodes.append(node)                   # then json.dump the page spec as usual

Design rules baked in
---------------------
* 1 inch == 100 node px, so figsize == node size / 100 and the SVG keeps the node's aspect ratio.
  Therefore  font_pt = font_px * 0.72  (see px_to_pt).
* Transparent background, palette colours from the guide, mathtext in Computer Modern
  (looks like LaTeX, needs no TeX installation).
* svg.fonttype = "path": glyphs are outlines, so the viewer needs no fonts (CJK included) and
  stays crisp at any camera zoom.
* NEVER use bbox_inches="tight": it changes the aspect ratio and breaks the node-box mapping.
"""
from __future__ import annotations

import base64
import io
import re
import xml.etree.ElementTree as ET

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# ---- fixed colour semantics (see guide, section 3) -------------------------------------------
PALETTE = {
    "positive": "#d97757",   # 正側 / 主角 / 重點
    "negative": "#6a9fd6",   # 負側 / 對照組
    "boundary": "#e0995f",   # 邊界 / 牆 / 閾值
    "vector": "#5fb8a8",     # 向量 / 方向 / 切線
    "warning": "#e07a70",    # 易錯 / 反例
    "ok": "#7dbb8c",         # 成立 / 不變
    "text": "#f2ede4",
    "muted": "#b7b0a5",
}


def px_to_pt(px: float) -> float:
    """Font size in node px -> matplotlib points (valid because 1 inch == 100 node px)."""
    return px * 0.72


def use_jbd_style(base_font_px: float = 20) -> None:
    plt.rcParams.update({
        "svg.fonttype": "path",
        "mathtext.fontset": "cm",
        "font.size": px_to_pt(base_font_px),
        "axes.facecolor": "none",
        "figure.facecolor": "none",
        "savefig.transparent": True,
        "text.color": PALETTE["text"],
        "axes.labelcolor": PALETTE["text"],
        "axes.edgecolor": PALETTE["muted"],
        "xtick.color": PALETTE["muted"],
        "ytick.color": PALETTE["muted"],
        "grid.color": PALETTE["muted"],
        "grid.alpha": 0.25,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 1.6,
        "lines.linewidth": 3,
    })


def new_figure(node_w: float, node_h: float, margins_px=(96, 76, 24, 24)):
    """Figure whose size maps 1:1 onto the image node.

    margins_px = (left, bottom, right, top) in node px. Axis labels / tick labels live in these
    margins, so keep them generous (>= 90 left, >= 70 bottom when you have axis labels).
    """
    fig = plt.figure(figsize=(node_w / 100.0, node_h / 100.0))
    l, b, r, t = margins_px
    ax = fig.add_axes([l / node_w, b / node_h, 1 - (l + r) / node_w, 1 - (b + t) / node_h])
    return fig, ax


def check_not_clipped(fig, tol_px: float = 1.0) -> list[str]:
    """True-geometry check: every artist (labels, legend, annotations) must lie inside the figure."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bb = fig.get_tightbbox(renderer)               # inches
    W, H = fig.get_size_inches()
    tol = tol_px / 100.0
    problems = []
    if bb.x0 < -tol: problems.append(f"content sticks out on the LEFT by {(-bb.x0)*100:.0f}px (increase left margin)")
    if bb.y0 < -tol: problems.append(f"content sticks out at the BOTTOM by {(-bb.y0)*100:.0f}px (increase bottom margin)")
    if bb.x1 > W + tol: problems.append(f"content sticks out on the RIGHT by {(bb.x1-W)*100:.0f}px")
    if bb.y1 > H + tol: problems.append(f"content sticks out at the TOP by {(bb.y1-H)*100:.0f}px")
    return problems


def svg_text(fig) -> str:
    buf = io.StringIO()
    fig.savefig(buf, format="svg")
    plt.close(fig)
    return buf.getvalue()


def check_svg(svg: str, max_bytes: int = 250_000) -> list[str]:
    """Cheap self-checks. Returns a list of problems (empty == OK)."""
    problems: list[str] = []
    try:
        root = ET.fromstring(svg)
    except ET.ParseError as exc:  # pragma: no cover
        return [f"SVG is not well-formed: {exc}"]
    if len(svg.encode("utf-8")) > max_bytes:
        problems.append(f"SVG is {len(svg.encode('utf-8'))} bytes (> {max_bytes}); simplify or rasterize dense layers")
    if re.search(r"(href|src)=\"https?://", svg):
        problems.append("SVG references an external resource")
    if "<text" in svg:
        problems.append("SVG contains live <text>; set svg.fonttype='path'")
    if root.tag.split("}")[-1] != "svg":
        problems.append("root element is not <svg>")
    return problems


def svg_data_uri(fig, max_bytes: int = 250_000) -> str:
    clipped = check_not_clipped(fig)
    if clipped:
        raise ValueError("; ".join(clipped))
    svg = svg_text(fig)
    problems = check_svg(svg, max_bytes)
    if problems:
        raise ValueError("; ".join(problems))
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


def image_node(prefix_key: str, name: str, x: float, y: float, w: float, h: float,
               data_uri: str, alt: str, z: int = 2) -> dict:
    if not alt.strip():
        raise ValueError("alt text is required (describe what the figure shows)")
    return {
        "id": prefix_key,
        "type": "image",
        "name": name,
        "sceneId": "placeholder",
        "transform": {"x": x, "y": y, "scaleX": 1, "scaleY": 1, "rotation": 0},
        "width": w,
        "height": h,
        "zIndex": z,
        "locked": False,
        "style": {"fill": "transparent", "stroke": "transparent", "textColor": "transparent",
                  "fontSize": 1, "radius": 0},
        "text": alt,
        "image": {"src": data_uri, "alt": alt, "fit": "contain"},
    }


def data_to_node(fig, ax, node_x: float, node_y: float, x: float, y: float) -> tuple[float, float]:
    """Map a point in DATA coordinates to page (node) coordinates for an image node placed at
    (node_x, node_y). Use it to overlay native text / connector endpoints exactly on a figure
    feature (e.g. a Chinese caption next to a plotted point).

    Valid because figsize == node size / 100 and fig.dpi == 100, so 1 display px == 1 node px.
    Call it AFTER the axes limits are final (after set_xlim / set_ylim / set_aspect).
    """
    fig.canvas.draw()
    dx, dy = ax.transData.transform((x, y))
    H = fig.get_size_inches()[1] * 100.0
    return node_x + dx, node_y + (H - dy)
