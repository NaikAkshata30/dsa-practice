#!/usr/bin/env python3

from __future__ import annotations

import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, datetime, timedelta
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo


# ============================================================
# CONFIGURATION
# ============================================================

HANDLE = "ashcodes._"
TIMEZONE = "Asia/Kolkata"

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "assets" / "codeforces-analytics.svg"

API_BASE = "https://codeforces.com/api"

# Codeforces asks clients not to make API calls more often
# than once every two seconds.
API_DELAY = 2.1


# ============================================================
# API HELPERS
# ============================================================

_last_api_call = 0.0


def api_get(method: str, params: dict | None = None) -> dict:
    """Call a public Codeforces API method."""

    global _last_api_call

    elapsed = time.time() - _last_api_call

    if elapsed < API_DELAY:
        time.sleep(API_DELAY - elapsed)

    query = urllib.parse.urlencode(params or {})
    url = f"{API_BASE}/{method}"

    if query:
        url += f"?{query}"

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "dsa-practice-codeforces-dashboard/1.0"
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"Could not fetch Codeforces API: {error}"
        ) from error

    _last_api_call = time.time()

    if payload.get("status") != "OK":
        raise RuntimeError(
            payload.get(
                "comment",
                f"Codeforces API failed for {method}",
            )
        )

    return payload["result"]


def fetch_profile() -> dict:
    """Fetch Codeforces profile information."""

    result = api_get(
        "user.info",
        {"handles": HANDLE},
    )

    if not result:
        raise RuntimeError(
            f"Codeforces handle '{HANDLE}' was not found."
        )

    return result[0]


def fetch_submissions() -> list[dict]:
    """Fetch public submission history."""

    return api_get(
        "user.status",
        {
            "handle": HANDLE,
            "from": 1,
            "count": 10000,
        },
    )


def fetch_rating_history() -> list[dict]:
    """Fetch Codeforces rating history."""

    return api_get(
        "user.rating",
        {"handle": HANDLE},
    )

# ============================================================
# DATA PROCESSING
# ============================================================

def problem_key(problem: dict) -> tuple[str, str]:
    """Return a stable identity for a Codeforces problem."""

    contest_id = problem.get("contestId")

    if contest_id is None:
        contest_id = problem.get("problemsetName", "unknown")

    index = problem.get("index", "unknown")

    return str(contest_id), str(index)


def accepted_submissions(submissions: list[dict]) -> list[dict]:
    """Return accepted submissions only."""

    return [
        submission
        for submission in submissions
        if submission.get("verdict") == "OK"
    ]


def unique_solved_problems(
    submissions: list[dict],
) -> list[dict]:
    """
    Return the first accepted submission for every unique problem,
    preserving solve order.
    """

    solved = set()
    result = []

    for submission in sorted(
        submissions,
        key=lambda item: item.get(
            "creationTimeSeconds",
            0,
        ),
    ):
        if submission.get("verdict") != "OK":
            continue

        problem = submission.get("problem", {})
        key = problem_key(problem)

        if key in solved:
            continue

        solved.add(key)

        result.append(submission)

    return result


def submission_dates(
    solved: list[dict],
) -> list[date]:
    """Get dates on which unique problems were solved."""

    timezone = ZoneInfo(TIMEZONE)

    return [
        datetime.fromtimestamp(
            submission["creationTimeSeconds"],
            timezone,
        ).date()
        for submission in solved
    ]


def calculate_streaks(
    dates: list[date],
) -> tuple[int, int]:
    """Calculate current and maximum solving streak."""

    unique_dates = sorted(set(dates))

    if not unique_dates:
        return 0, 0

    date_set = set(unique_dates)

    # Maximum streak
    best = 1
    current_run = 1

    for previous, current in zip(
        unique_dates,
        unique_dates[1:],
    ):
        if current == previous + timedelta(days=1):
            current_run += 1
            best = max(best, current_run)
        else:
            current_run = 1

    # Current streak
    today = datetime.now(
        ZoneInfo(TIMEZONE)
    ).date()

    if today not in date_set:
        current = today - timedelta(days=1)
    else:
        current = today

    current_streak = 0

    while current in date_set:
        current_streak += 1
        current -= timedelta(days=1)

    return current_streak, best


def daily_activity(
    submissions: list[dict],
) -> Counter:
    """
    Count accepted unique-problem solves per day.
    """

    timezone = ZoneInfo(TIMEZONE)
    counts = Counter()
    solved = set()

    for submission in sorted(
        submissions,
        key=lambda item: item.get(
            "creationTimeSeconds",
            0,
        ),
    ):
        if submission.get("verdict") != "OK":
            continue

        problem = submission.get("problem", {})
        key = problem_key(problem)

        if key in solved:
            continue

        solved.add(key)

        day = datetime.fromtimestamp(
            submission["creationTimeSeconds"],
            timezone,
        ).date()

        counts[day] += 1

    return counts


