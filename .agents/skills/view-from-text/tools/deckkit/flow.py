"""Flow layout for JianBauDau pages: blocks are stacked top to bottom and spill onto continuation pages ("(續)")
instead of being cut short (view-from-text SKILL 3A). Heights come from need.json (measured by preview_deck.py)."""
import re

TOP, BOTTOM, GAPY, X0, WIDTH = 136, 706, 12, 60, 1160


class Card:
    def __init__(self, key, text, c=None, size=24, align="left", h=90, weight=400, plain=False, color=None, lh=1.4):
        self.key, self.text, self.c, self.size, self.align, self.h, self.weight, self.plain, self.color, self.lh = \
            key, text, c, size, align, h, weight, plain, color, lh


class Fig:
    def __init__(self, key, fig_id, w=None):
        self.key, self.fig_id, self.w = key, fig_id, w


class Col:
    def __init__(self, width, items):
        self.width, self.items = width, items


class Row:
    def __init__(self, key, cols, conn=None, gapx=40):
        self.key, self.cols, self.conn, self.gapx = key, cols, conn or [], gapx


class Table:
    def __init__(self, key, rows, ws, row_h=60, hdr_h=56, size=22, hl=None, align="center", gap=8):
        self.key, self.rows, self.ws, self.row_h, self.hdr_h, self.size, self.hl, self.align, self.gap = \
            key, rows, ws, row_h, hdr_h, size, hl, align, gap


def split_notes(notes, n):
    """Spread the speaker notes over n pages; every page keeps at least ~60 characters."""
    if n <= 1:
        return [notes]
    parts = [p for p in re.split(r"(?<=[。!?])", notes) if p.strip()]
    if len(parts) < n or len(notes) / n < 70:
        return [notes] + ["(接續上一頁的說明)" + notes] * (n - 1)
    per = len(parts) / n
    out = []
    for i in range(n):
        chunk = "".join(parts[round(i * per):round((i + 1) * per)])
        out.append(chunk if i == 0 else "(接續上一頁)" + chunk)
    if min(len(re.sub(r"\s", "", c)) for c in out) < 75:
        return [notes] + ["(接續上一頁的說明)" + notes] * (n - 1)
    return out


