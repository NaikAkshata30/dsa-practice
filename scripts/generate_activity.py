#!/usr/bin/env python3
"""
Generate a custom DSA activity dashboard from public Codeforces submissions.
"""

from __future__ import annotations

import argparse
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


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

API_URL = "https://codeforces.com/api/user.status"

DEFAULT_HANDLE = "ashcodes._"
DEFAULT_TIMEZONE = "Asia/Kolkata"

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "assets" / "daily-activity.svg"


# ---------------------------------------------------------
# Codeforces API
# ---------------------------------------------------------

def fetch_submissions(handle: str, attempts: int = 3) -> list[dict]:
    """Fetch public Codeforces submissions for a user."""

    query = urllib.parse.urlencode(
        {
            "handle": handle,
            "from": 1,
            "count": 10000,
        }
    )

    url = f"{API_URL}?{query}"

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "dsa-practice-activity/1.0"
        },
    )

    for attempt in range(1, attempts + 1):

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.load(response)

            if payload.get("status") != "OK":
                raise RuntimeError(
                    payload.get(
                        "comment",
                        "Unknown Codeforces API error"
                    )
                )

            return payload["result"]

        except (
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
        ) as error:

            if attempt == attempts:
                raise RuntimeError(
                    f"Unable to access Codeforces API: {error}"
                ) from error

            time.sleep(2 ** (attempt - 1))

    raise RuntimeError("Unable to access Codeforces API")


# ---------------------------------------------------------
# Problem identification
# ---------------------------------------------------------

def problem_key(problem: dict) -> tuple[str, str]:
    """
    Create a stable identifier for a Codeforces problem.
    """

    contest_id = (
        problem.get("contestId")
        or problem.get("problemsetName")
        or "unknown"
    )

    index = (
        problem.get("index")
        or problem.get("name")
        or "unknown"
    )

    return str(contest_id), str(index)


# ---------------------------------------------------------
# Accepted problems
# ---------------------------------------------------------

def get_solved_problem_dates(
    submissions: list[dict],
    timezone_name: str,
) -> list[date]:
    """
    Find the first accepted date for every unique problem.
    """

    timezone = ZoneInfo(timezone_name)

    solved_problems: set[tuple[str, str]] = set()

    solved_dates: list[date] = []

    # Oldest → newest
    submissions = sorted(
        submissions,
        key=lambda item: item["creationTimeSeconds"],
    )

    for submission in submissions:

        if submission.get("verdict") != "OK":
            continue

        problem = submission.get("problem", {})

        key = problem_key(problem)

        # Already counted this problem
        if key in solved_problems:
            continue

        solved_problems.add(key)

        solved_at = datetime.fromtimestamp(
            submission["creationTimeSeconds"],
            timezone,
        )

        solved_dates.append(solved_at.date())

    return solved_dates


# ---------------------------------------------------------
# Statistics
# ---------------------------------------------------------

def calculate_streaks(
    activity: Counter,
    today: date,
) -> tuple[int, int]:
    """
    Return current streak and longest streak.
    """

    active_days = sorted(
        day for day, count in activity.items()
        if count > 0
    )

    if not active_days:
        return 0, 0

    # Longest streak
    longest = 1
    running = 1

    for index in range(1, len(active_days)):

        previous = active_days[index - 1]
        current = active_days[index]

        if (current - previous).days == 1:
            running += 1
            longest = max(longest, running)
        else:
            running = 1

    # Current streak
    if today in activity:

        current_streak = 1
        check = today - timedelta(days=1)

        while check in activity:

            current_streak += 1
            check -= timedelta(days=1)

    elif today - timedelta(days=1) in activity:

        current_streak = 1
        check = today - timedelta(days=2)

        while check in activity:

            current_streak += 1
            check -= timedelta(days=1)

    else:
        current_streak = 0

    return current_streak, longest


def contribution_level(
    count: int,
    maximum: int,
) -> int:
    """
    Convert a daily problem count into a visual level from 0–4.
    """

    if count <= 0:
        return 0

    if maximum <= 1:
        return 4

    return min(
        4,
        max(
            1,
            math.ceil((count / maximum) * 4),
        ),
    )


# ---------------------------------------------------------
# SVG generation
# ---------------------------------------------------------

