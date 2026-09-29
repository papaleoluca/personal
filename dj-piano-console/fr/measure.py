#!/usr/bin/env python3
"""Measure every drawing label in headless Chrome and compare the French against the English.

Reports French labels that leave their drawing's viewBox, and label pairs that overlap in French
but did not in English (the two documents carry the same elements in the same order). Run it
after changing a drawing translation or TAG_EDITS; it exits 1 on any problem.

    python3 fr/measure.py [--widths]
"""
import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
EN = PKG / "dj-piano-console-v2-spec.html"
FR = PKG / "dj-piano-console-v2-spec-fr.html"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

JS = r"""
<script>
document.fonts.ready.then(() => {
  const out = [];
  document.querySelectorAll('svg').forEach((svg, si) => {
    const vb = svg.viewBox.baseVal;
    const inv = svg.getScreenCTM().inverse();
    const toUser = (x, y) => { const p = svg.createSVGPoint(); p.x = x; p.y = y; return p.matrixTransform(inv); };
    const boxes = [...svg.querySelectorAll('text')].map((t, ti) => {
      const r = t.getBoundingClientRect();
      const a = toUser(r.left, r.top), b = toUser(r.right, r.bottom);
      return {ti, text: t.textContent, x0: Math.min(a.x, b.x), y0: Math.min(a.y, b.y), x1: Math.max(a.x, b.x), y1: Math.max(a.y, b.y)};
    });
    out.push({si, vb: [vb.x, vb.y, vb.width, vb.height], boxes});
  });
  const pre = document.createElement('pre'); pre.id = 'measure-out';
  pre.textContent = JSON.stringify(out); document.body.appendChild(pre);
});
</script>
"""


def measure(path, tmp):
    probe = Path(tmp) / (path.stem + ".probe.html")      # a copy with the probe script; the repo is never written
    probe.write_text(path.read_text(encoding="utf-8").replace("</body>", JS + "</body>"), encoding="utf-8")
    dom = subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--window-size=1600,1200",
         "--virtual-time-budget=5000", "--dump-dom", probe.as_uri()],
        capture_output=True, text=True, timeout=120).stdout
    m = re.search(r'<pre id="measure-out">(.*?)</pre>', dom, re.S)
    return json.loads(html.unescape(m.group(1)))


def inter(a, b, pad=0.3):
    w = min(a["x1"], b["x1"]) - max(a["x0"], b["x0"]) - pad
    h = min(a["y1"], b["y1"]) - max(a["y0"], b["y0"]) - pad
    return max(w, 0) * max(h, 0)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        en, fr = measure(EN, tmp), measure(FR, tmp)
    bad = 0
    for se, sf in zip(en, fr):
        x, y, w, h = sf["vb"]
        for bf in sf["boxes"]:
            over = max(x - bf["x0"], bf["x1"] - (x + w), y - bf["y0"], bf["y1"] - (y + h))
            if over > 0.5:
                bad += 1
                print(f"svg{sf['si']} CLIPPED by {over:.0f}: {bf['text']!r}  x {bf['x0']:.0f}..{bf['x1']:.0f} (viewBox {x:g}..{x + w:g})")
        be, bfs = se["boxes"], sf["boxes"]
        for i in range(len(bfs)):
            for j in range(i + 1, len(bfs)):
                if inter(bfs[i], bfs[j]) > 0 and inter(be[i], be[j]) == 0:
                    bad += 1
                    print(f"svg{sf['si']} NEW OVERLAP: {bfs[i]['text']!r} x {bfs[j]['text']!r}")
    if "--widths" in sys.argv:
        for se, sf in zip(en, fr):
            for a, b in zip(se["boxes"], sf["boxes"]):
                print(f"svg{sf['si']} {a['x1'] - a['x0']:6.0f} -> {b['x1'] - b['x0']:6.0f}  {b['text']}")
    print(f"{bad} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
