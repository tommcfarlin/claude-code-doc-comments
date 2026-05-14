#!/usr/bin/env python3
"""
Strip Swift doc comments from a directory tree.

Removes:
  - Lines that are `///` doc comments (whitespace + `///` prefix)
  - Block doc comments delimited by `/**` ... `*/`

Leaves alone:
  - Regular `//` comments
  - Regular `/* ... */` block comments (not starting with /**)
  - All code, strings, whitespace

Operates in two modes:
  --dry-run : prints stats per file, writes nothing
  --apply   : rewrites files in place
"""

import argparse
import os
import re
import sys
from pathlib import Path

DOC_LINE_RE = re.compile(r'^\s*///')
BLOCK_DOC_OPEN_RE = re.compile(r'/\*\*(?!/)')   # /** but not /**/
BLOCK_ANY_CLOSE_RE = re.compile(r'\*/')

EXCLUDED_DIRS = {'.build', 'build', '.swiftpm', 'Pods', '.git', 'DerivedData'}


def strip_file(path: Path) -> tuple[str, int]:
    """Return (new_contents, lines_removed) for the given Swift file."""
    original = path.read_text(encoding='utf-8')
    lines = original.splitlines(keepends=True)
    out = []
    in_block_doc = False
    removed = 0

    for line in lines:
        if in_block_doc:
            removed += 1
            if BLOCK_ANY_CLOSE_RE.search(line):
                in_block_doc = False
            continue

        # Pure /// line doc — drop
        if DOC_LINE_RE.match(line):
            removed += 1
            continue

        # /** ... */ on the same line — drop the doc, keep nothing
        # but only if the whole line is a doc block (whitespace + /** ... */)
        stripped = line.strip()
        if stripped.startswith('/**') and stripped.endswith('*/') and len(stripped) >= 5:
            removed += 1
            continue

        # /** start of multi-line block doc
        m = BLOCK_DOC_OPEN_RE.search(line)
        if m:
            # If the close is on the same line, treat as single-line doc only
            # if the doc occupies the whole line. Otherwise this is mixed
            # content — leave it alone to be safe.
            rest = line[m.end():]
            if BLOCK_ANY_CLOSE_RE.search(rest):
                # /** ... */ on same line but with other content — skip safely
                out.append(line)
                continue
            # Multi-line block doc starts here
            if line[:m.start()].strip() == '':
                removed += 1
                in_block_doc = True
                continue
            else:
                # /** preceded by code on same line — too risky, leave alone
                out.append(line)
                continue

        out.append(line)

    return ''.join(out), removed


def walk(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for name in filenames:
            if name.endswith('.swift'):
                yield Path(dirpath) / name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('root', type=Path)
    ap.add_argument('--apply', action='store_true', help='Write changes; default is dry-run')
    args = ap.parse_args()

    total_files = 0
    total_changed = 0
    total_lines_removed = 0

    for f in walk(args.root):
        total_files += 1
        new, removed = strip_file(f)
        if removed > 0:
            total_changed += 1
            total_lines_removed += removed
            if args.apply:
                f.write_text(new, encoding='utf-8')
            print(f"  {f.relative_to(args.root)}: -{removed} doc lines")

    mode = 'APPLIED' if args.apply else 'DRY-RUN'
    print(f"\n[{mode}] {total_changed}/{total_files} files changed, {total_lines_removed} doc lines removed total")


if __name__ == '__main__':
    main()