def generate_svg(
    handle: str,
    solved_dates: list[date],
    today: date,
    timezone_name: str,
) -> str:

    activity = Counter(solved_dates)

    # -----------------------------------------------------
    # Date range
    # -----------------------------------------------------

    year_ago = today - timedelta(days=364)

    # Start calendar on Sunday.
    days_since_sunday = (
        today.weekday() + 1
    ) % 7

    current_week_start = (
        today - timedelta(days=days_since_sunday)
    )

    start = current_week_start - timedelta(weeks=52)

    # -----------------------------------------------------
    # Statistics
    # -----------------------------------------------------

    total_solved = len(solved_dates)

    last_year_solved = sum(
        count
        for day, count in activity.items()
        if year_ago <= day <= today
    )

    last_month_start = today - timedelta(days=30)

    last_month_solved = sum(
        count
        for day, count in activity.items()
        if last_month_start <= day <= today
    )

    active_days = sum(
        1
        for day, count in activity.items()
        if year_ago <= day <= today and count > 0
    )

    current_streak, longest_streak = calculate_streaks(
        activity,
        today,
    )

    recent_max = max(
        (
            count
            for day, count in activity.items()
            if year_ago <= day <= today
        ),
        default=1,
    )

    # -----------------------------------------------------
    # Layout
    # -----------------------------------------------------

    cell = 12
    gap = 4
    pitch = cell + gap

    grid_x = 70
    grid_y = 92

    weeks = 53

    width = 920
    height = 335

    # -----------------------------------------------------
    # Colors
    # -----------------------------------------------------

    colors = [
        "#161b22",
        "#0e4429",
        "#006d32",
        "#26a641",
        "#39d353",
    ]

    # -----------------------------------------------------
    # SVG start
    # -----------------------------------------------------

    lines = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" '
            f'role="img" aria-labelledby="title description">'
        ),

        f'<title id="title">'
        f'{escape(handle)} DSA solving activity'
        f'</title>',

        (
            f'<desc id="description">'
            f'{total_solved} problems solved across '
            f'{active_days} active days in the last year.'
            f'</desc>'
        ),

        "<style>",

        """
        text {
            font-family:
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                sans-serif;
        }

        .title {
            fill: #f0f6fc;
            font-size: 18px;
            font-weight: 700;
        }

        .subtitle {
            fill: #8b949e;
            font-size: 12px;
        }

        .label {
            fill: #8b949e;
            font-size: 10px;
        }

        .stat-value {
            fill: #f0f6fc;
            font-size: 17px;
            font-weight: 700;
        }

        .stat-label {
            fill: #8b949e;
            font-size: 10px;
        }

        .cell {
            stroke: #30363d;
            stroke-width: 0.7;
        }

        .count {
            fill: #ffffff;
            font-size: 8px;
            font-weight: 700;
            pointer-events: none;
        }
        """,

        "</style>",

        (
            f'<rect x="0.5" y="0.5" '
            f'width="{width - 1}" '
            f'height="{height - 1}" '
            f'rx="14" '
            f'fill="#0d1117" '
            f'stroke="#30363d"/>'
        ),

        # Header
        (
            f'<text class="title" x="24" y="30">'
            f'Daily Solving Activity'
            f'</text>'
        ),

        (
            f'<text class="subtitle" x="24" y="52">'
            f'Codeforces · @{escape(handle)}'
            f'</text>'
        ),

        (
            f'<text class="subtitle" '
            f'x="{width - 24}" y="30" '
            f'text-anchor="end">'
            f'DSA Practice'
            f'</text>'
        ),
    ]

    # -----------------------------------------------------
    # Month labels
    # -----------------------------------------------------

    shown_months: set[tuple[int, int]] = set()

    for week in range(weeks):

        week_start = (
            start + timedelta(weeks=week)
        )

        for offset in range(7):

            day = week_start + timedelta(days=offset)

            if (
                day.day <= 7
                and year_ago <= day <= today
            ):

                month_key = (
                    day.year,
                    day.month,
                )

                if month_key not in shown_months:

                    x = (
                        grid_x
                        + week * pitch
                    )

                    lines.append(
                        f'<text class="label" '
                        f'x="{x}" y="78">'
                        f'{day.strftime("%b")}'
                        f'</text>'
                    )

                    shown_months.add(
                        month_key
                    )

                break

    # -----------------------------------------------------
    # Weekday labels
    # -----------------------------------------------------

    weekday_labels = {
        1: "Mon",
        3: "Wed",
        5: "Fri",
    }

    for weekday, label in weekday_labels.items():

        y = (
            grid_y
            + weekday * pitch
            + 9
        )

        lines.append(
            f'<text class="label" '
            f'x="25" y="{y}">'
            f'{label}'
            f'</text>'
        )

    # -----------------------------------------------------
    # Activity grid
    # -----------------------------------------------------

    for week in range(weeks):

        week_start = (
            start + timedelta(weeks=week)
        )

        for weekday in range(7):

            day = (
                week_start
                + timedelta(days=weekday)
            )

            x = (
                grid_x
                + week * pitch
            )

            y = (
                grid_y
                + weekday * pitch
            )

            if (
                day < year_ago
                or day > today
            ):
                continue

            count = activity.get(
                day,
                0,
            )

            level = contribution_level(
                count,
                recent_max,
            )

            fill = colors[level]

            noun = (
                "problem"
                if count == 1
                else "problems"
            )

            tooltip = (
                f"{day.strftime('%b %d, %Y')} · "
                f"{count} {noun} solved"
            )

            lines.append(
                (
                    f'<rect class="cell" '
                    f'x="{x}" y="{y}" '
                    f'width="{cell}" '
                    f'height="{cell}" '
                    f'rx="3" '
                    f'fill="{fill}">'
                )
            )

            lines.append(
                f'<title>{escape(tooltip)}</title>'
            )

            lines.append("</rect>")

            # Number inside active cells
            if count > 0:

                lines.append(
                    (
                        f'<text class="count" '
                        f'x="{x + cell / 2:g}" '
                        f'y="{y + 8.7:g}" '
                        f'text-anchor="middle">'
                        f'{count}'
                        f'</text>'
                    )
                )

    # -----------------------------------------------------
    # Statistics cards
    # -----------------------------------------------------

    stats = [
        (
            "Problems Solved",
            total_solved,
            24,
        ),
        (
            "Active Days",
            active_days,
            200,
        ),
        (
            "Best Streak",
            f"{longest_streak} days",
            376,
        ),
        (
            "Last 30 Days",
            last_month_solved,
            552,
        ),
        (
            "Last 12 Months",
            last_year_solved,
            728,
        ),
    ]

    card_y = 220
    card_width = 158
    card_height = 66

    for label, value, x in stats:

        lines.append(
            (
                f'<rect x="{x}" y="{card_y}" '
                f'width="{card_width}" '
                f'height="{card_height}" '
                f'rx="10" '
                f'fill="#161b22" '
                f'stroke="#30363d"/>'
            )
        )

        lines.append(
            (
                f'<text class="stat-value" '
                f'x="{x + 14}" '
                f'y="{card_y + 27}">'
                f'{escape(str(value))}'
                f'</text>'
            )
        )

        lines.append(
            (
                f'<text class="stat-label" '
                f'x="{x + 14}" '
                f'y="{card_y + 46}">'
                f'{escape(label)}'
                f'</text>'
            )
        )

    # -----------------------------------------------------
    # Footer
    # -----------------------------------------------------

    lines.append(
        (
            f'<text class="label" '
            f'x="24" y="312">'
            f'First accepted solve · '
            f'IST ({escape(timezone_name)})'
            f'</text>'
        )
    )

    # Legend

    legend_x = 690
    legend_y = 305

    lines.append(
        (
            f'<text class="label" '
            f'x="{legend_x - 38}" '
            f'y="{legend_y + 9}">'
            f'Less'
            f'</text>'
        )
    )

    for level, color in enumerate(colors):

        x = (
            legend_x
            + level * 22
        )

        lines.append(
            (
                f'<rect x="{x}" '
                f'y="{legend_y}" '
                f'width="14" '
                f'height="14" '
                f'rx="3" '
                f'fill="{color}" '
                f'stroke="#30363d"/>'
            )
        )

    lines.append(
        (
            f'<text class="label" '
            f'x="{legend_x + 5 * 22 + 4}" '
            f'y="{legend_y + 9}">'
            f'More'
            f'</text>'
        )
    )

    lines.append("</svg>")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------
