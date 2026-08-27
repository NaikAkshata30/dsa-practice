#!/usr/bin/env python3
"""Refresh README sections from rating directories and solution headers."""
from __future__ import annotations
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
HEADER = re.compile(r"^#\s*Codeforces:\s*(?:(\d+[A-Z]\d*)\s*-\s*)?(.+?)\s*$", re.I)
DIR = re.compile(r"^(\d+)-level$")
MARKERS = {name: (f"<!-- AUTO:{name.upper()}:START -->", f"<!-- AUTO:{name.upper()}:END -->") for name in ("problems", "patterns")}
PATTERNS = {
 "1903A":"Greedy & ordering","1901A":"Greedy & ordering","1900A":"Greedy & ordering","1896A":"Greedy & ordering",
 "339A":"Strings","71A":"Strings","1881A":"Strings",
 "1899A":"Math & games","1829A":"Math & games","1866A":"Math & games","1858A":"Math & games","1857A":"Math & games",
 "1890A":"Frequency & constructive","1862B":"Frequency & constructive","1859A":"Frequency & constructive",
 "1696A":"Membership check","1873C":"Grid simulation",
}

def discover():
    result = []
    for directory in ROOT.iterdir():
        matched = DIR.match(directory.name) if directory.is_dir() else None
        if not matched: continue
        for path in directory.glob("*.py"):
            header = next((HEADER.match(x) for x in path.read_text(encoding="utf-8-sig").splitlines()[:8] if HEADER.match(x)), None)
            if not header or not header.group(1): raise ValueError(f"Missing Codeforces ID in {path.relative_to(ROOT)}")
            pid, title = header.group(1).upper(), header.group(2).strip()
            contest = re.match(r"\d+", pid).group()
            result.append(dict(id=pid,title=title,rating=int(matched.group(1)),pattern=PATTERNS.get(pid,"To classify"),
                problem=f"https://codeforces.com/problemset/problem/{contest}/{pid[len(contest):]}",
                solution=quote(path.relative_to(ROOT).as_posix(), safe="/")))
    return sorted(result, key=lambda x:(x["rating"],x["id"]))

def problem_link(p): return f'[{p["id"]} — {p["title"]}]({p["problem"]})'
def snapshot(items):
    ratings={p["rating"] for p in items}
    return "| Repository metric | Current value |\n|:--|--:|\n"+f"| Solution files | **{len(items)}** |\n| Highest difficulty represented | **{max(ratings) if ratings else '—'}** |\n| Difficulty levels represented | **{len(ratings)}** |\n| Primary language | **Python** |\n| Practice track | **TLE Eliminators CP-31** |"
def difficulty(items):
    counts=defaultdict(int)
    for p in items: counts[p["rating"]]+=1
    maximum=max(counts.values(),default=1); rows=["| Rating | Relative volume | Solutions |","|--:|:--|--:|"]
    for rating,count in sorted(counts.items()):
        filled=round(16*count/maximum); rows.append(f"| **{rating}** | `{'█'*filled}{'░'*(16-filled)}` | **{count}** |")
    return "\n".join(rows)
def problems(items):
    groups=defaultdict(list)
    for p in items: groups[p["rating"]].append(p)
    output=[]
    for rating,group in sorted(groups.items()):
        rows=[f"### {rating} rated","","| # | Problem | Primary pattern | Solution |","|--:|:--|:--|:--:|"]
        rows += [f'| {i} | {problem_link(p)} | {p["pattern"]} | [Python]({p["solution"]}) |' for i,p in enumerate(group,1)]
        output.append("\n".join(rows))
    return "\n\n".join(output)
def patterns(items):
    groups=defaultdict(list)
    for p in items: groups[p["pattern"]].append(p)
    rows=["| Primary pattern | Problems |","|:--|:--|"]
    for pattern,group in sorted(groups.items()): rows.append(f"| **{pattern}** | "+" · ".join(f'{problem_link(p)} ([code]({p["solution"]}))' for p in group)+" |")
    return "\n".join(rows)
def replace(content,name,value):
    start,end=MARKERS[name]; updated,count=re.subn(re.escape(start)+r".*?"+re.escape(end),f"{start}\n{value}\n{end}",content,flags=re.S)
    if count != 1: raise RuntimeError(f"Expected one {name} marker pair; found {count}")
    return updated
def main():
    items=discover(); content=README.read_text(encoding="utf-8")
    for name,renderer in (("patterns",patterns),("problems",problems)): content=replace(content,name,renderer(items))
    README.write_text(content,encoding="utf-8",newline="\n")
    print(f"README refreshed from {len(items)} solutions across {len({p['rating'] for p in items})} rating level(s).")
if __name__ == "__main__": main()
