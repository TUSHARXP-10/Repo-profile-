"""Step 5a: scrape the public contribution calendar (no token needed).

  python scripts/fetch_contributions.py   ->  data/contributions.json

GitHub serves the calendar as HTML at /users/<username>/contributions — the
same fragment the profile page uses. We parse the day cells and derive stats.
"""
import datetime as dt
import json
import re
from collections import OrderedDict
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))
OUT = ROOT / "data" / "contributions.json"


def fetch_days(user):
    r = requests.get(
        f"https://github.com/users/{user}/contributions",
        headers={"User-Agent": "profile-art-bot"},
        timeout=30,
    )
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Counts live in <tool-tip for="<cell id>">N contributions on ...</tool-tip>
    counts = {}
    for tip in soup.find_all("tool-tip"):
        m = re.match(r"\s*(\d[\d,]*|No)\s+contribution", tip.get_text())
        if m and tip.get("for"):
            counts[tip["for"]] = 0 if m.group(1) == "No" else int(m.group(1).replace(",", ""))

    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        days.append({
            "date": td["data-date"],
            "count": counts.get(td.get("id"), 0),
            "level": int(td.get("data-level", 0)),
        })
    if not days:
        raise RuntimeError("no contribution cells found — GitHub markup may have changed")
    days.sort(key=lambda d: d["date"])
    return days


def _streaks(past):
    """Return (current, longest), each as (length, start_date, end_date)."""
    runs, start = [], None
    for i, d in enumerate(past):
        if d["count"] and start is None:
            start = i
        if start is not None and (not d["count"] or i == len(past) - 1):
            stop = i if d["count"] else i - 1
            runs.append((stop - start + 1, past[start]["date"], past[stop]["date"]))
            start = None
    longest = max(runs, default=(0, None, None))
    current = (0, None, None)
    # today with no contributions yet doesn't break a streak that ran through yesterday
    alive = {d["date"] for d in past[-2:]} if past and not past[-1]["count"] else {d["date"] for d in past[-1:]}
    if runs and runs[-1][2] in alive:
        current = runs[-1]
    return current, longest


def stats(days):
    today = dt.date.today().isoformat()
    past = [d for d in days if d["date"] <= today]
    total = sum(d["count"] for d in past)
    active = sum(1 for d in past if d["count"])
    current, longest = _streaks(past)
    best = max(past, key=lambda d: d["count"]) if past else {"date": None, "count": 0}
    monthly = OrderedDict()
    for d in past:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]
    return {
        "total": total,
        "active_days": active,
        "days": len(past),
        "avg_per_active_day": round(total / active, 1) if active else 0,
        "current_streak": {"days": current[0], "start": current[1], "end": current[2]},
        "longest_streak": {"days": longest[0], "start": longest[1], "end": longest[2]},
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": monthly,
    }


def main():
    user = CFG["github_user"]
    days = fetch_days(user)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({
        "user": user,
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "stats": stats(days),
        "days": days,
    }, indent=1), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(days)} days)")


if __name__ == "__main__":
    main()
