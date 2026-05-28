"""BrainBackroomRag — read-only RAG adapter over an external 2nd-brain FTS index.

Reads from a SQLite FTS5 index that follows the brain-backroom schema:
    notes(id, path, zone, title, type, content, sensitivity, external_llm, ...)
    notes_fts USING fts5(title, content, content='notes', tokenize='trigram')

Safety invariants (enforced here, not optional):
  1. Connection is opened read-only (URI mode=ro). Writes are impossible.
  2. Any note whose `sensitivity` is 'high' (quote-insensitive) OR whose
     `external_llm` is 'false' is EXCLUDED from results — it can never be
     surfaced to an external LLM through this adapter.
  3. Only a truncated summary of `content` is returned, never the full body.

The adapter exposes the same surface as MockRAG / LocalFTSRag:
    retrieve(query, *, scope=None, limit=20) -> List[Dict]

The path to the index is configurable; it is NOT hard-coded to any user
directory, and there is no default that points at a personal path.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


def _strip_quotes(value: Optional[str]) -> str:
    if value is None:
        return ""
    return value.strip().strip('"').strip("'").strip().lower()


def _bm25_to_score(bm25_value: float) -> float:
    neg = -float(bm25_value)
    if neg <= 0:
        return 0.0
    return neg / (1.0 + neg)


class BrainBackroomRag:
    """Read-only, sensitivity-gated FTS5 adapter for an external brain index."""

    MIN_TRIGRAM_LEN = 3

    def __init__(
        self,
        *,
        db_path: str,
        snapshot_id: str = "brain_backroom_v1",
        max_summary_chars: int = 200,
        allowed_zones: Optional[List[str]] = None,
    ) -> None:
        self.db_path = str(db_path)
        self.snapshot_id = snapshot_id
        self.max_summary_chars = max_summary_chars
        self.allowed_zones = set(allowed_zones) if allowed_zones else None
        if not Path(self.db_path).exists():
            raise FileNotFoundError(
                f"Brain FTS index not found at {self.db_path}."
            )
        self._conn: Optional[sqlite3.Connection] = None

    def _connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _is_safe(self, row: sqlite3.Row) -> bool:
        """Defensive gate. Excludes high-sensitivity or external-blocked notes."""
        sensitivity = _strip_quotes(row["sensitivity"] if "sensitivity" in row.keys() else None)
        external_llm = _strip_quotes(row["external_llm"] if "external_llm" in row.keys() else None)
        if sensitivity == "high":
            return False
        if external_llm == "false":
            return False
        if self.allowed_zones is not None:
            zone = _strip_quotes(row["zone"] if "zone" in row.keys() else None)
            if zone not in self.allowed_zones:
                return False
        return True

    def _summary(self, content: Optional[str]) -> str:
        if not content:
            return ""
        compact = " ".join(content.split())
        if len(compact) > self.max_summary_chars:
            return compact[: self.max_summary_chars - 3] + "..."
        return compact

    def retrieve(
        self,
        query: str,
        *,
        scope: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        if not query or not query.strip():
            return []
        match_expr = self._sanitize_query(query)
        if not match_expr:
            return []
        conn = self._connect()
        # Over-fetch so post-filtering for sensitivity still yields `limit`.
        fetch = max(int(limit) * 4, int(limit))
        try:
            rows = conn.execute(
                "SELECT n.id AS id, n.zone AS zone, n.title AS title, "
                "n.content AS content, n.sensitivity AS sensitivity, "
                "n.external_llm AS external_llm, bm25(notes_fts) AS bm25 "
                "FROM notes_fts "
                "JOIN notes n ON n.id = notes_fts.rowid "
                "WHERE notes_fts MATCH ? "
                "ORDER BY bm25 ASC "
                "LIMIT ?",
                (match_expr, fetch),
            ).fetchall()
        except sqlite3.OperationalError:
            return []

        out: List[Dict[str, Any]] = []
        for row in rows:
            if not self._is_safe(row):
                continue
            out.append(
                {
                    "id": str(row["id"]),
                    "score": _bm25_to_score(row["bm25"]),
                    "sanitized_summary": self._summary(row["content"]),
                    "source_type": _strip_quotes(row["zone"]) or "brain",
                }
            )
            if len(out) >= int(limit):
                break
        return out

    def safe_count(self) -> Dict[str, int]:
        """Aggregate-only diagnostic: how many notes pass / fail the gate.

        Returns counts, never content. Useful for logging without leakage.
        Filtering is done in Python to avoid SQL quote-escaping fragility.
        """
        conn = self._connect()
        rows = conn.execute("SELECT sensitivity, external_llm FROM notes").fetchall()
        total = len(rows)
        safe = 0
        for row in rows:
            sensitivity = _strip_quotes(row["sensitivity"])
            external_llm = _strip_quotes(row["external_llm"])
            if sensitivity == "high":
                continue
            if external_llm == "false":
                continue
            safe += 1
        return {"total": total, "safe": safe, "gated": total - safe}

    @classmethod
    def _sanitize_query(cls, query: str) -> str:
        """Trigram FTS needs tokens of length >= 3. OR-join for recall."""
        tokens = []
        for raw in query.split():
            cleaned = "".join(c for c in raw if c.isalnum() or c == "_")
            if len(cleaned) >= cls.MIN_TRIGRAM_LEN:
                tokens.append(f'"{cleaned}"')
        return " OR ".join(tokens)
