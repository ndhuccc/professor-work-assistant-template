"""Deck kit (shared infrastructure): one unit per KP, flow layout + hand-placed native-node pages. See README.md.
Reads figs.json / need.json from the current directory (DECK_WORK)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.abspath(os.environ.get("DECK_WORK", os.getcwd()))   # holds figs.json / need.json (run from the work dir)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))   # view-from-text/ (jbd_figure.py)
from flow import Card, Col, Fig, Flow, Row, Table  # noqa: E402

PFX = os.environ.get("DECK_PFX", "lec03kp00")   # node-id prefix, unique per KP: set env DECK_PFX
W, H = 1280, 720
HEADROOM, GAP = 100, 160
ZOOM, PITCH = H / (H + HEADROOM), W + GAP
TEXT, MUTED = "#f2ede4", "#b7b0a5"
MAIN, REF, EDGE, AUX, WARN, OK = "#d97757", "#6a9fd6", "#e0995f", "#5fb8a8", "#e07a70", "#7dbb8c"
DARK = "#1c1712"
RGB = {MAIN: (217, 119, 87), REF: (106, 159, 214), EDGE: (224, 153, 95), AUX: (95, 184, 168), WARN: (224, 122, 112), OK: (125, 187, 140)}
NEUTRAL_FILL, NEUTRAL_STROKE = "rgba(245,241,233,0.05)", "rgba(245,241,233,0.20)"
with open(os.path.join(WORK, "figs.json"), encoding="utf-8") as fh:
    FIGS = json.load(fh)
NEED = {}
if os.path.exists(os.path.join(WORK, "need.json")):
    with open(os.path.join(WORK, "need.json"), encoding="utf-8") as fh:
        NEED = json.load(fh)
scenes, nodes, steps = {}, {}, []
D = sys.modules[__name__]


def role(c):
    r, g, b = RGB[c]
    return f"rgba({r},{g},{b},0.12)", f"rgba({r},{g},{b},0.65)"


def en(t):
    return "\n".join("*" + ln + "*" if ln.strip() else ln for ln in t.split("\n"))


def T(*lines):
    return "\n".join(lines)


class Page:
    def __init__(self, unit, idx, label, title, en_title):
        self.u, self.idx, self.label = unit, idx, label
        self.ox, self.n = idx * PITCH, 0
        self.text(60, 26, 1160, 60, title, size=42, weight=700, lh=1.25, nid=f"{PFX}-{unit.uid}-p{idx + 1}-title")
        self.text(60, 88, 1160, 38, en_title, size=22, color=MUTED, lh=1.2, nid=f"{PFX}-{unit.uid}-p{idx + 1}-sub")

    def _add(self, node):
        assert node["id"] not in nodes, node["id"]
        nodes[node["id"]] = node
        scenes[self.u.sid]["nodeIds"].append(node["id"])
        return node["id"]

    def text(self, x, y, w, h, text, size=22, color=TEXT, weight=400, align="left", fill="transparent", stroke="transparent",
             bw=0, radius=0, lh=1.4, shape=False, nid=None):
        h = max(h, NEED.get(nid, 0))
        style = {"fill": fill, "stroke": stroke, "textColor": color, "fontSize": size, "radius": radius, "fontWeight": weight,
                 "textAlign": align, "lineHeight": lh}
        if bw:
            style["borderStyle"] = "solid"
            style["borderWidth"] = bw
        node = {"id": nid, "type": "shape" if shape else "text", "name": nid.split("-", 1)[1], "sceneId": self.u.sid,
                "transform": {"x": self.ox + x, "y": y, "scaleX": 1, "scaleY": 1, "rotation": 0}, "width": w, "height": h,
                "zIndex": 2, "locked": False, "style": style, "text": text}
        if shape:
            node["shapeKind"] = "rectangle"
        return self._add(node)

    def figure(self, fig_id, x, y, w=None):
        from jbd_figure import image_node
        f = FIGS[fig_id]
        fw, fh = f["w"], f["h"]
        if w and w != fw:
            fh, fw = fh * w / fw, w
        self.n += 1
        n = image_node(f"{PFX}-{self.u.uid}-p{self.idx + 1}-fig{self.n}", f"fig:{fig_id}", self.ox + x, y, fw, fh, f["uri"], f["alt"])
        n["sceneId"] = self.u.sid
        self._add(n)
        return y + fh

    def conn(self, src, sh, dst, th, label=None, offset="above"):
        self.n += 1
        nid = f"{PFX}-{self.u.uid}-p{self.idx + 1}-conn{self.n}"
        c = {"sourceNodeId": src, "sourceHook": sh, "targetNodeId": dst, "targetHook": th, "curve": False, "direction": "forward",
             "arrowSize": "medium"}
        if label:
            c["label"] = {"text": label, "t": 0.5, "offset": offset}
        node = {"id": nid, "type": "connector", "name": nid.split("-", 1)[1], "sceneId": self.u.sid,
                "transform": {"x": self.ox, "y": 0, "scaleX": 1, "scaleY": 1, "rotation": 0}, "width": 10, "height": 10, "zIndex": 1,
                "locked": False, "style": {"fill": "transparent", "stroke": REF, "textColor": DARK, "fontSize": 20, "radius": 0,
                                           "borderStyle": "solid", "borderWidth": 3}, "text": label or "", "connector": c}
        return self._add(node)

    def step(self, notes):
        steps.append({"id": f"{PFX}-{self.u.uid}-step{self.idx + 1}", "order": 0, "label": self.label, "durationMs": 900, "holdMs": 500,
                      "easing": "smooth", "speakerNotes": notes,
                      "target": {"kind": "scene-point", "sceneId": self.u.sid, "point": {"x": self.ox + W / 2, "y": H / 2 - HEADROOM / 2},
                                 "zoom": ZOOM, "referenceViewport": {"width": W, "height": H}}})

    # --- hand-placed card (native shape) helper
    def nid(self, key):
        return f"{PFX}-{self.u.uid}-p{self.idx + 1}-{key}"

    def need_h(self, key, h):
        return max(h, NEED.get(self.nid(key), 0))

    def card(self, key, x, y, w, h, text, c=None, size=22, align="left", plain=False, color=None):
        if plain:
            return self.text(x, y, w, h, text, size=size, color=color or TEXT, align=align, nid=self.nid(key))
        fill, stroke = role(c) if c else (NEUTRAL_FILL, NEUTRAL_STROKE)
        return self.text(x, y, w, h, text, size=size, align=align, fill=fill, stroke=stroke, bw=2, radius=16, shape=True, nid=self.nid(key))


class Unit:
    def __init__(self, uid, title, fx, fy):
        self.uid, self.title, self.fx, self.fy = uid, title, fx, fy
        self.sid, self.fid = f"{PFX}-scene-{uid}", f"{PFX}-frame-{uid}"
        scenes[self.sid] = {"id": self.sid, "name": title, "parentFrameId": self.fid, "nodeIds": [],
                            "camera": {"x": W / 2, "y": H / 2 - HEADROOM / 2, "zoom": ZOOM, "rotation": 0}}
        self.pages = []

    def page(self, label, title, en_title):
        p = Page(self, len(self.pages), label, title, en_title)
        self.pages.append(p)
        return p

    def flow(self, label, title, en_title, notes, *blocks):
        Flow(D, self, label, title, en_title, notes).add(*blocks).build()


def C(key, text, c=None, size=22, align="left", h=80, **kw):
    return Card(key, text, c=c, size=size, align=align, h=h, **kw)


def P_(key, text, size=22, color=None, h=50, align="left"):
    return Card(key, text, size=size, align=align, h=h, plain=True, color=color)


def SYM(key, rows, row_h=78, ws=(190, 962)):
    return Table(key, [("符號 Symbol", "意義 Meaning")] + [(s, zh + "  —  " + en(e)) for s, zh, e in rows], list(ws), row_h=row_h, hdr_h=50,
                 size=22, align="left")




def assemble(U, title, links, camera):
    """U: list of Unit; links: (src_idx, src_hook, dst_idx, dst_hook, label)."""
    scenes["scene-root"] = {"id": "scene-root", "name": "根畫布", "parentFrameId": None, "nodeIds": [], "camera": camera}

    def rnode(nid, typ, x, y, w, h, text, **kw):
        n = {"id": nid, "type": typ, "name": nid, "sceneId": "scene-root", "transform": {"x": x, "y": y, "scaleX": 1, "scaleY": 1, "rotation": 0},
             "width": w, "height": h, "zIndex": kw.pop("z", 1), "locked": False, "style": kw.pop("style"), "text": text}
        n.update(kw)
        nodes[nid] = n
        scenes["scene-root"]["nodeIds"].append(nid)

    for u in U:
        rnode(u.fid, "frame", u.fx, u.fy, 400, 200, u.title,
              style={"fill": "transparent", "stroke": "transparent", "textColor": "#f2ede4", "fontSize": 22, "radius": 0},
              frame={"childSceneId": u.sid, "previewMode": "live", "padding": 18, "clip": True})
    for i, (a, ha, b, hb, label) in enumerate(links, 1):
        c = {"sourceNodeId": U[a].fid, "sourceHook": ha, "targetNodeId": U[b].fid, "targetHook": hb, "curve": False, "direction": "forward",
             "arrowSize": "medium", "label": {"text": label, "t": 0.5, "offset": "above"}}
        rnode(f"{PFX}-rconn{i}", "connector", 0, 0, 10, 10, label, z=0,
              style={"fill": "transparent", "stroke": REF, "textColor": DARK, "fontSize": 20, "radius": 0, "borderStyle": "solid", "borderWidth": 3},
              connector=c)
    page_steps = {}
    for s in steps:
        page_steps.setdefault(s["target"]["sceneId"], []).append(s)
    flat = []
    for u in U:
        flat.append({"id": f"{PFX}-root-step-{u.uid}", "order": 0, "label": u.title, "durationMs": 900, "holdMs": 500, "easing": "smooth",
                     "target": {"kind": "scene-point", "sceneId": "scene-root", "point": {"x": u.fx + 200, "y": u.fy + 100}, "zoom": W / 480,
                                "referenceViewport": {"width": W, "height": H}}})
        flat.extend(page_steps[u.sid])
    flat[0]["speakerNotes"] = "x"
    for i, s in enumerate(flat):
        s["order"] = i
    steps[:] = flat
    return {"schemaVersion": 3, "rootSceneId": "scene-root", "scenes": scenes, "nodes": nodes, "steps": steps,
            "metadata": {"title": title, "createdAt": "2026-10-13T00:00:00.000Z", "updatedAt": "2026-10-13T00:00:00.000Z", "aspectRatio": "16:9"}}
