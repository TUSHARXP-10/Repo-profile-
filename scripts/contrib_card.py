"""Step 5: animated contribution heatmap (assets/contrib.svg)."""
import datetime as dt

from common import BG, BORDER, DIM, FG, FONT, esc, load_config, write

COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
CELL = 11
GAP = 3
PAD = 24
TOP = 46
LEFT = 34


def build(user, stats):
    weeks = stats["weeks"]
    ncols = max(len(weeks), 1)
    w = LEFT + ncols * (CELL + GAP) + PAD - GAP
    h = TOP + 7 * (CELL + GAP) + 40
    cells, months, last_month = [], [], None
    for x, week in enumerate(weeks):
        for date, count, level in week:
            d = dt.date.fromisoformat(date)
            y = (d.weekday() + 1) % 7
            cx = LEFT + x * (CELL + GAP)
            cy = TOP + y * (CELL + GAP)
            delay = x * 0.03 + y * 0.01
            cells.append(
                f'<rect x="{cx}" y="{cy}" width="{CELL}" height="{CELL}" rx="2" fill="{COLORS[level]}" opacity="0">'
                f'<title>{count} contributions on {date}</title>'
                f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.2f}s" dur="0.4s" fill="freeze"/></rect>'
            )
            if y == 0 and d.month != last_month and d.day <= 7:
                months.append(f'<text x="{cx}" y="{TOP - 8}">{d:%b}</text>')
                last_month = d.month
    days = "".join(f'<text x="{PAD - 14}" y="{TOP + i * (CELL + GAP) + 9}">{n}</text>'
                   for i, n in ((1, "Mon"), (3, "Wed"), (5, "Fri")))
    legend_x = w - PAD - 5 * (CELL + GAP) - 62
    legend = "".join(f'<rect x="{legend_x + 30 + i * (CELL + GAP)}" y="{h - 26}" width="{CELL}" height="{CELL}" rx="2" fill="{c}"/>'
                     for i, c in enumerate(COLORS))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<rect width="{w}" height="{h}" rx="10" fill="{BG}" stroke="{BORDER}"/>
<g font-family="{FONT}">
<text x="{PAD}" y="24" fill="{FG}" font-size="14" font-weight="bold">{stats['total']} contributions in the last year · @{esc(user)}</text>
<g fill="{DIM}" font-size="9">{''.join(months)}{days}
<text x="{legend_x}" y="{h - 17}">Less</text><text x="{legend_x + 32 + 5 * (CELL + GAP)}" y="{h - 17}">More</text></g>
{''.join(cells)}
{legend}
</g>
</svg>
"""


def main(stats=None):
    cfg = load_config()
    if stats is None:
        from github_data import fetch
        stats = fetch(cfg["github_user"])
    write("contrib.svg", build(cfg["github_user"], stats))


if __name__ == "__main__":
    main()
