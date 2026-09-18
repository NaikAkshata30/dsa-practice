#!/usr/bin/env python3
"""Generate the unified Codeforces Practice Pulse dashboard."""
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

HANDLE = "ashcodes._"
TIMEZONE = "Asia/Kolkata"
API = "https://codeforces.com/api"
ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "assets" / "codeforces-analytics.svg"
TZ = ZoneInfo(TIMEZONE)
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"


def api_get(method: str, params: dict) -> list | dict:
    url = f"{API}/{method}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": "dsa-practice-pulse/2.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.load(response)
            if payload.get("status") != "OK":
                raise RuntimeError(payload.get("comment", "Codeforces API error"))
            return payload["result"]
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            if attempt == 2:
                raise RuntimeError(f"Unable to access Codeforces API: {error}") from error
            time.sleep(2 ** attempt)
    raise RuntimeError("Unable to access Codeforces API")


def problem_key(problem: dict) -> tuple[str, str]:
    return str(problem.get("contestId", problem.get("problemsetName", "unknown"))), str(problem.get("index", "unknown"))


def unique_solves(submissions: list[dict]) -> list[dict]:
    seen = set()
    solved = []
    for submission in sorted(submissions, key=lambda item: item.get("creationTimeSeconds", 0)):
        if submission.get("verdict") != "OK":
            continue
        key = problem_key(submission.get("problem", {}))
        if key not in seen:
            seen.add(key)
            solved.append(submission)
    return solved


def solve_date(submission: dict) -> date:
    return datetime.fromtimestamp(submission["creationTimeSeconds"], TZ).date()


def streaks(days: list[date], today: date) -> tuple[int, int]:
    ordered = sorted(set(days))
    if not ordered:
        return 0, 0
    best = run = 1
    for previous, current in zip(ordered, ordered[1:]):
        run = run + 1 if current == previous + timedelta(days=1) else 1
        best = max(best, run)
    cursor = today if today in ordered else today - timedelta(days=1)
    current = 0
    available = set(ordered)
    while cursor in available:
        current += 1
        cursor -= timedelta(days=1)
    return current, best


def txt(x, y, value, size=13, color="#91a9c3", weight=400, anchor="start", cls=""):
    class_attr = f' class="{cls}"' if cls else ""
    return (f'<text{class_attr} x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{escape(str(value))}</text>')


def card(x, y, width, height, fill="#0e1b2b", radius=16):
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" fill="{fill}" stroke="#263b52"/>'


def render_metrics(solved_count, active_days, current_streak, best_streak, last_30):
    cards = [
        ("UNIQUE SOLVES", solved_count, "first accepted problems"),
        ("ACTIVE DAYS", active_days, "across all recorded time"),
        ("BEST STREAK", f"{best_streak}d", f"current run: {current_streak}d"),
        ("LAST 30 DAYS", last_30, "new problems cleared"),
    ]
    lines = []
    for i, (label, value, note) in enumerate(cards):
        x = 48 + i * 285
        lines += [card(x, 112, 257, 105, "url(#metric)" if i % 2 == 0 else "url(#metricAlt)"),
                  txt(x + 21, 140, label, 11, "#42e8c7", 700),
                  txt(x + 21, 181, value, 30, "#f8fafc", 750),
                  txt(x + 21, 203, note, 10, "#83a6c7")]
    return lines


