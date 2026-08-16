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


def fetch_problemset() -> list[dict]:
    """
    Fetch Codeforces problem metadata.

    The problemset endpoint provides problem ratings and tags.
    """

    result = api_get("problemset.problems")

    return result["problems"]


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


def build_problem_map(
    problems: list[dict],
) -> dict[tuple[str, str], dict]:
    """Map problem identity to metadata."""

    return {
        problem_key(problem): problem
        for problem in problems
    }


def pattern_counts(
    solved: list[dict],
    problem_map: dict[tuple[str, str], dict],
) -> Counter:
    """
    Count Codeforces tags across unique solved problems.

    A problem contributes at most once to each tag.
    """

    counts = Counter()

    for submission in solved:
        problem = submission.get("problem", {})
        key = problem_key(problem)

        metadata = problem_map.get(key, problem)

        for tag in metadata.get("tags", []):
            counts[tag] += 1

    return counts


def difficulty_data(
    solved: list[dict],
    problem_map: dict[tuple[str, str], dict],
) -> list[tuple[int, int]]:
    """
    Return:
        (solve_number, problem_rating)

    for every solved problem that has a rating.
    """

    result = []

    for index, submission in enumerate(solved, start=1):
        problem = submission.get("problem", {})
        key = problem_key(problem)

        metadata = problem_map.get(key, problem)
        rating = metadata.get("rating")

        if isinstance(rating, int):
            result.append((index, rating))

    return result


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

    # Decorative circular chart area
    cx = x + 530
    cy = y + 205

    lines.append(
        f'<circle cx="{cx}" cy="{cy}" r="82" '
        f'fill="#0d1117" '
        f'stroke="#30363d" stroke-width="2"/>'
    )

    bar_values = [
        (35, "#f2cc60"),
        (58, "#58a6ff"),
        (45, "#f85149"),
    ]

    bar_width = 26
    gap = 15

    start_x = cx - (
        (len(bar_values) * bar_width)
        + ((len(bar_values) - 1) * gap)
    ) / 2

    for i, (bar_height, color) in enumerate(bar_values):

        bx = start_x + i * (
            bar_width + gap
        )

        by = cy + 35 - bar_height

        lines.append(
            f'<rect x="{bx}" y="{by}" '
            f'width="{bar_width}" '
            f'height="{bar_height}" '
            f'rx="7" fill="{color}"/>'
        )

    lines.append(
        svg_text(
            cx,
            y + 340,
            f"@{HANDLE}",
            size=14,
            color="#8b949e",
            anchor="middle",
        )
    )

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
# PROBLEM PATTERNS PANEL
# ============================================================

PATTERN_COLORS = [
    "#3fb950",
    "#f2cc60",
    "#58a6ff",
    "#a371f7",
    "#ff7b72",
    "#db61a2",
]


def render_patterns(
    counts: Counter,
    total_solved: int,
) -> list[str]:

    lines = []

    x = 40
    y = 515
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
            "Problem Patterns",
        )
    )

    top_patterns = counts.most_common(6)

    if not top_patterns:
        lines.append(
            svg_text(
                x + 30,
                y + 110,
                "No tagged problems available yet.",
                size=14,
                color="#8b949e",
            )
        )

        return lines

    card_width = 185
    card_height = 105

    positions = [
        (x + 25, y + 75),
        (x + 225, y + 75),
        (x + 425, y + 75),
        (x + 25, y + 195),
        (x + 225, y + 195),
        (x + 425, y + 195),
    ]

    for index, (tag, count) in enumerate(
        top_patterns
    ):

        px, py = positions[index]
        color = PATTERN_COLORS[
            index % len(PATTERN_COLORS)
        ]

        lines.append(
            f'<rect x="{px}" y="{py}" '
            f'width="{card_width}" '
            f'height="{card_height}" '
            f'rx="10" '
            f'fill="#161b22" '
            f'stroke="#30363d"/>'
        )

        percentage = (
            count / total_solved * 100
            if total_solved
            else 0
        )

        lines.append(
            svg_text(
                px + 15,
                py + 32,
                tag.title(),
                size=15,
                color="#c9d1d9",
                weight=500,
            )
        )

        lines.append(
            svg_text(
                px + 15,
                py + 66,
                count,
                size=23,
                color=color,
                weight=600,
            )
        )

        lines.append(
            svg_text(
                px + card_width - 15,
                py + 66,
                f"{percentage:.1f}%",
                size=12,
                color="#8b949e",
                anchor="end",
            )
        )

        progress_width = (
            (card_width - 30)
            * percentage
            / 100
        )

        lines.append(
            f'<rect x="{px + 15}" '
            f'y="{py + 82}" '
            f'width="{card_width - 30}" '
            f'height="7" rx="3.5" '
            f'fill="#21262d"/>'
        )

        lines.append(
            f'<rect x="{px + 15}" '
            f'y="{py + 82}" '
            f'width="{progress_width:.2f}" '
            f'height="7" rx="3.5" '
            f'fill="{color}"/>'
        )

    unique_patterns = len(counts)

    lines.append(
        svg_text(
            x + 30,
            y + 350,
            f"Total Problems: {total_solved}   •   "
            f"Unique Patterns: {unique_patterns}",
            size=13,
            color="#8b949e",
        )
    )

    return lines


