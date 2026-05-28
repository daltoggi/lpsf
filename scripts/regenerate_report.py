#!/usr/bin/env python3
"""Regenerate EVALUATION_REPORT.md from an existing EVALUATION_REPORT.json.

Useful when render_report() gains new sections and the markdown needs to
catch up without paying for another API run.

Usage:
    python3 scripts/regenerate_report.py
    python3 scripts/regenerate_report.py --json path/to/REPORT.json --out path/to/REPORT.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def main() -> None:
    default_json = REPO_ROOT / "ops" / "lpsf" / "EVALUATION_REPORT.json"
    default_md = REPO_ROOT / "ops" / "lpsf" / "EVALUATION_REPORT.md"

    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default=str(default_json), help="Input JSON path")
    parser.add_argument("--out", default=str(default_md), help="Output markdown path")
    args = parser.parse_args()

    src = Path(args.json)
    if not src.exists():
        print(f"ERROR: source JSON not found: {src}")
        sys.exit(1)

    from lpsf.experiments.benchmark import BenchmarkReport
    from lpsf.experiments.report import render_report

    payload = json.loads(src.read_text(encoding="utf-8"))
    report = BenchmarkReport.from_dict(payload)
    md = render_report(report)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print(f"Rendered {len(md):,} bytes → {out}")


if __name__ == "__main__":
    main()
