"""
migrate_html.py — Re-render all existing HTML reports with the current template.

Extracts the embedded JSON payload from each HTML file and calls write_html()
so every report gets the latest UI (volume column, shared X-axis, combined
expand modal, S→B/B→S badges, etc.).

snapshot_info is not stored in old files, so delta/trend sections will show
"no previous snapshot" — everything else is fully restored.

Usage:
    python3 migrate_html.py               # migrate all reports/*.html
    python3 migrate_html.py --dry-run     # list files that would be migrated
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Make sure local modules are importable
sys.path.insert(0, str(Path(__file__).parent))
from exporter_html import write_html


def extract_payload(html: str) -> dict | None:
    """Pull the JSON object from `const RAW = {...};` in the HTML."""
    m = re.search(r"const RAW = (\{.*?\});\s*\n", html, re.DOTALL)
    if not m:
        return None
    return json.loads(m.group(1))


def migrate_file(path: Path, dry_run: bool = False) -> bool:
    html = path.read_text(encoding="utf-8")
    payload = extract_payload(html)
    if payload is None:
        print(f"  SKIP  {path.name}  (no RAW payload found)")
        return False

    tickers   = payload.get("tickers", [])
    timestamp = payload.get("generated", path.stem)

    if not tickers:
        print(f"  SKIP  {path.name}  (empty tickers list)")
        return False

    if dry_run:
        print(f"  WOULD migrate  {path.name}  ({len(tickers)} tickers)")
        return True

    write_html(
        analyzed=tickers,
        output_path=path,
        timestamp=timestamp,
        iso_timestamp="",
        snapshot_info={},   # delta info not available in old files
    )
    print(f"  OK    {path.name}  ({len(tickers)} tickers)")
    return True


def main():
    parser = argparse.ArgumentParser(description="Re-render old HTML reports with the current template.")
    parser.add_argument("--dry-run", action="store_true", help="List files without writing")
    parser.add_argument("--dir", default="reports", help="Directory containing HTML reports (default: reports)")
    args = parser.parse_args()

    reports_dir = Path(__file__).parent / args.dir
    html_files  = sorted(reports_dir.glob("options_signals_*.html"))

    if not html_files:
        print(f"No HTML files found in {reports_dir}")
        return

    print(f"{'DRY RUN — ' if args.dry_run else ''}Migrating {len(html_files)} file(s) in {reports_dir}\n")

    ok = skip = 0
    for f in html_files:
        if migrate_file(f, dry_run=args.dry_run):
            ok += 1
        else:
            skip += 1

    print(f"\nDone. {'Would migrate' if args.dry_run else 'Migrated'}: {ok}  Skipped: {skip}")


if __name__ == "__main__":
    main()
