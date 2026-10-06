"""Step 3b: convert source-prepped.png into a self-typing monochrome ASCII SVG.

  python scripts/make_ascii_svg.py   ->  tushar-ascii.svg

Each row is revealed by a left-to-right clip wipe with a block cursor riding
the edge, staggered top to bottom. It prints once and freezes (SMIL, so it
plays inside GitHub's <img> sandbox). STATIC=1 emits the final frame.
Without source-prepped.png it renders the handle in block letters instead.
"""
import json
import os
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))
SRC = ROOT / "source-prepped.png"
OUT = ROOT / f"{CFG['handle']}-ascii.svg"

RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense); white background -> space
COLS = 100
CHAR_ASPECT = 0.53       # glyph width / line height
FONT_SIZE = 10
CHAR_W = FONT_SIZE * 0.6
LINE_H = FONT_SIZE * 1.13
PAD = 18
ROW_DELAY = 0.06         # seconds between rows starting
ROW_DUR = 0.35           # seconds to wipe one row
BG, BORDER, FG = "#0d1117", "#30363d", "#c9d1d9"
FONT = "'JetBrains Mono','Fira Code',Consolas,'Courier New',monospace"
STATIC = os.environ.get("STATIC") == "1"


def name_image(text):
    """Black text on white, used when no prepped photo exists."""
    font = ImageFont.load_default()
    for name in ("DejaVuSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf"):
        try:
            font = ImageFont.truetype(name, 220)
            break
        except OSError:
            pass
    box = ImageDraw.Draw(Image.new("L", (1, 1))).textbbox((0, 0), text, font=font)
    img = Image.new("L", (box[2] - box[0] + 60, box[3] - box[1] + 60), 255)
    ImageDraw.Draw(img).text((30 - box[0], 30 - box[1]), text, fill=0, font=font)
    return img


def to_rows(img):
    rows = max(1, round(img.height / img.width * COLS * CHAR_ASPECT))
    px = np.asarray(img.convert("L").resize((COLS, rows), Image.LANCZOS), dtype=np.float32) / 255
    idx = ((1 - px) * (len(RAMP) - 1)).round().astype(int)  # dark -> dense
    lines = ["".join(RAMP[i] for i in r).rstrip() for r in idx]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return lines


def build(lines):
    w = round(COLS * CHAR_W + PAD * 2)
    h = round(len(lines) * LINE_H + PAD * 2)
    defs, body = [], []
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        y = PAD + (i + 1) * LINE_H - 2
        lw = len(line) * CHAR_W
        # NBSPs keep leading spaces; textLength pins every column to the grid
        text = escape(line).replace(" ", " ")
        attrs = f'x="{PAD}" y="{y:.1f}" textLength="{lw:.1f}" lengthAdjust="spacingAndGlyphs"'
        if STATIC:
            body.append(f"<text {attrs}>{text}</text>")
            continue
        begin, dur = f"{i * ROW_DELAY:.2f}s", f"{ROW_DUR}s"
        top = y - LINE_H + 2
        defs.append(
            f'<clipPath id="r{i}"><rect x="{PAD}" y="{top:.1f}" width="0" height="{LINE_H + 1:.1f}">'
            f'<animate attributeName="width" from="0" to="{lw:.1f}" begin="{begin}" dur="{dur}" fill="freeze"/>'
            f"</rect></clipPath>"
        )
        body.append(f'<text {attrs} clip-path="url(#r{i})">{text}</text>')
        body.append(
            f'<rect x="{PAD}" y="{top:.1f}" width="{CHAR_W:.1f}" height="{LINE_H - 1:.1f}" fill="{FG}" opacity="0">'
            f'<set attributeName="opacity" to="0.9" begin="{begin}"/>'
            f'<animate attributeName="x" from="{PAD}" to="{PAD + lw:.1f}" begin="{begin}" dur="{dur}" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{i * ROW_DELAY + ROW_DUR:.2f}s"/></rect>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<defs>{''.join(defs)}</defs>
<rect width="{w}" height="{h}" rx="10" fill="{BG}" stroke="{BORDER}"/>
<g font-family="{FONT}" font-size="{FONT_SIZE}" fill="{FG}">
{chr(10).join(body)}
</g>
</svg>
"""


def main():
    if SRC.exists():
        img = Image.open(SRC)
    else:
        print(f"no {SRC.name}; rendering the handle instead (run prep_photo.py first)")
        img = name_image(CFG["handle"].capitalize())
    OUT.write_text(build(to_rows(img)), encoding="utf-8")
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
