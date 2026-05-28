"""Shared scenario helpers for M4 Phase 1 hypotheses.

Provides factories for synthetic experience_events, evidence_snapshots, and
RAG fixtures. All data is synthetic; no real brain content is loaded.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .mock_llm import MockLLM
from .mock_rag import MockRAG


SYNTHETIC_TIMESTAMP = "2026-05-23T22:00:00Z"


def insert_synthetic_snapshot(conn, *, snapshot_id: str = "snap_exp") -> str:
    """Insert a synthetic evidence_snapshots row directly (no adapter)."""
    conn.execute(
        """
        INSERT INTO evidence_snapshots (
            snapshot_id, adapter_version, allowed_scope, source_counts,
            index_metadata, retrieval_parameters, drift_observations,
            created_at, pinned_at
        )
        VALUES (?, 'mock-rag-v0', '["synthetic"]', '{"synthetic": 4}',
                '{"type": "mock"}', '{"limit": 20}', '[]', ?, ?)
        """,
        (snapshot_id, SYNTHETIC_TIMESTAMP, SYNTHETIC_TIMESTAMP),
    )
    return snapshot_id


def insert_synthetic_event(
    conn, *, snapshot_id: str, event_id: str = "evt_exp"
) -> str:
    conn.execute(
        """
        INSERT INTO experience_events (
            event_id, sanitized_summary, event_type, importance, novelty,
            outcome, goal_relevance, privacy_level, evidence_refs,
            snapshot_id, created_at
        )
        VALUES (?, 'synthetic experiment event', 'synthetic', 0.5, 0.5,
                'accepted', 0.7, 'D3', '["ev:fixture"]', ?, ?)
        """,
        (event_id, snapshot_id, SYNTHETIC_TIMESTAMP),
    )
    return event_id


def default_rag_fixture() -> Dict[str, List[Dict[str, Any]]]:
    """Fixture mapping query patterns to sanitized evidence refs."""
    return {
        "best path": [
            {
                "id": "ev:A",
                "score": 0.80,
                "sanitized_summary": "path A is grounded in source registry",
                "source_type": "synthetic",
            },
            {
                "id": "ev:B",
                "score": 0.60,
                "sanitized_summary": "path B is an alternative interpretation",
                "source_type": "synthetic",
            },
        ],
        "controversial topic": [
            {
                "id": "ev:X",
                "score": 0.70,
                "sanitized_summary": "topic X with conflicting evidence",
                "source_type": "synthetic",
            },
        ],
        "memory question": [
            {
                "id": "ev:M1",
                "score": 0.55,
                "sanitized_summary": "memory record one",
                "source_type": "synthetic",
            },
            {
                "id": "ev:M2",
                "score": 0.45,
                "sanitized_summary": "memory record two",
                "source_type": "synthetic",
            },
        ],
        "privacy query": [
            {
                "id": "ev:safe",
                "score": 0.50,
                "sanitized_summary": "safe public summary",
                "source_type": "synthetic",
            },
        ],
    }


def build_mock_world(
    conn,
    *,
    snapshot_id: str = "snap_exp",
    event_id: str = "evt_exp",
    seed: int = 0,
    rag_fixture: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    response_map: Optional[Dict[str, str]] = None,
) -> Tuple[str, str, MockLLM, MockRAG]:
    """Insert snapshot + event and return (snapshot_id, event_id, llm, rag)."""
    insert_synthetic_snapshot(conn, snapshot_id=snapshot_id)
    insert_synthetic_event(conn, snapshot_id=snapshot_id, event_id=event_id)
    llm = MockLLM(seed=seed, response_map=response_map or {})
    rag = MockRAG(
        snapshot_id=snapshot_id,
        fixture=rag_fixture or default_rag_fixture(),
    )
    return snapshot_id, event_id, llm, rag


def available_evidence_ids(
    rag_fixture: Optional[Dict[str, List[Dict[str, Any]]]] = None,
) -> List[str]:
    fixture = rag_fixture or default_rag_fixture()
    ids: List[str] = []
    for refs in fixture.values():
        for ref in refs:
            if ref["id"] not in ids:
                ids.append(ref["id"])
    return ids
