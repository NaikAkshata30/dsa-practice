#!/usr/bin/env python3
"""Generate repository-derived progress charts for the README."""
from __future__ import annotations

from collections import Counter
from html import escape
from pathlib import Path

from generate_readme import discover

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"


def text(x, y, value, size=14, color="#8b949e", weight=400, anchor="start"):
    return (
        f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
        f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}">'
        f'{escape(str(value))}</text>'
    )


def shell(title, subtitle, height):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="{height}" '
        f'viewBox="0 0 900 {height}" role="img" aria-label="{escape(title)}">',
        '<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        '<stop stop-color="#0d1117"/><stop offset="1" stop-color="#111827"/>'
        '</linearGradient><linearGradient id="bar" x1="0" y1="0" x2="1" y2="0">'
        '<stop stop-color="#22d3ee"/><stop offset="1" stop-color="#8b5cf6"/>'
        '</linearGradient></defs>',
        f'<rect x="0.5" y="0.5" width="899" height="{height - 1}" rx="16" '
        'fill="url(#bg)" stroke="#30363d"/>',
        text(32, 42, title, 21, "#f0f6fc", 700),
        text(32, 67, subtitle, 12),
    ]


def difficulty_chart(problems):
    counts = Counter(p["rating"] for p in problems)
    levels = sorted(set(range(800, max(counts, default=800) + 100, 100)) | set(counts))
    height = 112 + len(levels) * 42
    lines = shell("Difficulty Ladder", "Repository solutions grouped by Codeforces rating", height)
    maximum = max(counts.values(), default=1)
    for i, level in enumerate(levels):
        y = 105 + i * 42
        value = counts[level]
        width = 620 * value / maximum if value else 0
        lines += [text(34, y + 5, level, 13, "#c9d1d9", 600),
                  f'<rect x="105" y="{y - 10}" width="620" height="18" rx="9" fill="#1f2937"/>']
        if width:
            lines.append(f'<rect x="105" y="{y - 10}" width="{width:.1f}" height="18" rx="9" fill="url(#bar)"/>')
        lines.append(text(755, y + 5, value, 13, "#f0f6fc", 700))
    lines += [text(866, height - 22, f"{len(problems)} solutions", 11, anchor="end"), "</svg>"]
    return "\n".join(lines)


def pattern_chart(problems):
    counts = Counter(p["pattern"] for p in problems)
    rows = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    height = 112 + len(rows) * 38
    lines = shell("Pattern Coverage", "Primary ideas represented in the local solution archive", height)
    maximum = max(counts.values(), default=1)
    for i, (pattern, value) in enumerate(rows):
        y = 103 + i * 38
        width = 520 * value / maximum
        lines += [text(34, y + 4, pattern, 12, "#c9d1d9", 600),
                  f'<rect x="255" y="{y - 10}" width="520" height="16" rx="8" fill="#1f2937"/>',
                  f'<rect x="255" y="{y - 10}" width="{width:.1f}" height="16" rx="8" fill="url(#bar)"/>',
                  text(805, y + 4, value, 12, "#f0f6fc", 700)]
    lines += [text(866, height - 22, "Generated from solution metadata", 11, anchor="end"), "</svg>"]
    return "\n".join(lines)


def main():
    problems = discover()
    ASSETS.mkdir(parents=True, exist_ok=True)
    outputs = {
        ASSETS / "difficulty-ladder.svg": difficulty_chart(problems),
        ASSETS / "pattern-coverage.svg": pattern_chart(problems),
    }
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8", newline="\n")
        print(f"Generated {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
