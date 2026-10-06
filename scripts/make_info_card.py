"""Step 4: neofetch-style info card.

  python scripts/make_info_card.py   ->  info-card.svg

Content lives in profile.json ("card"). Each line fades and slides in on a
short stagger. STATIC=1 emits a frozen final frame for local previews.
"""
import json
import os
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))
OUT = ROOT / "info-card.svg"

W = 490
PAD = 22
FONT_SIZE = 13
CHAR_W = FONT_SIZE * 0.6
LINE_H = 21
BAR_H = 32
KEY_COL = 12
WRAP = int((W - 2 * PAD) / CHAR_W) - KEY_COL
STEP = 0.14
BG, BAR, BORDER = "#0d1117", "#161b22", "#30363d"
FG, DIM, KEY, TITLE = "#c9d1d9", "#8b949e", "#7ee787", "#79c0ff"
DOTS = ["#ff5f56", "#ffbd2e", "#27c93f"]
SWATCHES = ["#484f58", "#ff7b72", "#7ee787", "#d29922", "#79c0ff", "#d2a8ff", "#56d4dd", "#e6edf3"]
FONT = "'JetBrains Mono','Fira Code',Consolas,'Courier New',monospace"
STATIC = os.environ.get("STATIC") == "1"


def esc(s):
    return escape(str(s)).replace(" ", " ")


def lines():
    """Yield (svg_fragment_builder) rows: each is a function of y -> svg."""
    user = f"{CFG['handle']}@{CFG['host']}"
    yield lambda y: (f'<text x="{PAD}" y="{y}"><tspan fill="{TITLE}" font-weight="bold">{esc(CFG["handle"])}</tspan>'
                     f'<tspan fill="{FG}">@</tspan><tspan fill="{TITLE}" font-weight="bold">{esc(CFG["host"])}</tspan></text>')
    yield lambda y: f'<text x="{PAD}" y="{y}" fill="{DIM}">{"-" * len(user)}</text>'
    for key, value in CFG["card"]:
        items = value if isinstance(value, list) else [value]
        first = True
        for item in items:
            prefix = "• " if isinstance(value, list) else ""
            wrapped = textwrap.wrap(prefix + item, WRAP, subsequent_indent="  " if prefix else "")
            for chunk in wrapped:
                k = f"{key}:" if first else ""
                first = False
                yield (lambda y, k=k, chunk=chunk:
                       f'<text x="{PAD}" y="{y}"><tspan fill="{KEY}" font-weight="bold">{esc(k.ljust(KEY_COL))}</tspan>'
                       f'<tspan fill="{FG}">{esc(chunk)}</tspan></text>')
    yield None  # spacer
    yield lambda y: "".join(f'<rect x="{PAD + i * 28}" y="{y - 13}" width="24" height="16" rx="3" fill="{c}"/>'
                            for i, c in enumerate(SWATCHES))


def build():
    out, y, i = [], BAR_H + PAD + 4, 0
    for row in lines():
        if row is None:
            y += LINE_H // 2
            continue
        frag = row(y)
        if STATIC:
            out.append(frag)
        else:
            b = f"{0.3 + i * STEP:.2f}s"
            out.append(
                f'<g opacity="0">'
                f'<animate attributeName="opacity" from="0" to="1" begin="{b}" dur="0.35s" fill="freeze"/>'
                f'<animateTransform attributeName="transform" type="translate" from="-8 0" to="0 0" begin="{b}" dur="0.35s" fill="freeze"/>'
                f"{frag}</g>"
            )
        y += LINE_H
        i += 1
    if not STATIC:
        out.append(f'<rect x="{PAD}" y="{y - 13}" width="8" height="15" fill="{FG}" opacity="0">'
                   f'<set attributeName="opacity" to="1" begin="{0.3 + i * STEP:.2f}s"/>'
                   f'<animate attributeName="opacity" values="1;1;0;0" dur="1s" begin="{0.3 + i * STEP:.2f}s" repeatCount="indefinite"/></rect>')
    h = y + PAD - 4
    dots = "".join(f'<circle cx="{18 + j * 18}" cy="{BAR_H / 2}" r="5.5" fill="{c}"/>' for j, c in enumerate(DOTS))
    title = f"{CFG['handle']}@{CFG['host']}: ~ — neofetch"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}">
<clipPath id="win"><rect width="{W}" height="{h}" rx="10"/></clipPath>
<g clip-path="url(#win)">
<rect width="{W}" height="{h}" fill="{BG}"/>
<rect width="{W}" height="{BAR_H}" fill="{BAR}"/>
<line x1="0" y1="{BAR_H}" x2="{W}" y2="{BAR_H}" stroke="{BORDER}"/>
</g>
<rect x="0.5" y="0.5" width="{W - 1}" height="{h - 1}" rx="10" fill="none" stroke="{BORDER}"/>
{dots}
<text x="{W / 2}" y="{BAR_H / 2 + 4}" text-anchor="middle" fill="{DIM}" font-family="{FONT}" font-size="11">{esc(title)}</text>
<g font-family="{FONT}" font-size="{FONT_SIZE}">
{chr(10).join(out)}
</g>
</svg>
"""


def main():
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
