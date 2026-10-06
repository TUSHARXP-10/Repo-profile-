"""Step 4: convert assets/portrait.txt into a self-typing SVG (assets/ascii.svg).

Each line is revealed left-to-right by a SMIL-animated clip rect, one line
after another, which works inside GitHub's <img> sandbox (no JS needed).
"""
from common import ASSETS, BG, BORDER, FONT, GREEN, esc, write

FONT_SIZE = 9
CHAR_W = FONT_SIZE * 0.6
LINE_H = FONT_SIZE * 1.15
PAD = 16
LINE_DUR = 0.12  # seconds to type one line


def build(art):
    lines = art.rstrip("\n").split("\n")
    cols = max(len(l) for l in lines)
    w = round(cols * CHAR_W + PAD * 2)
    h = round(len(lines) * LINE_H + PAD * 2)
    defs, texts = [], []
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        line = line.ljust(cols)  # equal widths keep columns aligned
        y = PAD + (i + 1) * LINE_H - 2
        lw = len(line) * CHAR_W
        begin = f"{i * LINE_DUR:.2f}s"
        defs.append(
            f'<clipPath id="c{i}"><rect x="{PAD}" y="{y - LINE_H:.1f}" width="0" height="{LINE_H + 2:.1f}">'
            f'<animate attributeName="width" from="0" to="{lw:.1f}" begin="{begin}" '
            f'dur="{LINE_DUR * 2:.2f}s" fill="freeze"/></rect></clipPath>'
        )
        texts.append(
            f'<text x="{PAD}" y="{y:.1f}" clip-path="url(#c{i})" textLength="{lw:.1f}" '
            f'lengthAdjust="spacingAndGlyphs">{esc(line).replace(" ", "\u00a0")}</text>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<defs>{''.join(defs)}</defs>
<rect width="{w}" height="{h}" rx="10" fill="{BG}" stroke="{BORDER}"/>
<g font-family="{FONT}" font-size="{FONT_SIZE}" fill="{GREEN}" xml:space="preserve">
{chr(10).join(texts)}
</g>
</svg>
"""


def main():
    art = (ASSETS / "portrait.txt").read_text(encoding="utf-8")
    write("ascii.svg", build(art))


if __name__ == "__main__":
    main()
