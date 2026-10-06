"""Render data/contributions.json as a stats dashboard terminal window.

  python scripts/render_stats_svg.py   ->  stats-card.svg

Tiles: current streak, longest streak, contributions, active days, best day,
avg per active day, plus a contributions-per-month bar chart. Tiles fade in
on a stagger and bars grow from the baseline, once, then freeze.
"""
import datetime as dt
import json
import os

from terminal import ACCENT, BAR_H, DIM, FG, H, LINE, PAD, ROOT, TILE, W, esc, window

DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "stats-card.svg"
GAP = 8
TILE_H = 64
BAR = "#7f9f68"
BAR_TOP = "#a9c98c"
STATIC = os.environ.get("STATIC") == "1"


def md(date):
    if not date:
        return "—"
    d = dt.date.fromisoformat(date)
    return f"{d:%b} {d.day}"


def span(streak):
    return f"{md(streak['start'])} – {md(streak['end'])}" if streak["days"] else "start one today"


def fade(i, inner):
    if STATIC:
        return f"<g>{inner}</g>"
    b = f"{0.2 + i * 0.12:.2f}s"
    return (f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin="{b}" dur=".4s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" from="0 6" to="0 0" begin="{b}" dur=".4s" fill="freeze"/>'
            f"{inner}</g>")


def tile(x, y, w, h, label, value, unit="", sub="", color=FG):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{TILE}" stroke="{LINE}" stroke-opacity=".7"/>'
            f'<text x="{x + 10}" y="{y + 15}" font-size="8.5" fill="{DIM}">$ {esc(label)}</text>'
            f'<text x="{x + 10}" y="{y + 39}" font-size="21" font-weight="bold" fill="{color}">{esc(value)}'
            f'<tspan font-size="9" font-weight="normal" fill="{DIM}">{"  " + esc(unit) if unit else ""}</tspan></text>'
            f'<text x="{x + 10}" y="{y + 54}" font-size="8" fill="{DIM}">{esc(sub)}</text>')


def chart(x, y, w, h, monthly):
    items = list(monthly.items())[-13:]
    peak = max((v for _, v in items), default=0) or 1
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{TILE}" stroke="{LINE}" stroke-opacity=".7"/>',
           f'<text x="{x + 10}" y="{y + 15}" font-size="8.5" fill="{DIM}">$ contributions / month</text>']
    inner_w = w - 20
    slot = inner_w / max(len(items), 1)
    bw = slot * 0.62
    base = y + h - 20
    top = y + 40
    for i, (month, v) in enumerate(items):
        bh = max(1.5, (base - top) * v / peak) if v else 1.5
        bx = x + 10 + i * slot + (slot - bw) / 2
        fill = BAR_TOP if v == peak else BAR
        delay = f"{1.0 + i * 0.06:.2f}s"
        anim = "" if STATIC else (
            f'<animate attributeName="height" from="0" to="{bh:.1f}" begin="{delay}" dur=".5s" fill="freeze" '
            f'calcMode="spline" keySplines=".2 .7 .3 1" keyTimes="0;1"/>'
            f'<animate attributeName="y" from="{base}" to="{base - bh:.1f}" begin="{delay}" dur=".5s" fill="freeze" '
            f'calcMode="spline" keySplines=".2 .7 .3 1" keyTimes="0;1"/>')
        h0 = f"{bh:.1f}" if STATIC else "0"
        y0 = f"{base - bh:.1f}" if STATIC else f"{base}"
        out.append(f'<rect x="{bx:.1f}" y="{y0}" width="{bw:.1f}" height="{h0}" rx="1.5" fill="{fill}">'
                   f'<title>{month}: {v:,}</title>{anim}</rect>')
        label = dt.date.fromisoformat(month + "-01").strftime("%b")[0]
        out.append(f'<text x="{bx + bw / 2:.1f}" y="{base + 12}" font-size="7.5" fill="{DIM}" text-anchor="middle">{label}</text>')
        if v == peak and v:
            out.append(f'<text x="{bx + bw / 2:.1f}" y="{base - bh - 4:.1f}" font-size="7.5" fill="{FG}" text-anchor="middle">{v:,}</text>')
    return "".join(out)


def build(data):
    s = data["stats"]
    tw = (W - 2 * PAD - GAP) / 2
    x1, x2 = PAD, PAD + tw + GAP
    y = BAR_H + PAD
    pct = round(100 * s["active_days"] / s["days"]) if s["days"] else 0
    best = s["best_day"]
    rows = [
        (tile(x1, y, tw, TILE_H, "current streak", s["current_streak"]["days"], "days", span(s["current_streak"]), ACCENT),
         tile(x2, y, tw, TILE_H, "longest streak", s["longest_streak"]["days"], "days", span(s["longest_streak"]))),
        (tile(x1, y + (TILE_H + GAP), tw, TILE_H, "contributions", f"{s['total']:,}", "", "in the last year"),
         tile(x2, y + (TILE_H + GAP), tw, TILE_H, "active days", s["active_days"], f"/ {s['days']}", f"{pct}% of the year")),
        (tile(x1, y + 2 * (TILE_H + GAP), tw, TILE_H, "best day", best["count"], "", md(best["date"]) if best["count"] else "—"),
         tile(x2, y + 2 * (TILE_H + GAP), tw, TILE_H, "avg / active day", s["avg_per_active_day"], "", "contributions")),
    ]
    body, i = [], 0
    for pair in rows:
        for t in pair:
            body.append(fade(i, t))
            i += 1
    cy = y + 3 * (TILE_H + GAP)
    body.append(fade(i, chart(x1, cy, W - 2 * PAD, H - PAD - cy, s["monthly"])))
    return window("snapshot ~ ./stats.sh", "\n".join(body))


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    OUT.write_text(build(data), encoding="utf-8")
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
