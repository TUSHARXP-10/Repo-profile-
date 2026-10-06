"""Step 5b: render data/contributions.json as an animated heatmap.

  python scripts/render_heatmap_svg.py   ->  contrib-heatmap.svg

53-week x 7-day grid of rounded boxes in a muted sage ramp that drop in
diagonally once on load (CSS keyframes, then freeze). Transparent background,
and label colours follow the viewer's light/dark theme.
"""
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

# none -> most active (level 5 is the top 5% of active days)
PALETTE_DARK = ["#2d342d", "#3b5236", "#56744a", "#7f9f68", "#a9c98c", "#d6edbd"]
PALETTE_LIGHT = ["#e8ebe5", "#cfe0c0", "#a9c98c", "#7f9f68", "#56744a", "#34502e"]
W = 860
LEFT, TOP = 34, 18
GAP = 2.6
FONT = "'JetBrains Mono','SF Mono','Fira Code',Consolas,'Courier New',monospace"


def weeks_of(days):
    weeks = []
    for d in days:
        date = dt.date.fromisoformat(d["date"])
        if not weeks or (date.weekday() + 1) % 7 == 0:
            weeks.append([])
        weeks[-1].append((date, d))
    return weeks[-53:]


def neon_threshold(days):
    active = sorted(d["count"] for d in days if d["count"])
    return active[int(len(active) * 0.95)] if len(active) >= 20 else float("inf")


def build(data):
    days, s = data["days"], data["stats"]
    weeks = weeks_of(days)
    neon = neon_threshold(days)
    cell = (W - LEFT - GAP * 52) / 53
    step = cell + GAP
    grid_h = 7 * step - GAP
    h = round(TOP + grid_h + 30)

    cells, months, last = [], [], None
    for x, week in enumerate(weeks):
        for date, d in week:
            y = (date.weekday() + 1) % 7
            level = 5 if d["level"] == 4 and d["count"] >= neon else d["level"]
            cells.append(
                f'<rect class="c l{level}" x="{LEFT + x * step:.1f}" y="{TOP + y * step:.1f}" '
                f'width="{cell:.1f}" height="{cell:.1f}" rx="2" style="animation-delay:{x * 0.028 + y * 0.03:.3f}s">'
                f'<title>{d["count"]} contributions on {d["date"]}</title></rect>'
            )
            if y == 0 and date.month != last and date.day <= 7 and x < len(weeks) - 2:
                months.append(f'<text x="{LEFT + x * step:.1f}" y="{TOP - 6}">{date:%b}</text>')
                last = date.month
    labels = "".join(f'<text x="{LEFT - 6}" y="{TOP + i * step + cell * 0.75:.1f}" text-anchor="end">{n}</text>'
                     for i, n in ((1, "Mon"), (3, "Wed"), (5, "Fri")))
    light = "".join(f".l{i}{{fill:{c}}}" for i, c in enumerate(PALETTE_LIGHT))
    dark = "".join(f".l{i}{{fill:{c}}}" for i, c in enumerate(PALETTE_DARK))

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}">
<style>
{light} .t {{ fill: #57606a; }} .cap {{ fill: #24292f; }}
@media (prefers-color-scheme: dark) {{ {dark} .t {{ fill: #8b949e; }} .cap {{ fill: #c9d1d9; }} }}
.c {{ opacity: 0; transform-box: fill-box; transform-origin: center;
      animation: drop .5s cubic-bezier(.2,.7,.3,1) forwards; }}
@keyframes drop {{ from {{ opacity: 0; transform: translateY(-8px) scale(.4); }}
                  to   {{ opacity: 1; transform: none; }} }}
@media (prefers-reduced-motion: reduce) {{ .c {{ animation: none; opacity: 1; }} }}
</style>
<g font-family="{FONT}">
<g class="t" font-size="10">{"".join(months)}{labels}</g>
{"".join(cells)}
<text class="cap" x="{LEFT}" y="{TOP + grid_h + 20:.1f}" font-size="11" font-weight="bold">{s["total"]:,} contributions in the last year</text>
</g>
</svg>
"""


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    OUT.write_text(build(data), encoding="utf-8")
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