# ============================================================
# DIFFICULTY PROGRESSION PANEL
# ============================================================

def render_difficulty(
    difficulty: list[tuple[int, int]],
) -> list[str]:

    lines = []

    x = 720
    y = 515
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
            "Difficulty Progression",
        )
    )

    if not difficulty:

        lines.append(
            svg_text(
                x + 30,
                y + 120,
                "Problem ratings will appear as rated problems are solved.",
                size=14,
                color="#8b949e",
            )
        )

        return lines

    chart_x = x + 75
    chart_y = y + 85
    chart_width = 430
    chart_height = 245

    ratings = [
        rating
        for _, rating in difficulty
    ]

    min_rating = min(ratings)
    max_rating = max(ratings)

    lower = (
        min_rating // 100
    ) * 100

    upper = (
        math.ceil(max_rating / 100)
    ) * 100

    if lower == upper:
        lower -= 100
        upper += 100

    # Horizontal grid
    tick_values = list(
        range(
            lower,
            upper + 1,
            100,
        )
    )

    for rating in tick_values:

        ratio = (
            rating - lower
        ) / (
            upper - lower
        )

        gy = (
            chart_y
            + chart_height
            - ratio * chart_height
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
                rating,
                size=10,
                color="#8b949e",
                anchor="end",
            )
        )

    # X-axis
    if len(difficulty) == 1:
        x_positions = [
            chart_x + chart_width / 2
        ]
    else:
        x_positions = [
            chart_x
            + i * chart_width
            / (len(difficulty) - 1)
            for i in range(
                len(difficulty)
            )
        ]

    points = []

    for (solve_number, rating), px in zip(
        difficulty,
        x_positions,
    ):

        ratio = (
            rating - lower
        ) / (
            upper - lower
        )

        py = (
            chart_y
            + chart_height
            - ratio * chart_height
        )

        points.append(
            (px, py)
        )

    # Connecting line
    if len(points) > 1:

        point_string = " ".join(
            f"{px:.1f},{py:.1f}"
            for px, py in points
        )

        lines.append(
            f'<polyline points="{point_string}" '
            f'fill="none" '
            f'stroke="#58a6ff" '
            f'stroke-width="3" '
            f'stroke-linecap="round" '
            f'stroke-linejoin="round"/>'
        )

    # Points
    for index, (
        (solve_number, rating),
        (px, py),
    ) in enumerate(
        zip(difficulty, points)
    ):

        is_latest = (
            index == len(points) - 1
        )

        lines.append(
            f'<circle cx="{px:.1f}" '
            f'cy="{py:.1f}" '
            f'r="{8 if is_latest else 5}" '
            f'fill="#0d1117" '
            f'stroke="{ "#3fb950" if is_latest else "#58a6ff" }" '
            f'stroke-width="3">'
            f'<title>Problem {solve_number}: '
            f'{rating}</title>'
            f'</circle>'
        )

    lines.append(
        svg_text(
            chart_x + chart_width / 2,
            chart_y + chart_height + 38,
            "Problems Solved (in order)",
            size=12,
            color="#8b949e",
            anchor="middle",
        )
    )

    # Insights card
    card_x = x + 520
    card_y = y + 88
    card_width = 190
    card_height = 245

    lines.append(
        f'<rect x="{card_x}" y="{card_y}" '
        f'width="{card_width}" '
        f'height="{card_height}" '
        f'rx="10" '
        f'fill="#161b22" '
        f'stroke="#30363d"/>'
    )

    highest = max(ratings)

    first_rating = ratings[0]
    latest_rating = ratings[-1]
    rating_gain = latest_rating - first_rating

    insights = [
        (
            "Highest Rating",
            highest,
            "#3fb950",
        ),
        (
            "Latest Rating",
            latest_rating,
            "#58a6ff",
        ),
        (
            "Rating Change",
            f"{rating_gain:+d}",
            "#a371f7",
        ),
    ]

    for index, (
        label,
        value,
        color,
    ) in enumerate(insights):

        iy = card_y + 48 + index * 62

        lines.append(
            svg_text(
                card_x + 20,
                iy,
                label,
                size=12,
                color="#8b949e",
            )
        )

        lines.append(
            svg_text(
                card_x + 20,
                iy + 25,
                value,
                size=21,
                color=color,
                weight=600,
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
    problem_map: dict[tuple[str, str], dict],
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

    patterns = pattern_counts(
        solved,
        problem_map,
    )

    difficulty = difficulty_data(
        solved,
        problem_map,
    )

    solved_count = len(solved)

    WIDTH = 1500
    HEIGHT = 950

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

    lines.extend(
        render_patterns(
            patterns,
            solved_count,
        )
    )

    lines.extend(
        render_difficulty(
            difficulty,
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

    print("Fetching problem metadata...")
    problemset = fetch_problemset()

    solved = unique_solved_problems(
        submissions
    )

    problem_map = build_problem_map(
        problemset
    )

    dashboard = render_dashboard(
        profile,
        solved,
        submissions,
        problem_map,
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
    print(f"Problem metadata entries: {len(problemset)}")
    print(f"Output: {OUTPUT}")


if __name__ == "__main__":
    main()