# Command line
# ---------------------------------------------------------

def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description=__doc__
    )

    parser.add_argument(
        "--handle",
        default=DEFAULT_HANDLE,
    )

    parser.add_argument(
        "--timezone",
        default=DEFAULT_TIMEZONE,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )

    parser.add_argument(
        "--today",
        type=date.fromisoformat,
        help="Override today's date for testing.",
    )

    return parser.parse_args()


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main() -> None:

    args = parse_args()

    today = (
        args.today
        or datetime.now(
            ZoneInfo(args.timezone)
        ).date()
    )

    print(
        f"Fetching Codeforces submissions "
        f"for @{args.handle}..."
    )

    submissions = fetch_submissions(
        args.handle
    )

    solved_dates = get_solved_problem_dates(
        submissions,
        args.timezone,
    )

    svg = generate_svg(
        args.handle,
        solved_dates,
        today,
        args.timezone,
    )

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.output.write_text(
        svg,
        encoding="utf-8",
        newline="\n",
    )

    activity = Counter(solved_dates)

    current_streak, longest_streak = calculate_streaks(
        activity,
        today,
    )

    print()
    print("Activity dashboard generated.")
    print(f"Handle: @{args.handle}")
    print(f"Submissions fetched: {len(submissions)}")
    print(f"Problems solved: {len(solved_dates)}")
    print(f"Active days: {len(activity)}")
    print(f"Current streak: {current_streak} days")
    print(f"Best streak: {longest_streak} days")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()