# ============================================================
# SVG HELPERS
# ============================================================

def svg_text(
    x: float,
    y: float,
    text: str,
    size: int = 14,
    color: str = "#c9d1d9",
    weight: int = 400,
    anchor: str = "start",
) -> str:

    return (
        f'<text x="{x}" y="{y}" '
        f'font-size="{size}" '
        f'font-weight="{weight}" '
        f'fill="{color}" '
        f'text-anchor="{anchor}" '
        f'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,'
        f'Helvetica,Arial,sans-serif">'
        f'{escape(str(text))}</text>'
    )


def rounded_card(
    x: int,
    y: int,
    width: int,
    height: int,
) -> str:

    return (
        f'<rect x="{x}" y="{y}" '
        f'width="{width}" height="{height}" '
        f'rx="14" '
        f'fill="#0d1117" '
        f'stroke="#30363d" '
        f'stroke-width="1.2"/>'
    )


def section_title(
    x: int,
    y: int,
    title: str,
) -> str:

    return svg_text(
        x,
        y,
        title,
        size=24,
        color="#58a6ff",
        weight=600,
    )


def format_number(value: int | float) -> str:
    """Format large numbers compactly."""

    if isinstance(value, float):
        value = int(value)

    return f"{value:,}"


# ============================================================
# OVERVIEW PANEL
# ============================================================

def render_overview(
    profile: dict,
    solved_count: int,
    current_streak: int,
    best_streak: int,
) -> list[str]:

    lines = []

    x = 40
    y = 110
    width = 660
    height = 385

    lines.append(
        rounded_card(
            x,
            y,
            width,
            height,
        )
    )

    lines.append(
        section_title(
            x + 28,
            y + 48,
            "Overview",
        )
    )

    rating = profile.get("rating", "Unrated")
    rank = profile.get("rank", "Unrated")
    contribution = profile.get(
        "contribution",
        0,
    )

    stats = [
        ("Problems Solved", solved_count, "#3fb950"),
        ("Current Streak", f"{current_streak} days", "#ff7b72"),
        ("Max Streak", f"{best_streak} days", "#a371f7"),
        ("Rating", rating, "#f2cc60"),
        ("Rank", rank, "#58a6ff"),
        ("Contribution", contribution, "#58a6ff"),
    ]

    start_y = y + 105

    for index, (label, value, color) in enumerate(stats):

        row_y = start_y + index * 43

        lines.append(
            svg_text(
                x + 30,
                row_y,
                "●",
                size=14,
                color=color,
                weight=700,
            )
        )

        lines.append(
            svg_text(
                x + 55,
                row_y,
                f"{label}:",
                size=15,
                color="#8b949e",
            )
        )

        lines.append(
            svg_text(
                x + 330,
                row_y,
                format_number(value)
                if isinstance(value, int)
                else value,
                size=16,
                color="#58a6ff",
                weight=600,
            )
        )

    # Provenance callout (all displayed values come from public API data).
    cx = x + 530
    cy = y + 205

    lines.append(
        f'<rect x="{cx - 92}" y="{cy - 66}" width="184" height="132" '
        f'rx="16" fill="#161b22" stroke="#30363d"/>'
    )

    lines.append(
        svg_text(
            cx,
            cy - 18,
            "PUBLIC API",
            size=13,
            color="#3fb950",
            weight=700,
            anchor="middle",
        )
    )

    lines.append(svg_text(cx, cy + 12, "Verified profile data", size=13,
                          color="#f0f6fc", weight=600, anchor="middle"))
    lines.append(svg_text(cx, cy + 38, f"@{HANDLE}", size=12,
                          color="#8b949e", anchor="middle"))

    return lines


# ============================================================
# SUBMISSION ACTIVITY PANEL
# ============================================================

