#!/usr/bin/env python3
"""Automatic quality audit for a bilingual lecture note (lectures/lecNN*.md).

Checks what a program can check (SKILL.md section 7, NARRATIVE.md):
  L1  every heading has an English part in full-width parentheses, no placeholder English ("Knowledge point 09")
  L2  headings that repeat three or more times (boilerplate sections)
  L3  slide / class-time vocabulary that does not belong in a lecture (main line, extension pages, minutes, core allocation)
  L4  learning objectives that are the same sentence for several knowledge points
  L5  in-page links (#anchor) that do not match any heading
  L6  numbers written as Chinese numerals in headings (hard to search)
  L7  each knowledge point contains the SKILL.md 4.6 fields (one-sentence summary, plain explanation, formal definition,
      example, common misconception, practice)
  L8  slide-by-slide transcription: too many tiny sections per knowledge point
  L9  slides / sections that are only a one-line fragment (< 40 characters of body)
Usage:  py .agents/skills/textbook-lecture-notes/scripts/audit_lecture.py lectures/lecNN.md
Exit code 1 when there is a FAIL.
"""
import argparse
import re
import sys
from collections import Counter

HEAD = re.compile(r"^(#{2,3})\s+(.*)$", re.M)
FIELDS = [("一句話重點", "One-sentence"), ("白話說明", "Plain explanation"), ("正式定義", "Formal definition"),
          ("例子", "Example"), ("常見迷思", "Common misconception"), ("小練習", "Practice")]
META = re.compile(r"主線頁|延伸頁|課堂主線|Core allocation|簡報時長|淨授課|休息|core minutes|主線時間")
PLACEHOLDER = re.compile(r"Knowledge point\s*\d+|knowledge-point|Section\s*\d+\s*[)）]", re.I)
CN_NUM = re.compile(r"[一二三四五六七八九十百千萬兆]+[點兆萬億]|[點][一二三四五六七八九零]")


def slug(h):
    h = re.sub(r"<[^>]+>", "", h).strip().lower()
    h = re.sub(r"[^\w\s-]", "", h, flags=re.U)
    return re.sub(r"[\s]+", "-", h)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("lecture")
    ap.add_argument("--source", action="append", default=[], help="source text file(s); L10 warns when the lecture repeats long runs of the source (14+ identical CJK characters)")
    ap.add_argument("--max-sections-per-kp", type=int, default=14, help="L8 limit (default 14)")
    args = ap.parse_args()
    text = open(args.lecture, encoding="utf-8").read()
    fails, warns = [], []
    F = lambda c, m: fails.append(f"FAIL {c} {m}")
    W = lambda c, m: warns.append(f"WARN {c} {m}")

    heads = [(len(m.group(1)), m.group(2).strip(), m.start()) for m in HEAD.finditer(text)]
    # L1
    for lvl, h, _ in heads:
        if PLACEHOLDER.search(h): F("L1", f"placeholder English in heading: {h!r}")
        elif ("（" not in h and "(" not in h) and not re.match(r"^(符號表|術語對照|學習目標)", h) and re.search(r"[一-鿿]", h):
            W("L1", f"heading has no English part: {h!r}")
    # L2
    zh = Counter(re.split(r"[（(]", h)[0].strip() for lvl, h, _ in heads if lvl == 3)
    for t, c in zh.items():
        if c >= 3 and not re.match(r"^(符號表|術語對照|術語表|學習目標|來源)", t): W("L2", f"heading {t!r} appears {c} times (boilerplate sections)")
    # L3
    for m in META.finditer(text):
        ln = text.count("\n", 0, m.start()) + 1
        W("L3", f"line {ln}: slide/class-time wording in a lecture: {m.group(0)!r}")
        break
    n_meta = len(META.findall(text))
    if n_meta > 3: F("L3", f"{n_meta} places use slide/class-time wording; the lecture must not depend on the deck or the class schedule")
    # L4
    objs = re.findall(r"學習目標[^\n]*\n+([^\n]+)", text)
    norm = Counter(re.sub(r"[「『][^」』]*[」』]", "X", o) for o in objs)
    for o, c in norm.items():
        if c >= 3: W("L4", f"{c} learning objectives are the same sentence ({o[:30]!r}...): write objectives specific to each knowledge point")
    # L5
    anchors = {slug(h) for _, h, _ in heads}
    for m in re.finditer(r"\]\(#([^)]+)\)", text):
        if m.group(1).lower() not in anchors and m.group(1) not in anchors:
            W("L5", f"link #{m.group(1)} matches no heading")
    # L6
    for lvl, h, _ in heads:
        if CN_NUM.search(h): W("L6", f"Chinese numerals in a heading (use digits so it can be searched): {h!r}")
    # L7 / L8 / L9 per knowledge point
    kp_idx = [(i, h) for i, (lvl, h, _) in enumerate(heads) if lvl == 2 and re.match(r"KP\s*\d+", h)]
    for n, (i, h) in enumerate(kp_idx):
        start = heads[i][2]
        end = heads[kp_idx[n + 1][0]][2] if n + 1 < len(kp_idx) else len(text)
        block = text[start:end]
        found = [zh_ for zh_, en_ in FIELDS if f"**{zh_}**" in block or zh_ in block]
        miss = [zh_ for zh_, _ in FIELDS if zh_ not in found]
        if len(found) < 3: F("L7", f"{h[:20]!r}: only {len(found)}/6 SKILL 4.6 fields present (missing {miss})")
        elif miss: W("L7", f"{h[:20]!r}: missing fields {miss}")
        subs = [x for x in heads[i + 1:(kp_idx[n + 1][0] if n + 1 < len(kp_idx) else len(heads))] if x[0] == 3]
        if len(subs) > args.max_sections_per_kp:
            W("L8", f"{h[:20]!r}: {len(subs)} sections; a lecture explains in connected prose, it does not transcribe one slide per section")
    secs = re.split(r"^### .*$", text, flags=re.M)[1:]
    titles = [h for lvl, h, _ in heads if lvl == 3]
    tiny = [t for t, b in zip(titles, secs) if len(re.sub(r"[\s>*#|$-]", "", b)) < 40]
    if len(tiny) > 3: W("L9", f"{len(tiny)} sections are one-line fragments, e.g. {tiny[:3]}")

    if args.source:
        cj = re.compile(r"[㐀-鿿豈-﫿]")
        stream = lambda t: "".join(cj.findall(re.sub(r"\$[^$]*\$", "", t)))
        grams = set()
        for sp in args.source:
            st = stream(open(sp, encoding="utf-8").read())
            grams |= {st[i:i + 14] for i in range(len(st) - 13)}
        lt = stream(text)
        hits = sum(1 for i in range(len(lt) - 13) if lt[i:i + 14] in grams)
        if hits > 30: W("L10", f"{hits} positions start a 14-character run identical to the source: rewrite in your own words")
    for x in fails + warns: print(x)
    print(f"audit_lecture: {args.lecture}  headings {len(heads)}  knowledge points {len(kp_idx)}  FAIL {len(fails)}  WARN {len(warns)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