class Flow:
    """Usage: f = Flow(D, unit, label, title, en_title, notes); f.add(Card(...)); ...; f.build()"""

    def __init__(self, D, unit, label, title, en_title, notes):
        self.D, self.u, self.label, self.title, self.en_title, self.notes = D, unit, label, title, en_title, notes
        self.blocks = []

    def add(self, *blocks):
        self.blocks.extend(blocks)
        return self

    # ---- measured heights
    def nid(self, key):
        return f"{self.D.PFX}-{self.u.uid}-{key}"

    def card_h(self, card):
        return max(card.h, self.D.NEED.get(self.nid(card.key), 0))

    def fig_size(self, fig, width=None):
        f = self.D.FIGS[fig.fig_id]
        w = fig.w or width or f["w"]
        w = min(w, width or w)
        return w, f["h"] * w / f["w"]

    def col_h(self, col):
        h = 0
        for it in col.items:
            h += (self.fig_size(it, col.width)[1] if isinstance(it, Fig) else self.card_h(it)) + 12
        return h - 12

    def row_cells_h(self, t, r, key):
        hs = [self.D.NEED.get(self.nid(f"{key}-c{j}"), 0) for j in range(len(t.rows[r]))]
        return max([t.hdr_h if r == 0 else t.row_h] + hs)

    # ---- units of packing: (height, placer)
    def units(self):
        out = []
        for b in self.blocks:
            if isinstance(b, Card):
                out.append(("card", b, self.card_h(b)))
            elif isinstance(b, Fig):
                out.append(("fig", b, self.fig_size(b, WIDTH)[1]))
            elif isinstance(b, Row):
                out.append(("row", b, max(self.col_h(c) for c in b.cols)))
            elif isinstance(b, Table):
                for r in range(1, len(b.rows)):
                    out.append(("trow", (b, r), self.row_cells_h(b, r, f"{b.key}-r{r}")))
        return out

    def build(self):
        units = self.units()
        pages, cur, y, cur_table = [], [], TOP, None
        for kind, obj, h in units:
            need_hdr = 0
            if kind == "trow" and (cur_table is not obj[0]):
                need_hdr = self.row_cells_h(obj[0], 0, f"{obj[0].key}-h{len(pages)}") + obj[0].gap
            if cur and y + need_hdr + h > BOTTOM:
                pages.append(cur)
                cur, y, cur_table = [], TOP, None
                if kind == "trow":
                    need_hdr = self.row_cells_h(obj[0], 0, f"{obj[0].key}-h{len(pages)}") + obj[0].gap
            if kind == "trow" and cur_table is not obj[0]:
                cur.append(("thdr", obj[0], y))
                y += need_hdr
                cur_table = obj[0]
            elif kind != "trow":
                cur_table = None
            cur.append((kind, obj, y))
            y += h + (obj[0].gap if kind == "trow" else GAPY)
        pages.append(cur)
        notes = split_notes(self.notes, len(pages))
        for i, items in enumerate(pages):
            cont = i > 0
            p = self.u.page(self.label + ("(續)" if cont else ""), self.title + ("(續)" if cont else ""),
                            self.en_title + (" (continued)" if cont else ""))
            for kind, obj, y in items:
                self.place(p, kind, obj, y, i)
            p.step(notes[i])
        return self

    def place(self, p, kind, obj, y, page_no):
        D = self.D
        if kind == "card":
            self.place_card(p, obj, X0, y, WIDTH)
        elif kind == "fig":
            w, h = self.fig_size(obj, WIDTH)
            p.figure(obj.fig_id, X0 + (WIDTH - w) / 2, y, w)
        elif kind == "row":
            x, firsts = X0, []
            for col in obj.cols:
                yy, first = y, None
                for it in col.items:
                    if isinstance(it, Fig):
                        w, h = self.fig_size(it, col.width)
                        p.figure(it.fig_id, x, yy, w)
                        yy += h + 12
                    else:
                        nid = self.place_card(p, it, x, yy, col.width)
                        first = first or nid
                        yy += D.nodes[nid]["height"] + 12
                firsts.append(first)
                x += col.width + obj.gapx
            for a, ha, b, hb, label, *opt in obj.conn:
                p.conn(firsts[a], ha, firsts[b], hb, label, offset=opt[0] if opt else "above")
        elif kind in ("thdr", "trow"):
            t, r = (obj, 0) if kind == "thdr" else obj
            key = f"{t.key}-h{page_no}" if kind == "thdr" else f"{t.key}-r{r}"
            h = self.row_cells_h(t, r, key)
            x = X0
            for j, cell in enumerate(t.rows[r]):
                hdr = r == 0
                c = D.REF if hdr else (D.MAIN if r == t.hl else None)
                fill, stroke = D.role(c) if c else (D.NEUTRAL_FILL, D.NEUTRAL_STROKE)
                p.text(x, y, t.ws[j], h, cell, size=t.size, weight=700 if hdr else 400,
                       align="center" if (hdr or j == 0) else t.align, fill=fill, stroke=stroke, bw=1, radius=12, lh=1.25,
                       shape=True, nid=f"{D.PFX}-{self.u.uid}-{key}-c{j}")
                x += t.ws[j] + 8

    def place_card(self, p, card, x, y, w):
        D = self.D
        h = self.card_h(card)
        if card.plain:
            return p.text(x, y, w, h, card.text, size=card.size, color=card.color or D.TEXT, align=card.align, weight=card.weight,
                          lh=card.lh, nid=self.nid(card.key))
        fill, stroke = D.role(card.c) if card.c else (D.NEUTRAL_FILL, D.NEUTRAL_STROKE)
        return p.text(x, y, w, h, card.text, size=card.size, align=card.align, weight=card.weight, fill=fill, stroke=stroke, bw=2,
                      radius=16, lh=card.lh, shape=True, nid=self.nid(card.key))
