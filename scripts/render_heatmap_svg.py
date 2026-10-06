"""Step 5b: render data/contributions.json as an animated heatmap.

  python scripts/render_heatmap_svg.py   ->  contrib-heatmap.svg

53-week x 7-day grid of rounded boxes that slide down diagonally once on load
(CSS keyframes, then freeze), plus a Less->More legend and a stats footer.
"""
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
#           none -> brightest (level 5 is a neon top end for standout days)
W = 860
CELL, GAP = 11, 3
LEFT, TOP = 40, 58
BG, BORDER, FG, DIM = "#0d1117", "#30363d", "#c9d1d9", "#8b949e"
FONT = "'JetBrains Mono','Fira Code',Consolas,'Courier New',monospace"


def weeks_of(days):
    weeks = []
    for d in days:
        date = dt.date.fromisoformat(d["date"])
        if not weeks or (date.weekday() + 1) % 7 == 0:
            weeks.append([])
        weeks[-1].append((date, d))
    return weeks[-53:]


def neon_threshold(days):
    """Counts at or above the 95th percentile of active days get level 5."""
    active = sorted(d["count"] for d in days if d["count"])
    return active[int(len(active) * 0.95)] if len(active) >= 20 else float("inf")


def build(data):
    days, s = data["days"], data["stats"]
    weeks = weeks_of(days)
    neon = neon_threshold(days)
    grid_w = len(weeks) * (CELL + GAP) - GAP
    left = LEFT + max(0, (W - LEFT - 22 - grid_w) // 2)
    h = TOP + 7 * (CELL + GAP) + 58

    cells, months, last = [], [], None
    for x, week in enumerate(weeks):
        for date, d in week:
            y = (date.weekday() + 1) % 7
            level = 5 if d["level"] == 4 and d["count"] >= neon else d["level"]
            cx, cy = left + x * (CELL + GAP), TOP + y * (CELL + GAP)
            delay = (x + y) * 0.018
            cells.append(
                f'<rect class="c" x="{cx}" y="{cy}" width="{CELL}" height="{CELL}" rx="3" '
                f'fill="{PALETTE[level]}" style="animation-delay:{delay:.3f}s">'
                f'<title>{d["count"]} contributions on {d["date"]}</title></rect>'
            )
            if y == 0 and date.month != last and date.day <= 7 and x < len(weeks) - 1:
                months.append(f'<text x="{cx}" y="{TOP - 8}">{date:%b}</text>')
                last = date.month

    labels = "".join(f'<text x="{left - 8}" y="{TOP + i * (CELL + GAP) + 10}" text-anchor="end">{n}</text>'
                     for i, n in ((1, "Mon"), (3, "Wed"), (5, "Fri")))
    ly = h - 30
    lx = left + grid_w - len(PALETTE) * (CELL + GAP) - 34
    legend = (f'<text x="{lx - 6}" y="{ly + 10}" text-anchor="end">Less</text>'
              + "".join(f'<rect x="{lx + i * (CELL + GAP)}" y="{ly}" width="{CELL}" height="{CELL}" rx="3" fill="{c}"/>'
                        for i, c in enumerate(PALETTE))
              + f'<text x="{lx + len(PALETTE) * (CELL + GAP) + 4}" y="{ly + 10}">More</text>')
    best = s["best_day"]
    footer = (f'current streak <tspan fill="{FG}">{s["current_streak"]}d</tspan> · '
              f'longest <tspan fill="{FG}">{s["longest_streak"]}d</tspan> · '
              f'best day <tspan fill="{FG}">{best["count"]}</tspan>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}">
<style>
.c {{ opacity: 0; transform-box: fill-box; transform-origin: center;
      animation: drop .45s cubic-bezier(.2,.7,.3,1) forwards; }}
@keyframes drop {{ from {{ opacity: 0; transform: translateY(-10px) scale(.6); }}
                  to   {{ opacity: 1; transform: none; }} }}
@media (prefers-reduced-motion: reduce) {{ .c {{ animation: none; opacity: 1; }} }}
</style>
<rect x="0.5" y="0.5" width="{W - 1}" height="{h - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>
<g font-family="{FONT}">
<text x="{left}" y="30" fill="{FG}" font-size="15" font-weight="bold">{s["total"]:,} contributions in the last year</text>
<text x="{left + grid_w}" y="30" fill="{DIM}" font-size="11" text-anchor="end">@{data["user"]}</text>
<g fill="{DIM}" font-size="10">{"".join(months)}{labels}</g>
{"".join(cells)}
<g fill="{DIM}" font-size="10">{legend}<text x="{left}" y="{ly + 10}">{footer}</text></g>
</g>
</svg>
"""


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    OUT.write_text(build(data), encoding="utf-8")
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
