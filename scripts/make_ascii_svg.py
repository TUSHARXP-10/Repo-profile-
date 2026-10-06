"""Step 3b: convert a portrait into a self-typing monochrome ASCII terminal window.

  python scripts/make_ascii_svg.py   ->  tushar-ascii.svg

Source, in order of preference:
  1. source-prepped.png  (made locally by prep_photo.py: background removed, CLAHE)
  2. your GitHub avatar  (downloaded, auto-contrasted)
  3. your name in block letters

The workflow runs this with --auto daily so the avatar version stays current;
a portrait generated from a real photo is never overwritten.

Each row is revealed by a left-to-right clip wipe with a block cursor riding the
edge, staggered top to bottom; it prints once and freezes (SMIL, so it plays
inside GitHub's <img> sandbox). STATIC=1 emits the final frame.
"""
import io
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

from terminal import ACCENT, BAR_H, CFG, DIM, FG, H, PAD, ROOT, W, esc, window

SRC = ROOT / "source-prepped.png"
OUT = ROOT / f"{CFG['handle']}-ascii.svg"

RAMP = " .`:-=+*cs#%@"   # bright (sparse) -> dark (dense); white background -> space
COLS = 100
CHAR_W = (W - 2 * PAD) / COLS
LINE_H = CHAR_W / 0.55   # monospace glyphs are ~1.8x taller than wide
FONT_SIZE = CHAR_W / 0.6
PROMPT_H = 22
ROW_DELAY = 0.045
ROW_DUR = 0.3
TEXT = "#b1bac4"
STATIC = os.environ.get("STATIC") == "1"


def avatar():
    import requests
    url = f"https://avatars.githubusercontent.com/u/{CFG['github_id']}?s=460"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    img = Image.open(io.BytesIO(r.content)).convert("RGBA")
    white = Image.new("RGBA", img.size, "white")
    gray = Image.alpha_composite(white, img).convert("L")
    return ImageOps.autocontrast(gray, cutoff=1)


def name_image(text):
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


def source():
    if SRC.exists():
        return Image.open(SRC).convert("L"), "photo"
    try:
        return avatar(), "avatar"
    except Exception as e:  # offline, no avatar, etc.
        print(f"avatar unavailable ({e}); rendering the name instead")
        return name_image(CFG["name"]), "name"


def to_rows(img):
    max_rows = int((H - BAR_H - 2 * PAD - PROMPT_H) / LINE_H)
    cols = COLS
    rows = round(img.height / img.width * cols * CHAR_W / LINE_H)
    if rows > max_rows:  # tall photo: shrink width so it fits the window
        cols = int(cols * max_rows / rows)
        rows = max_rows
    px = np.asarray(img.resize((cols, max(rows, 1)), Image.LANCZOS), dtype=np.float32) / 255
    idx = ((1 - px) * (len(RAMP) - 1)).round().astype(int)
    lines = ["".join(RAMP[i] for i in r).rstrip() for r in idx]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return lines, cols


def build(lines, cols):
    area_top = BAR_H + PAD
    area_h = H - BAR_H - 2 * PAD - PROMPT_H
    top = area_top + max(0, (area_h - len(lines) * LINE_H) / 2)
    left = PAD + (COLS - cols) * CHAR_W / 2
    defs, body = [], [f'<g font-size="{FONT_SIZE:.2f}" fill="{TEXT}">']
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        y = top + (i + 1) * LINE_H - LINE_H * 0.22
        lw = len(line) * CHAR_W
        text = esc(line).replace(" ", " ")  # NBSPs keep leading spaces
        attrs = f'x="{left:.1f}" y="{y:.2f}" textLength="{lw:.1f}" lengthAdjust="spacingAndGlyphs"'
        if STATIC:
            body.append(f"<text {attrs}>{text}</text>")
            continue
        b, end = i * ROW_DELAY, i * ROW_DELAY + ROW_DUR
        ry = top + i * LINE_H
        defs.append(
            f'<clipPath id="r{i}"><rect x="{left:.1f}" y="{ry:.2f}" width="0" height="{LINE_H + .5:.2f}">'
            f'<animate attributeName="width" from="0" to="{lw:.1f}" begin="{b:.2f}s" dur="{ROW_DUR}s" fill="freeze"/>'
            f"</rect></clipPath>"
        )
        body.append(f'<text {attrs} clip-path="url(#r{i})">{text}</text>')
        body.append(
            f'<rect x="{left:.1f}" y="{ry:.2f}" width="{CHAR_W * 1.6:.1f}" height="{LINE_H:.2f}" fill="{FG}" opacity="0">'
            f'<set attributeName="opacity" to=".85" begin="{b:.2f}s"/>'
            f'<animate attributeName="x" from="{left:.1f}" to="{left + lw:.1f}" begin="{b:.2f}s" dur="{ROW_DUR}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{end:.2f}s"/></rect>'
        )
    body.append("</g>")

    # prompt line at the bottom: snapshot:~ $ whoami  Name█
    done = len(lines) * ROW_DELAY + ROW_DUR
    py = H - PAD
    prompt = (f'<text x="{PAD}" y="{py}" font-size="8.5" fill="{DIM}">snapshot:~ $ whoami  '
              f'<tspan fill="{FG}" font-weight="bold">{esc(CFG["name"])}</tspan></text>')
    cx = PAD + (len("snapshot:~ $ whoami  ") + len(CFG["name"]) + 0.6) * 5.1
    cursor = f'<rect x="{cx:.1f}" y="{py - 8}" width="5" height="10" fill="{ACCENT}"'
    if STATIC:
        body += [prompt, cursor + "/>"]
    else:
        body += [
            f'<g opacity="0"><set attributeName="opacity" to="1" begin="{done:.2f}s"/>{prompt}</g>',
            cursor + f' opacity="0"><animate attributeName="opacity" values="1;1;0;0" dur="1.1s" '
                     f'begin="{done:.2f}s" repeatCount="indefinite"/></rect>',
        ]
    return window(f"snapshot ~ ./{CFG['handle']}.sh", "\n".join(body), "".join(defs))


def main():
    # --auto (used by the workflow): never overwrite a portrait made from a real photo
    if "--auto" in sys.argv and OUT.exists() and "<!-- source: photo -->" in OUT.read_text(encoding="utf-8"):
        print(f"{OUT.name} was made from a photo; leaving it alone")
        return
    img, kind = source()
    lines, cols = to_rows(img)
    OUT.write_text(f"<!-- source: {kind} -->\n" + build(lines, cols), encoding="utf-8")
    print(f"wrote {OUT.name} ({len(lines)} rows x {cols} cols)")


if __name__ == "__main__":
    main()
