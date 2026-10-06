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


def stats(days):
    today = dt.date.today().isoformat()
    past = [d for d in days if d["date"] <= today]

    longest = run = 0
    for d in past:
        run = run + 1 if d["count"] else 0
        longest = max(longest, run)

    current = 0
    for i, d in enumerate(reversed(past)):
        if d["count"]:
            current += 1
        elif i > 0:  # today with zero doesn't break the streak yet
            break

    best = max(past, key=lambda d: d["count"]) if past else {"date": None, "count": 0}
    monthly = OrderedDict()
    for d in past:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]

    return {
        "total": sum(d["count"] for d in past),
        "current_streak": current,
        "longest_streak": longest,
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