def render_activity(
    activity: Counter,
    today: date,
) -> list[str]:

    lines = []

    x = 720
    y = 110
    width = 740
    height = 385

    lines.append(
        rounded_card(
            x,
            y,
            width,
            height,
        )
    )

    lines.append(
        section_title(
            x + 28,
            y + 48,
            "Submissions Activity (per day)",
        )
    )

    # Last 30 days
    days = [
        today - timedelta(days=i)
        for i in range(29, -1, -1)
    ]

    values = [
        activity.get(day, 0)
        for day in days
    ]

    max_value = max(values, default=1)

    chart_x = x + 75
    chart_y = y + 95
    chart_width = 600
    chart_height = 220

    # Grid lines
    for level in range(6):

        value = max(
            0,
            math.ceil(
                max_value * level / 5
            ),
        )

        gy = (
            chart_y
            + chart_height
            - level * chart_height / 5
        )

        lines.append(
            f'<line x1="{chart_x}" y1="{gy}" '
            f'x2="{chart_x + chart_width}" y2="{gy}" '
            f'stroke="#21262d" stroke-width="1"/>'
        )

        lines.append(
            svg_text(
                chart_x - 12,
                gy + 5,
                value,
                size=10,
                color="#8b949e",
                anchor="end",
            )
        )

    bar_gap = 3
    bar_width = (
        chart_width / len(days)
    ) - bar_gap

    for index, value in enumerate(values):

        bar_height = (
            value / max_value
        ) * chart_height if max_value else 0

        bx = (
            chart_x
            + index * (
                bar_width + bar_gap
            )
        )

        by = (
            chart_y
            + chart_height
            - bar_height
        )

        lines.append(
            f'<rect x="{bx:.2f}" y="{by:.2f}" '
            f'width="{bar_width:.2f}" '
            f'height="{max(bar_height, 2):.2f}" '
            f'rx="3" fill="#6e40c9">'
            f'<title>{value} problem(s) solved on '
            f'{days[index].strftime("%b %d, %Y")}</title>'
            f'</rect>'
        )

    # X-axis labels
    label_indexes = [
        0,
        7,
        14,
        21,
        29,
    ]

    for index in label_indexes:

        lx = (
            chart_x
            + index * (
                bar_width + bar_gap
            )
            + bar_width / 2
        )

        lines.append(
            svg_text(
                lx,
                chart_y + chart_height + 28,
                days[index].strftime("%b %d"),
                size=10,
                color="#8b949e",
                anchor="middle",
            )
        )

    lines.append(
        svg_text(
            chart_x + chart_width / 2,
            chart_y + chart_height + 55,
            "Last 30 Days",
            size=12,
            color="#8b949e",
            anchor="middle",
        )
    )

    return lines


# ============================================================
# MAIN SVG
# ============================================================

def render_dashboard(
    profile: dict,
    solved: list[dict],
    submissions: list[dict],
) -> str:

    timezone = ZoneInfo(TIMEZONE)

    today = datetime.now(
        timezone
    ).date()

    dates = submission_dates(solved)

    current_streak, best_streak = calculate_streaks(
        dates
    )

    activity = daily_activity(
        submissions
    )


    solved_count = len(solved)

    WIDTH = 1500
    HEIGHT = 560

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}">',
        """
        <defs>
            <linearGradient id="background"
                            x1="0" y1="0"
                            x2="1" y2="1">
                <stop offset="0%" stop-color="#0d1117"/>
                <stop offset="100%" stop-color="#090c10"/>
            </linearGradient>
        </defs>
        """,
        f'<rect width="{WIDTH}" height="{HEIGHT}" '
        f'fill="url(#background)"/>',
        f'<rect x="18" y="18" '
        f'width="{WIDTH - 36}" '
        f'height="{HEIGHT - 36}" '
        f'rx="16" '
        f'fill="none" '
        f'stroke="#30363d"/>',
    ]

    # Header
    lines.append(
        svg_text(
            45,
            78,
            "Codeforces Analytics",
            size=32,
            color="#f0f6fc",
            weight=600,
        )
    )

    lines.append(
        svg_text(
            WIDTH - 45,
            76,
            f"@{HANDLE}",
            size=13,
            color="#8b949e",
            anchor="end",
        )
    )

    # Panels
    lines.extend(
        render_overview(
            profile,
            solved_count,
            current_streak,
            best_streak,
        )
    )

    lines.extend(
        render_activity(
            activity,
            today,
        )
    )


    # Footer
    lines.append(
        svg_text(
            WIDTH / 2,
            HEIGHT - 28,
            "Data fetched from Codeforces API • "
            "Automatically generated",
            size=12,
            color="#8b949e",
            anchor="middle",
        )
    )

    lines.append("</svg>")

    return "\n".join(lines)


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    print(
        f"Fetching Codeforces data for @{HANDLE}..."
    )

    profile = fetch_profile()

    print("Fetching submissions...")
    submissions = fetch_submissions()

    print("Fetching rating history...")
    rating_history = fetch_rating_history()

    solved = unique_solved_problems(
        submissions
    )

    dashboard = render_dashboard(
        profile,
        solved,
        submissions,
    )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT.write_text(
        dashboard,
        encoding="utf-8",
        newline="\n",
    )

    ratings = [
        metadata.get("rating")
        for _, metadata in []
    ]

    print()
    print("Codeforces dashboard generated successfully.")
    print(f"Handle: @{HANDLE}")
    print(f"Problems solved: {len(solved)}")
    print(f"Submissions fetched: {len(submissions)}")
    print(f"Rating history entries: {len(rating_history)}")
    print(f"Output: {OUTPUT}")


if __name__ == "__main__":
    main()