def render_heatmap(activity: Counter, today: date):
    x, y, width, height = 48, 239, 1104, 265
    lines = [card(x, y, width, height), txt(x + 24, y + 35, "365-day solving trail", 14, "#f8fafc", 700)]
    year_start = today - timedelta(days=364)
    start = year_start - timedelta(days=(year_start.weekday() + 1) % 7)
    recent_total = sum(value for day, value in activity.items() if year_start <= day <= today)
    recent_days = sum(1 for day, value in activity.items() if year_start <= day <= today and value)
    lines.append(txt(x + width - 24, y + 35, f"{recent_total} solves · {recent_days} active days", 10, "#8db3d8", 500, "end"))
    cell, gap, gx, gy = 11, 4, x + 92, y + 91
    max_count = max((value for day, value in activity.items() if year_start <= day <= today), default=1)
    colors = ["#142234", "#164a55", "#087f78", "#16b8a5", "#52f0c8"]
    shown = set()
    for week in range(53):
        week_start = start + timedelta(weeks=week)
        for offset in range(7):
            day = week_start + timedelta(days=offset)
            if year_start <= day <= today and day.day <= 7 and (day.year, day.month) not in shown:
                lines.append(txt(gx + week * (cell + gap), y + 72, day.strftime("%b"), 9, "#8db3d8"))
                shown.add((day.year, day.month))
                break
    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        lines.append(txt(x + 25, gy + row * (cell + gap) + 9, label, 9, "#8db3d8"))
    for week in range(53):
        for row in range(7):
            day = start + timedelta(weeks=week, days=row)
            if not year_start <= day <= today:
                continue
            count = activity.get(day, 0)
            level = 0 if not count else min(4, max(1, math.ceil(count / max_count * 4)))
            cx, cy = gx + week * (cell + gap), gy + row * (cell + gap)
            lines.append(f'<rect x="{cx}" y="{cy}" width="{cell}" height="{cell}" rx="2.5" fill="{colors[level]}" stroke="#294057"><title>{day:%d %b %Y}: {count} solved</title></rect>')
            if count:
                lines.append(txt(cx + cell / 2, cy + 8.3, count, 7, "#ffffff", 700, "middle"))
    lines.append(txt(x + 24, y + height - 18, "Each square marks a first accepted solution · Asia/Kolkata", 9, "#7697b8"))
    legend_x = x + width - 176
    lines.append(txt(legend_x - 38, y + height - 18, "LESS", 8, "#7697b8"))
    for i, color in enumerate(colors):
        lines.append(f'<rect x="{legend_x + i * 17}" y="{y + height - 29}" width="11" height="11" rx="2" fill="{color}" stroke="#294057"/>')
    lines.append(txt(legend_x + 93, y + height - 18, "MORE", 8, "#7697b8"))
    return lines


