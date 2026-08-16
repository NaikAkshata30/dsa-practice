#!/usr/bin/env python3

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
PROBLEMS_DIR = ROOT / "800-level"


SNAPSHOT_START = "<!-- AUTO:SNAPSHOT:START -->"
SNAPSHOT_END = "<!-- AUTO:SNAPSHOT:END -->"

PROBLEMS_START = "<!-- AUTO:PROBLEMS:START -->"
PROBLEMS_END = "<!-- AUTO:PROBLEMS:END -->"


def get_problem_files():
    """Return all Python solution files from the 800-level folder."""

    if not PROBLEMS_DIR.exists():
        return []

    return sorted(
        PROBLEMS_DIR.glob("*.py"),
        key=lambda path: path.name.lower(),
    )


def extract_problem_info(file_path):
    """
    Extract the Codeforces problem number and title
    from a filename.

    Expected examples:

        71A - Way Too Long Words.py
        339A - Helpful Maths.py
        1903A - Halloumi Boxes.py
    """

    name = file_path.stem

    match = re.match(
        r"^(\d+[A-Z])\s*[-—]\s*(.+)$",
        name,
    )

    if match:
        problem_id = match.group(1)
        title = match.group(2).strip()
    else:
        problem_id = name
        title = name

    return problem_id, title


def codeforces_url(problem_id):
    """Build the Codeforces problem URL."""

    number = re.match(r"(\d+)", problem_id)

    if not number:
        return None

    contest_id = number.group(1)

    return (
        f"https://codeforces.com/problemset/problem/"
        f"{contest_id}/{problem_id[len(contest_id):]}"
    )


def github_solution_url(file_path):
    """Build a relative GitHub/Markdown link to the solution."""

    relative = file_path.relative_to(ROOT)

    # Convert Windows backslashes to URL-style slashes.
    return str(relative).replace("\\", "/")


def generate_snapshot(problem_count):
    """Generate the automatic journey snapshot."""

    if problem_count == 0:
        level = "—"
    else:
        level = "800"

    return f"""| Problems Solved | Practice Level | Language |
|:---:|:---:|:---:|
| **{problem_count}** | **{level}** | **Python** |"""


def generate_problem_table(files):
    """Generate the Problems table."""

    rows = [
        "| Problem | Solution |",
        "|---|:---:|",
    ]

    for file_path in files:

        problem_id, title = extract_problem_info(file_path)

        problem_url = codeforces_url(problem_id)

        solution_url = github_solution_url(file_path)

        if problem_url:
            problem_text = (
                f"[{problem_id} — {title}]"
                f"({problem_url})"
            )
        else:
            problem_text = f"{problem_id} — {title}"

        rows.append(
            f"| {problem_text} | "
            f"[Python]({solution_url}) |"
        )

    return "\n".join(rows)


def replace_section(
    content,
    start_marker,
    end_marker,
    replacement,
):
    """Replace an automatically generated README section."""

    pattern = (
        re.escape(start_marker)
        + r".*?"
        + re.escape(end_marker)
    )

    new_section = (
        start_marker
        + "\n"
        + replacement
        + "\n"
        + end_marker
    )

    updated, count = re.subn(
        pattern,
        new_section,
        content,
        flags=re.DOTALL,
    )

    if count == 0:
        raise RuntimeError(
            f"Could not find README markers:\n"
            f"{start_marker}\n"
            f"{end_marker}"
        )

    return updated


def main():

    if not README.exists():
        raise FileNotFoundError(
            "README.md was not found."
        )

    files = get_problem_files()

    problem_count = len(files)

    content = README.read_text(
        encoding="utf-8"
    )

    # Update Journey Snapshot
    content = replace_section(
        content,
        SNAPSHOT_START,
        SNAPSHOT_END,
        generate_snapshot(problem_count),
    )

    # Update Problems table
    content = replace_section(
        content,
        PROBLEMS_START,
        PROBLEMS_END,
        generate_problem_table(files),
    )

    README.write_text(
        content,
        encoding="utf-8",
        newline="\n",
    )

    print("README updated successfully.")
    print(f"Problems found: {problem_count}")
    print(f"README: {README}")


if __name__ == "__main__":
    main()