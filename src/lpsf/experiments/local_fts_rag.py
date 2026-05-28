"""LocalFTSRag — read-only RAG adapter over a SQLite FTS5 index.

Conforms to the EvidenceAdapter Protocol used by LPSF baselines:
    retrieve(query, *, scope=None, limit=20) -> List[Dict]

Returns only id / score / sanitized_summary / source_type. The raw body is
NEVER returned, mirroring MockRAG's no-body invariant.

The underlying database is built by `scripts/build_corpus.py` from
`data/corpus/*.md`. The connection is opened in URI read-only mode
(`mode=ro`) so the adapter physically cannot mutate the index.
"""

from __future__ import annotations

import math
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


def _bm25_to_score(bm25_value: float) -> float:
    """Map SQLite FTS5 bm25() output to a [0, 1] relevance score.

    bm25() returns smaller (more negative) values for better matches.
    We map by -bm25 / (1 + |-bm25|) so:
      bm25 = 0   → 0.0   (no match)
      bm25 = -1  → 0.5   (moderate)
      bm25 = -∞  → 1.0   (perfect)
    """
    neg = -float(bm25_value)
    if neg <= 0:
        return 0.0
    return neg / (1.0 + neg)


class LocalFTSRag:
    """Read-only FTS5 RAG adapter.

    Drop-in for MockRAG in any baseline. Same surface, real text corpus.
    """

    def __init__(
        self,
        *,
        db_path: str,
        snapshot_id: str = "local_fts_v1",
    ) -> None:
        self.db_path = str(db_path)
        self.snapshot_id = snapshot_id
        if not Path(self.db_path).exists():
            raise FileNotFoundError(
                f"FTS index not found at {self.db_path}. "
                f"Run scripts/build_corpus.py first."
            )
        # Lazy connection — opened on first retrieve()
        self._conn: Optional[sqlite3.Connection] = None

    def _connect(self) -> sqlite3.Connection:
        if self._conn is None:
            uri = f"file:{self.db_path}?mode=ro"
            self._conn = sqlite3.connect(uri, uri=True)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def retrieve(
        self,
        query: str,
        *,
        scope: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Returns sorted candidates by BM25 score (best first), with bodies stripped."""
        if not query or not query.strip():
            return []
        conn = self._connect()
        sanitized = self._sanitize_query(query)
        if not sanitized:
            return []
        try:
            rows = conn.execute(
                "SELECT notes.id AS id, meta.summary AS summary, "
                "meta.source_type AS source_type, bm25(notes) AS bm25 "
                "FROM notes JOIN meta ON notes.id = meta.id "
                "WHERE notes MATCH ? "
                "ORDER BY bm25 ASC "
                "LIMIT ?",
                (sanitized, int(limit)),
            ).fetchall()
        except sqlite3.OperationalError:
            return []
        return [
            {
                "id": row["id"],
                "score": _bm25_to_score(row["bm25"]),
                "sanitized_summary": row["summary"],
                "source_type": row["source_type"],
            }
            for row in rows
        ]

    @staticmethod
    def _sanitize_query(query: str) -> str:
        """Turn a free-text query into an FTS5 match expression.

        FTS5 MATCH supports words, phrases (double-quoted), and operators
        like AND / OR / NEAR. To stay safe with arbitrary user text we
        strip punctuation and OR-join the remaining tokens; this gives
        recall over precision, which is the right default for the
        first-stage retriever.
        """
        tokens = []
        for raw in query.split():
            cleaned = "".join(c for c in raw if c.isalnum() or c == "_")
            if cleaned:
                tokens.append(cleaned)
        return " OR ".join(tokens)
