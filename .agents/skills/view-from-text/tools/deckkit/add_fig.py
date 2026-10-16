"""Register a dark-skin figure (assets/figures/<id>.svg) in <work_dir>/figs.json for the deck kit.
Usage:  py add_fig.py <work_dir> <figure_id> "<alt text>" [<repo_root>]"""
import base64
import json
import os
import re
import sys

work, fid, alt = sys.argv[1], sys.argv[2], sys.argv[3]
root = sys.argv[4] if len(sys.argv) > 4 else os.getcwd()
raw = open(os.path.join(root, "assets", "figures", fid + ".svg"), "rb").read()
m = re.search(rb'viewBox="0 0 ([\d.]+) ([\d.]+)"', raw)
w, h = round(float(m.group(1)) * 100 / 72), round(float(m.group(2)) * 100 / 72)   # matplotlib pt -> figsize*100 px
path = os.path.join(work, "figs.json")
figs = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
figs[fid] = {"uri": "data:image/svg+xml;base64," + base64.b64encode(raw).decode(), "w": w, "h": h, "alt": alt}
json.dump(figs, open(path, "w", encoding="utf-8"), ensure_ascii=False)
print(fid, w, h)
