"""Deterministic mock RAG adapter for M4 Phase 1 experiments.

Satisfies the EvidenceAdapter Protocol from src/lpsf/adapter.py.
Fixture-driven, no network, no file I/O, never returns bodies.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


class MockRAG:
    """Fixture-driven evidence retrieval stub satisfying EvidenceAdapter."""

    def __init__(
        self,
        *,
        snapshot_id: str,
        fixture: Dict[str, List[Dict[str, Any]]],
        blocked_ids: Optional[set] = None,
    ) -> None:
        self._snapshot_id = snapshot_id
        self._fixture = fixture  # {query_pattern: [evidence_ref_dict, ...]}
        self._blocked_ids: set = blocked_ids or set()

    def version(self) -> str:
        return "mock-rag-v0"

    def allowed_scope(self) -> List[str]:
        return ["synthetic"]

    def snapshot_metadata(self) -> Dict[str, Any]:
        return {
            "index_metadata": {"type": "mock", "snapshot_id": self._snapshot_id},
            "source_counts": {"synthetic": len(self._fixture)},
            "retrieval_parameters": {"limit": 20, "engine": "mock"},
        }

    def retrieve(
        self,
        query: str,
        scope: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Return sanitized evidence refs matching the query pattern.

        Evidence refs contain only id, score, sanitized_summary, source_type.
        Bodies are NEVER included.
        """
        results: List[Dict[str, Any]] = []
        for pattern, refs in self._fixture.items():
            if pattern in query or re.search(pattern, query):
                for ref in refs:
                    sanitized = {
                        "id": ref["id"],
                        "score": ref.get("score", 0.5),
                        "sanitized_summary": ref.get("sanitized_summary", ""),
                        "source_type": ref.get("source_type", "synthetic"),
                    }
                    # Never leak body content
                    results.append(sanitized)
        return results[:limit]

    def is_blocked(self, source_id: str) -> bool:
        return source_id in self._blocked_ids