def render_submission_activity(activity: Counter, today: date):
    x, y, width, height = 48, 526, 430, 195
    lines = [card(x, y, width, height), txt(x + 20, y + 31, "SUBMISSION ACTIVITY", 11, "#42e8c7", 700)]
    days = [today - timedelta(days=i) for i in range(29, -1, -1)]
    values = [activity.get(day, 0) for day in days]
    maximum = max(values, default=1)
    chart_x, chart_y, chart_w, chart_h = x + 28, y + 58, width - 56, 104
    for level in range(3):
        ly = chart_y + level * chart_h / 2
        lines.append(f'<line x1="{chart_x}" y1="{ly}" x2="{chart_x + chart_w}" y2="{ly}" stroke="#1f354a"/>')
    bar_gap = 2.5
    bar_w = chart_w / 30 - bar_gap
    for i, value in enumerate(values):
        bh = value / maximum * chart_h if maximum else 0
        bx, by = chart_x + i * (bar_w + bar_gap), chart_y + chart_h - bh
        lines.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w:.1f}" height="{max(1.5, bh):.1f}" rx="2" fill="url(#activity)"><title>{days[i]:%d %b}: {value} solved</title></rect>')
    for index in (0, 9, 19, 29):
        lines.append(txt(chart_x + index * (bar_w + bar_gap), y + height - 15, days[index].strftime("%d %b"), 8, "#7697b8"))
    return lines


def render_topics(solved: list[dict]):
    x, y, width, height = 500, 526, 324, 195
    counts = Counter(tag for item in solved for tag in item.get("problem", {}).get("tags", []))
    topics = counts.most_common(4)
    maximum = topics[0][1] if topics else 1
    lines = [card(x, y, width, height), txt(x + 20, y + 31, "TOPIC FINGERPRINT", 11, "#42e8c7", 700)]
    for i, (topic, count) in enumerate(topics):
        row_y = y + 67 + i * 29
        label = topic if len(topic) <= 19 else topic[:17] + "…"
        lines += [txt(x + 20, row_y, label, 10, "#9fc0dd"),
                  f'<rect x="{x + 142}" y="{row_y - 10}" width="128" height="10" rx="5" fill="#17273a"/>',
                  f'<rect x="{x + 142}" y="{row_y - 10}" width="{128 * count / maximum:.1f}" height="10" rx="5" fill="url(#topic)"/>',
                  txt(x + 286, row_y, count, 9, "#f7c873", 700)]
    return lines


def render_recent(solved: list[dict]):
    x, y, width, height = 846, 526, 306, 195
    lines = [card(x, y, width, height), txt(x + 20, y + 31, "RECENT WINS", 11, "#42e8c7", 700)]
    for i, submission in enumerate(reversed(solved[-3:])):
        problem = submission.get("problem", {})
        name = problem.get("name", "Unknown problem")
        name = name if len(name) <= 25 else name[:23] + "…"
        problem_id = f'{problem.get("contestId", "")}{problem.get("index", "")}'
        solved_on = solve_date(submission).strftime("%d %b")
        row_y = y + 68 + i * 43
        lines += [f'<circle cx="{x + 21}" cy="{row_y - 4}" r="4" fill="#f4b860"/>',
                  txt(x + 34, row_y, name, 10, "#f8fafc", 600),
                  txt(x + width - 18, row_y, f"{problem_id} · {solved_on}", 8, "#83a6c7", 400, "end")]
    return lines


def render_dashboard(solved: list[dict]) -> str:
    today = datetime.now(TZ).date()
    dates = [solve_date(item) for item in solved]
    activity = Counter(dates)
    current, best = streaks(dates, today)
    last_30 = sum(1 for day in dates if day >= today - timedelta(days=29))
    width, height = 1200, 750
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
             '<title id="title">Codeforces Practice Pulse</title>',
             f'<desc id="desc">{len(solved)} unique accepted problems across {len(set(dates))} active days.</desc>',
             '<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#07111f"/><stop offset="1" stop-color="#10182c"/></linearGradient>'
             '<linearGradient id="metric" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#10263a"/><stop offset="1" stop-color="#13243b"/></linearGradient>'
             '<linearGradient id="metricAlt" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#13283b"/><stop offset="1" stop-color="#20213a"/></linearGradient>'
             '<linearGradient id="activity" x1="0" y1="1" x2="0" y2="0"><stop stop-color="#2b8a85"/><stop offset="1" stop-color="#f4b860"/></linearGradient>'
             '<linearGradient id="topic" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#22c7aa"/><stop offset="1" stop-color="#f4b860"/></linearGradient></defs>',
             f'<rect width="{width}" height="{height}" fill="url(#bg)"/>',
             f'<rect x="20" y="20" width="1160" height="710" rx="20" fill="none" stroke="#2b3f58"/>',
             '<rect x="48" y="48" width="4" height="54" rx="2" fill="#f4b860"/>',
             txt(70, 60, "CODEFORCES · CONSISTENT PRACTICE", 10, "#42e8c7", 700),
             txt(70, 91, "Practice Pulse", 25, "#f8fafc", 750),
             txt(1152, 61, f"@{HANDLE}", 11, "#9fc0dd", 500, "end"),
             txt(1152, 85, f"CP-31 journey · updated {today:%d %b %Y}", 9, "#7697b8", 400, "end")]
    lines += render_metrics(len(solved), len(set(dates)), current, best, last_30)
    lines += render_heatmap(activity, today)
    lines += render_submission_activity(activity, today)
    lines += render_topics(solved)
    lines += render_recent(solved)
    lines.append("</svg>")
    return "\n".join(lines)


def main():
    print(f"Fetching Codeforces submissions for @{HANDLE}...")
    submissions = api_get("user.status", {"handle": HANDLE, "from": 1, "count": 10000})
    solved = unique_solves(submissions)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render_dashboard(solved), encoding="utf-8", newline="\n")
    print(f"Generated {OUTPUT}")
    print(f"Submissions fetched: {len(submissions)}")
    print(f"Unique problems solved: {len(solved)}")


if __name__ == "__main__":
    main()
