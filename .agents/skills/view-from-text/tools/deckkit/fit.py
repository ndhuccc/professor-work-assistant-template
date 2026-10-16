"""Grow text boxes to their measured content height (preview_deck slack.json), a few rounds.
Usage:  py fit.py <work_dir> <deck_script.py>      (work_dir holds kit.py, flow.py, figs.json, need.json, the deck script)"""
import json
import os
import subprocess
import sys

WORK = os.path.abspath(sys.argv[1])
SCRIPT = sys.argv[2]
TOOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "preview_deck.py")
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}
NEED_F = os.path.join(WORK, "need.json")
need = json.load(open(NEED_F, encoding="utf-8")) if os.path.exists(NEED_F) else {}
for rnd in range(4):
    print(subprocess.run([sys.executable, SCRIPT], cwd=WORK, capture_output=True, text=True, env=ENV).stdout.strip())
    subprocess.run([sys.executable, TOOL, os.path.join(WORK, "draft.jbd.json"), "--out", os.path.join(WORK, "prev")], cwd=WORK, capture_output=True, env=ENV)
    slack = json.load(open(os.path.join(WORK, "prev", "slack.json"), encoding="utf-8"))
    changed = 0
    for page, items in slack.items():
        for m in items:
            want = m["content"] + (m["h"] - m["content"] - m["slack"]) + 4
            if m["overflowH"] or m["slack"] < 0:
                if want <= need.get(m["id"], 0):
                    want = need[m["id"]] + 12          # KaTeX display margins overflow without growing the content box
                need[m["id"]] = want
                changed += 1
    json.dump(need, open(NEED_F, "w", encoding="utf-8"))
    print("round", rnd, "grown", changed)
    if not changed:
        break
