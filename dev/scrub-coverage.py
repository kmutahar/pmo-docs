#!/usr/bin/env python3
"""Maintainer tool: check which names in a source project .scrub-names would NOT catch. Not shipped.

Usage: python3 dev/scrub-coverage.py SRC NAMES_FILE OUT
  SRC         source project folder holding data/roster.md, config.yaml and registers/*.yaml
  NAMES_FILE  the names list (the untracked .scrub-names in the repo root)
  OUT         file that receives the uncaught names, one "category<TAB>name" per line
              (private data: write it outside tracked files, e.g. under tmp/)
Prints counts only (per category: found, not caught). Patterns are matched as Python regexes,
case-insensitive, so exotic grep -E syntax in NAMES_FILE may differ slightly.
"""
import sys

if sys.version_info < (3, 10):
    sys.exit("pmo-docs needs Python 3.10 or newer (this is %d.%d)." % sys.version_info[:2])

import argparse
import glob
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/pmo-docs/scripts/_vendor"))
import yaml

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("src")
ap.add_argument("names_file")
ap.add_argument("out")
args = ap.parse_args()
src, names_file, out = args.src, args.names_file, args.out
pats = [re.compile(l.rstrip('\n'), re.I) for l in open(names_file, encoding='utf-8') if l.strip()]
caught = lambda s: any(p.search(s) for p in pats)
cands = {}
def add(cat, s):
    s = str(s).strip()
    if len(s) >= 3: cands.setdefault(cat, set()).add(s)
for line in open(f'{src}/data/roster.md', encoding='utf-8'):
    cells = [c.strip() for c in line.strip().strip('|').split('|')]
    if len(cells) < 5 or cells[0] in ('slug',) or set(cells[0]) <= set('-'): continue
    add('roster slug', cells[0]); add('full name en', cells[3]); add('full name ar', cells[4])
    for w in re.split(r'[\s\-]+', cells[3]): add('name part en', w)
    for w in cells[4].split(): add('name part ar', w)
c = yaml.safe_load(open(f'{src}/config.yaml', encoding='utf-8'))
def walk(cat, v):
    if isinstance(v, dict):
        for k, x in v.items(): walk(cat, x)
    elif isinstance(v, list):
        for x in v: walk(cat, x)
    elif isinstance(v, str) and len(v) < 60: add(cat, v)
walk('config.project values', c.get('project'))
sp = c.get('subprojects')
for k in (sp.keys() if isinstance(sp, dict) else [x.get('id', x) if isinstance(x, dict) else x for x in sp or []]): add('subproject id', k)
for f in glob.glob(f'{src}/registers/*.yaml'):
    d = yaml.safe_load(open(f, encoding='utf-8')) or {}
    rows = next((v for v in d.values() if isinstance(v, list)), []) if isinstance(d, dict) else d
    for r in rows or []:
        if isinstance(r, dict):
            for k in ('owner', 'assignee', 'assigned_to', 'by', 'raised_by', 'who', 'owners', 'attendees'):
                v = r.get(k)
                for x in (v if isinstance(v, list) else [v] if v else []): add('register people values', x)
miss = []
for cat, ss in sorted(cands.items()):
    m = sorted(s for s in ss if not caught(s))
    print(f'{cat}: {len(ss)} found, {len(m)} not caught')
    miss += [f'{cat}\t{s}' for s in m]
open(out, 'w', encoding='utf-8').write('\n'.join(miss) + ('\n' if miss else ''))
