#!/usr/bin/env python3
"""Build an FTS5 index from data/corpus/*.md.

The index is a single SQLite file at data/corpus.fts.db. Two tables:
  - notes (FTS5 virtual): title, body — used by MATCH queries
  - meta:   id, title, summary, source_type, body_length — non-indexed metadata

The LocalFTSRag adapter reads from this file in read-only mode. The summary
column is what gets exposed via the RAG protocol; the raw body is NOT
returned by the adapter.

Run:
    python3 scripts/build_corpus.py
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS_DIR = REPO_ROOT / "data" / "corpus"
DEFAULT_DB_PATH = REPO_ROOT / "data" / "corpus.fts.db"


def read_note(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    # Title: first `# ` heading
    title_match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    title = title_match.group(1).strip() if title_match else path.stem
    # Body: everything after the title line
    if title_match:
        body = text[title_match.end():].strip()
    else:
        body = text
    # Summary: first non-empty paragraph after the title
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    summary = paragraphs[0] if paragraphs else ""
    # Compact whitespace in summary
    summary = " ".join(summary.split())
    if len(summary) > 280:
        summary = summary[:277] + "..."
    return {
        "id": path.stem,
        "title": title,
        "summary": summary,
        "source_type": "markdown",
        "body": body,
        "body_length": len(body),
    }


def build(corpus_dir: Path, db_path: Path) -> int:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "CREATE VIRTUAL TABLE notes USING fts5("
            "id UNINDEXED, title, body, tokenize='porter unicode61'"
            ")"
        )
        conn.execute(
            "CREATE TABLE meta ("
            "id TEXT PRIMARY KEY, title TEXT, summary TEXT, "
            "source_type TEXT, body_length INTEGER"
            ")"
        )
        notes = sorted(corpus_dir.glob("*.md"))
        if not notes:
            print(f"ERROR: no markdown files in {corpus_dir}", file=sys.stderr)
            return 1
        for path in notes:
            note = read_note(path)
            conn.execute(
                "INSERT INTO notes (id, title, body) VALUES (?, ?, ?)",
                (note["id"], note["title"], note["body"]),
            )
            conn.execute(
                "INSERT INTO meta (id, title, summary, source_type, body_length) "
                "VALUES (?, ?, ?, ?, ?)",
                (note["id"], note["title"], note["summary"],
                 note["source_type"], note["body_length"]),
            )
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM meta").fetchone()[0]
        print(f"Built {db_path} with {count} notes from {corpus_dir}")
        return 0
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default=str(DEFAULT_CORPUS_DIR))
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    args = parser.parse_args()
    return build(Path(args.corpus), Path(args.db))


if __name__ == "__main__":
    sys.exit(main())
