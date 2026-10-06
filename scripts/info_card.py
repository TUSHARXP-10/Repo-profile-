"""Step 4b: neofetch-style info card (assets/info.svg)."""
import datetime as dt

from common import ACCENT, BG, BORDER, DIM, FG, FONT, GREEN, YELLOW, esc, load_config, write

FONT_SIZE = 14
LINE_H = 22
PAD = 24
WIDTH = 520
KEY_COL = 13  # characters reserved for keys
STEP = 0.18   # seconds between lines appearing
PALETTE = ["#484f58", "#ff7b72", "#3fb950", "#d29922", "#58a6ff", "#bc8cff", "#39c5cf", "#c9d1d9"]


def build(cfg, stats):
    user = cfg["github_user"]
    title = f"{user.lower()}@{cfg.get('host', 'github')}"
    rows = [("title", title), ("rule", "-" * len(title))]
    rows += [("kv", k, v) for k, v in cfg.get("info", [])]
    rows.append(("blank",))
    rows.append(("head", "GitHub Stats"))
    if stats:
        rows += [
            ("kv", "Repos", f"{stats['repos']}"),
            ("kv", "Stars", f"{stats['stars']}"),
            ("kv", "Followers", f"{stats['followers']}"),
            ("kv", "Commits/yr", f"{stats['total']} contributions"),
        ]
    if cfg.get("contact"):
        rows.append(("blank",))
        rows.append(("head", "Contact"))
        rows += [("kv", k, v) for k, v in cfg["contact"]]
    rows.append(("blank",))
    rows.append(("palette",))
    rows.append(("foot", f"updated {dt.datetime.utcnow():%Y-%m-%d %H:%M} UTC"))

    out = []
    y = PAD + FONT_SIZE
    for i, row in enumerate(rows):
        anim = (f'<animate attributeName="opacity" from="0" to="1" begin="{i * STEP:.2f}s" '
                f'dur="0.3s" fill="freeze"/>')
        kind = row[0]
        g = f'<g opacity="0">{anim}'
        if kind == "title":
            name, host = row[1].split("@", 1)
            out.append(f'{g}<text x="{PAD}" y="{y}"><tspan fill="{ACCENT}" font-weight="bold">{esc(name)}</tspan>'
                       f'<tspan fill="{FG}">@</tspan><tspan fill="{ACCENT}" font-weight="bold">{esc(host)}</tspan></text></g>')
        elif kind == "rule":
            out.append(f'{g}<text x="{PAD}" y="{y}" fill="{DIM}">{row[1]}</text></g>')
        elif kind == "head":
            out.append(f'{g}<text x="{PAD}" y="{y}" fill="{YELLOW}" font-weight="bold">— {esc(row[1])} —</text></g>')
        elif kind == "kv":
            key = esc(f"{row[1]}:".ljust(KEY_COL))
            out.append(f'{g}<text x="{PAD}" y="{y}" xml:space="preserve"><tspan fill="{GREEN}" font-weight="bold">{key}</tspan>'
                       f'<tspan fill="{FG}">{esc(row[2])}</tspan></text></g>')
        elif kind == "palette":
            blocks = "".join(f'<rect x="{PAD + j * 30}" y="{y - FONT_SIZE}" width="26" height="18" rx="3" fill="{c}"/>'
                             for j, c in enumerate(PALETTE))
            out.append(f"{g}{blocks}</g>")
        elif kind == "foot":
            out.append(f'{g}<text x="{PAD}" y="{y}" fill="{DIM}" font-size="11">{esc(row[1])}</text></g>')
        y += LINE_H if kind != "blank" else LINE_H // 2

    # blinking cursor after the last line
    out.append(f'<rect x="{PAD}" y="{y - FONT_SIZE}" width="9" height="16" fill="{FG}">'
               f'<animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></rect>')
    h = y + PAD
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{h}" viewBox="0 0 {WIDTH} {h}">
<rect width="{WIDTH}" height="{h}" rx="10" fill="{BG}" stroke="{BORDER}"/>
<g font-family="{FONT}" font-size="{FONT_SIZE}">
{chr(10).join(out)}
</g>
</svg>
"""


def main(stats=None):
    cfg = load_config()
    if stats is None:
        from github_data import fetch
        stats = fetch(cfg["github_user"])
    write("info.svg", build(cfg, stats))


if __name__ == "__main__":
    main()
