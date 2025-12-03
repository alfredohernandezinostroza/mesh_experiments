#!/usr/bin/env python3
"""Parse NLM MeSH ASCII file into a CSV with one column per tag.

The MeSH ASCII format contains entries separated by blank lines. Each entry
has lines with a tag, a delimiter (usually ' - '), and a value, for example:

UI - D000328
MH - Behavior
ENTRY - Behavioral Characteristics
MN - F01.145.500

This script parses all tags found and writes a CSV where each tag is a column.
If a tag appears multiple times for an entry, values are joined with '||'.

Usage:
    python scripts/parse_mesh_ascii_to_csv.py path/to/mesh_ascii.txt [out.csv]

"""
from pathlib import Path
import sys
import csv
import re
from collections import defaultdict


def parse_mesh_ascii(path):
    entries = []
    cur = defaultdict(list)
    last_tag = None

    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for raw in f:
            line = raw.rstrip('\n')
            if not line.strip():
                # end of entry
                if cur:
                    entries.append(dict(cur))
                    cur = defaultdict(list)
                    last_tag = None
                continue

            # continuation lines start with whitespace
            if line.startswith(' ') or line.startswith('\t'):
                if last_tag is not None and cur[last_tag]:
                    # append continuation to last value
                    cur[last_tag][-1] = cur[last_tag][-1] + ' ' + line.strip()
                continue

            # Try common delimiters: ' - ' or ' = '
            m = re.match(r'^(?P<tag>[^\-:=]+?)\s*-\s*(?P<val>.*)$', line)
            if not m:
                m = re.match(r'^(?P<tag>[^\-:=]+?)\s*=\s*(?P<val>.*)$', line)
            if not m:
                # fallback: split on first two chars and rest (some files use fixed width)
                if len(line) > 3 and line[2] == ' ':
                    tag = line[:2].strip()
                    val = line[3:].strip()
                else:
                    # unknown format: skip
                    continue
            else:
                tag = m.group('tag').strip()
                val = m.group('val').strip()

            # normalize tag (keep as-is but collapse internal spaces)
            tag = re.sub(r'\s+', ' ', tag)

            cur[tag].append(val)
            last_tag = tag

    # append last entry if file doesn't end with blank line
    if cur:
        entries.append(dict(cur))

    return entries


def entries_to_csv(entries, out_path):
    # collect all tags
    tags = set()
    for e in entries:
        tags.update(e.keys())
    tags = sorted(tags)

    with open(out_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(tags)
        for e in entries:
            row = []
            for t in tags:
                if t in e:
                    vals = e[t]
                    # join multiple values with '||' to preserve commas inside
                    row.append('||'.join(v for v in vals))
                else:
                    row.append('')
            writer.writerow(row)


def main(argv):
    if len(argv) < 2:
        print('Usage: parse_mesh_ascii_to_csv.py path/to/mesh_ascii.txt [out.csv]')
        return 1
    inp = Path(argv[1])
    if not inp.exists():
        print('Input file not found:', inp)
        return 1
    out = Path(argv[2]) if len(argv) > 2 else inp.with_suffix('.csv')

    entries = parse_mesh_ascii(inp)
    print(f'Parsed {len(entries)} MeSH entries, writing CSV to {out}')
    entries_to_csv(entries, out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
