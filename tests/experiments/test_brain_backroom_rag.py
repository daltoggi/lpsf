"""Tests for BrainBackroomRag — sensitivity-gated read-only brain adapter.

Uses a synthetic FTS index that mirrors the brain-backroom schema, including
deliberately-forbidden rows (sensitivity=high, external_llm=false) to prove
the gate excludes them. Does NOT depend on any real personal data.
"""

import sqlite3
from pathlib import Path

import pytest

from lpsf.experiments.brain_backroom_rag import BrainBackroomRag, _strip_quotes


def _build_synthetic_brain(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE notes (
            id INTEGER PRIMARY KEY,
            path TEXT, zone TEXT, title TEXT, type TEXT, content TEXT,
            sensitivity TEXT, external_llm TEXT
        );
        CREATE VIRTUAL TABLE notes_fts USING fts5(
            title, content, content='notes', content_rowid='id',
            tokenize='trigram'
        );
        """
    )
    rows = [
        # id, path, zone, title, content, sensitivity, external_llm
        (1, "a.md", "core", "Async patterns", "asynchronous programming patterns in python", "normal", "true"),
        (2, "b.md", "core", "Database choices", "choosing between sqlite and postgres databases", '"normal"', "true"),
        (3, "c.md", "source", "Secret salary", "confidential salary negotiation private", "high", "true"),
        (4, "d.md", "core", "Blocked note", "this note must never reach an external model", "normal", "false"),
        (5, "e.md", "lab", "Search infra", "full text search infrastructure with fts5", "normal", "true"),
    ]
    for r in rows:
        conn.execute(
            "INSERT INTO notes (id, path, zone, title, content, sensitivity, external_llm) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (r[0], r[1], r[2], r[3], r[4], r[5], r[6]),
        )
        conn.execute(
            "INSERT INTO notes_fts (rowid, title, content) VALUES (?, ?, ?)",
            (r[0], r[3], r[4]),
        )
    conn.commit()
    conn.close()


@pytest.fixture
def brain_db(tmp_path):
    db = tmp_path / "brain.fts.db"
    _build_synthetic_brain(db)
    return str(db)


def test_strip_quotes():
    assert _strip_quotes('"normal"') == "normal"
    assert _strip_quotes("'high'") == "high"
    assert _strip_quotes(" True ") == "true"
    assert _strip_quotes(None) == ""


def test_retrieve_returns_safe_notes(brain_db):
    rag = BrainBackroomRag(db_path=brain_db)
    results = rag.retrieve("database sqlite postgres")
    ids = {r["id"] for r in results}
    assert "2" in ids  # the safe database note


def test_high_sensitivity_note_is_excluded(brain_db):
    rag = BrainBackroomRag(db_path=brain_db)
    # Query that would match the secret salary note by content
    results = rag.retrieve("confidential salary negotiation private")
    ids = {r["id"] for r in results}
    assert "3" not in ids, "high-sensitivity note leaked through the gate"


def test_external_blocked_note_is_excluded(brain_db):
    rag = BrainBackroomRag(db_path=brain_db)
    results = rag.retrieve("this note must never reach external model")
    ids = {r["id"] for r in results}
    assert "4" not in ids, "external_llm=false note leaked through the gate"


def test_summary_is_truncated_not_full_body(brain_db):
    rag = BrainBackroomRag(db_path=brain_db, max_summary_chars=20)
    results = rag.retrieve("search infrastructure fts5")
    for r in results:
        assert len(r["sanitized_summary"]) <= 20


def test_shape_matches_protocol(brain_db):
    rag = BrainBackroomRag(db_path=brain_db)
    results = rag.retrieve("async programming patterns")
    for r in results:
        assert set(r.keys()) == {"id", "score", "sanitized_summary", "source_type"}
        assert 0.0 <= r["score"] <= 1.0


def test_safe_count_aggregates(brain_db):
    rag = BrainBackroomRag(db_path=brain_db)
    counts = rag.safe_count()
    assert counts["total"] == 5
    assert counts["gated"] == 2  # the high-sensitivity + external-blocked notes
    assert counts["safe"] == 3


def test_allowed_zones_filter(brain_db):
    rag = BrainBackroomRag(db_path=brain_db, allowed_zones=["lab"])
    results = rag.retrieve("search infrastructure fts5 database async")
    for r in results:
        assert r["source_type"] == "lab"


def test_read_only_blocks_writes(brain_db):
    rag = BrainBackroomRag(db_path=brain_db)
    rag.retrieve("warm up")
    with pytest.raises(sqlite3.OperationalError):
        rag._conn.execute("INSERT INTO notes (id, path, zone) VALUES (99, 'x', 'core')")


def test_missing_db_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        BrainBackroomRag(db_path=str(tmp_path / "nope.db"))


def test_empty_query_returns_empty(brain_db):
    rag = BrainBackroomRag(db_path=brain_db)
    assert rag.retrieve("") == []
    assert rag.retrieve("a") == []  # below trigram min length
