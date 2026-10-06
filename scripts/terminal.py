"""Shared terminal-window chrome so the portrait and stats panels match."""
import json
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))

W, H = 400, 480          # both whoami panels share this size
BAR_H = 24
PAD = 14
FONT = "'JetBrains Mono','SF Mono','Fira Code',Consolas,'Courier New',monospace"

BG = "#0d1117"
TILE = "#161b22"
LINE = "#30363d"
FG = "#e6edf3"
DIM = "#8b949e"
ACCENT = "#a9c98c"       # sage green, matches the heatmap


def esc(s):
    return escape(str(s))


def window(title, body, defs="", style=""):
    dots = "".join(f'<circle cx="{14 + i * 11}" cy="{BAR_H / 2}" r="3.2" fill="{c}"/>'
                   for i, c in enumerate(("#e0a458", "#d9b25c", "#c9a24f")))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<style>{style}</style>
<defs>{defs}</defs>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="8" fill="{BG}" stroke="{LINE}"/>
<line x1="1" y1="{BAR_H}" x2="{W - 1}" y2="{BAR_H}" stroke="{LINE}" stroke-opacity=".6"/>
{dots}
<text x="{W / 2}" y="{BAR_H / 2 + 3}" text-anchor="middle" fill="{DIM}" font-family="{FONT}" font-size="8.5">{esc(title)}</text>
<g font-family="{FONT}">
{body}
</g>
</svg>
"""
