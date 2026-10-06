"""Fetch profile stats and the contribution calendar.

Uses the GraphQL API when GH_TOKEN / GITHUB_TOKEN is set, otherwise falls
back to the public REST API + the public contributions HTML fragment.
"""
import datetime as dt
import os
import re

import requests

API = "https://api.github.com"
LEVELS = {
    "NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4,
}

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      totalCount
      nodes { stargazerCount }
    }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
  }
}
"""


def _token():
    return os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")


def _graphql(user, token):
    r = requests.post(
        f"{API}/graphql",
        json={"query": QUERY, "variables": {"login": user}},
        headers={"Authorization": f"bearer {token}"},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("errors"):
        raise RuntimeError(data["errors"])
    u = data["data"]["user"]
    cal = u["contributionsCollection"]["contributionCalendar"]
    weeks = [
        [(d["date"], d["contributionCount"], LEVELS.get(d["contributionLevel"], 0))
         for d in w["contributionDays"]]
        for w in cal["weeks"]
    ]
    return {
        "repos": u["repositories"]["totalCount"],
        "stars": sum(n["stargazerCount"] for n in u["repositories"]["nodes"]),
        "followers": u["followers"]["totalCount"],
        "total": cal["totalContributions"],
        "weeks": weeks,
    }


def _public(user):
    s = requests.Session()
    s.headers["User-Agent"] = "profile-readme-builder"
    stats = {"repos": 0, "stars": 0, "followers": 0}
    try:
        u = s.get(f"{API}/users/{user}", timeout=30).json()
        repos = s.get(f"{API}/users/{user}/repos?per_page=100&type=owner", timeout=30).json()
        stats["repos"] = u.get("public_repos", 0)
        stats["followers"] = u.get("followers", 0)
        stats["stars"] = sum(r.get("stargazers_count", 0) for r in repos if isinstance(r, dict))
    except (requests.RequestException, ValueError) as e:
        print(f"warning: REST stats failed: {e}")

    days = []
    try:
        html = s.get(f"https://github.com/users/{user}/contributions", timeout=30).text
        # Counts live in <tool-tip for="contribution-day-component-X-Y">N contributions ...</tool-tip>
        tips = {}
        for tid, txt in re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', html):
            m = re.match(r"\s*(\d+)", txt)
            tips[tid] = int(m.group(1)) if m else 0
        for attrs in re.findall(r"<td([^>]*ContributionCalendar-day[^>]*)>", html):
            date = re.search(r'data-date="([\d-]+)"', attrs)
            level = re.search(r'data-level="(\d)"', attrs)
            tid = re.search(r'id="([^"]+)"', attrs)
            if date:
                days.append((date.group(1), tips.get(tid.group(1), 0) if tid else 0,
                             int(level.group(1)) if level else 0))
    except requests.RequestException as e:
        print(f"warning: contributions scrape failed: {e}")

    days.sort()
    weeks, cur = [], []
    for d in days:
        wd = (dt.date.fromisoformat(d[0]).weekday() + 1) % 7  # Sunday = 0
        if cur and wd == 0:
            weeks.append(cur)
            cur = []
        cur.append(d)
    if cur:
        weeks.append(cur)
    stats["weeks"] = weeks
    stats["total"] = sum(d[1] for d in days)
    return stats


def fetch(user):
    token = _token()
    if token:
        try:
            return _graphql(user, token)
        except (requests.RequestException, RuntimeError, KeyError, TypeError) as e:
            print(f"warning: GraphQL failed ({e}), falling back to public data")
    return _public(user)
