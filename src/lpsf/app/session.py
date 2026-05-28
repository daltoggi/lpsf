"""LPSFSearchSession — a persistent, personalizing search session.

Wires retrieval (any EvidenceAdapter) + LPSF reranking + on-disk attractor
state into a loop:

    search(query)            -> ranked results (RAG + accumulated attractors [+ LLM judge])
    record_pick(query, id)   -> writes an experience_event + deepen_attractor

Because the state DB is on disk, attractors accumulate across process
invocations. The more a user picks a given note, the higher it ranks on
future related queries. That is the entire personalization mechanism, and
it is auditable: every pick is an experience_event row, every nudge is a
plasticity_mark row.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from lpsf import db as db_mod
from lpsf.experiments.baselines import LLMPlusLPSF, LLMPlusLPSFRerank
from lpsf.operators.deepen_attractor import deepen_attractor


@dataclass
class SearchResult:
    """One ranked candidate returned by a search."""

    rank: int
    evidence_id: str
    path: str
    amplitude: float
    rag_score: float
    attractor_depth: float
    summary: str
    picked_before: int  # how many times this note was picked in the past


class LPSFSearchSession:
    """A persistent search session with attractor-based personalization."""

    def __init__(
        self,
        *,
        state_db_path: Union[str, Path],
        rag: Any,
        llm: Optional[Any] = None,
        judge_llm: Optional[Any] = None,
        snapshot_id: str = "app_v1",
        use_rerank: bool = False,
        alpha: float = 1.0,
        beta: float = 1.0,
        gamma: float = 1.0,
        pick_strength: float = 0.3,
        pick_half_life: int = 30 * 24 * 3600,  # 30 days; picks fade slowly
    ) -> None:
        self.state_db_path = str(state_db_path)
        self.rag = rag
        self.llm = llm
        self.judge_llm = judge_llm
        self.snapshot_id = snapshot_id
        self.use_rerank = use_rerank
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.pick_strength = pick_strength
        self.pick_half_life = pick_half_life

        self.conn = db_mod.init_db(self.state_db_path)
        self._ensure_snapshot()

    # ---------- lifecycle -------------------------------------------------

    def close(self) -> None:
        self.conn.close()

    def _ensure_snapshot(self) -> None:
        row = self.conn.execute(
            "SELECT 1 FROM evidence_snapshots WHERE snapshot_id = ?",
            (self.snapshot_id,),
        ).fetchone()
        if row is not None:
            return
        now = _now_iso()
        self.conn.execute(
            """
            INSERT INTO evidence_snapshots (
                snapshot_id, adapter_version, allowed_scope, source_counts,
                index_metadata, retrieval_parameters, drift_observations,
                created_at, pinned_at
            )
            VALUES (?, 'app-v1', '["app"]', '{}', '{}', '{}', '[]', ?, ?)
            """,
            (self.snapshot_id, now, now),
        )
        self.conn.commit()

    # ---------- search ----------------------------------------------------

    def search(self, query: str, *, limit: int = 5) -> List[SearchResult]:
        evidence = self.rag.retrieve(query, scope=None, limit=max(limit, 20))
        summaries = {ref["id"]: ref.get("sanitized_summary", "") for ref in evidence}
        rag_scores = {f"path:{ref['id']}": float(ref.get("score", 0.0)) for ref in evidence}

        baseline = self._make_baseline()
        resp = baseline.respond(
            self.conn,
            query=query,
            snapshot_id=self.snapshot_id,
            llm=self.llm,
            rag=self.rag,
            seed=0,
        )

        attractors = _load_attractor_depths(self.conn, self.snapshot_id)
        pick_counts = self._pick_counts()

        ranked = sorted(
            resp.amplitudes.items(), key=lambda kv: kv[1], reverse=True
        )
        results: List[SearchResult] = []
        for i, (path, amp) in enumerate(ranked[:limit], start=1):
            evidence_id = path.split("path:", 1)[-1]
            results.append(
                SearchResult(
                    rank=i,
                    evidence_id=evidence_id,
                    path=path,
                    amplitude=round(float(amp), 4),
                    rag_score=round(rag_scores.get(path, 0.0), 4),
                    attractor_depth=round(attractors.get(path, 0.0), 4),
                    summary=summaries.get(evidence_id, ""),
                    picked_before=pick_counts.get(path, 0),
                )
            )
        return results

    # ---------- feedback --------------------------------------------------

    def record_pick(self, picked_evidence_id: str, *, query: str = "") -> Dict[str, Any]:
        """Record a user selection: write an experience_event + deepen the attractor.

        Returns a small dict describing the event and the resulting depth delta.
        """
        path = (
            picked_evidence_id
            if picked_evidence_id.startswith("path:")
            else f"path:{picked_evidence_id}"
        )
        evidence_id = path.split("path:", 1)[-1]
        event_id = self._insert_pick_event(evidence_id, query)
        result = deepen_attractor(
            self.conn,
            event_id=event_id,
            snapshot_id=self.snapshot_id,
            target_type="path",
            target_id=path,
            strength=self.pick_strength,
            half_life=self.pick_half_life,
            evidence_refs=[evidence_id],
            reason=f"user pick for query: {query[:80]}",
            scope="app",
        )
        self.conn.commit()
        return {
            "event_id": event_id,
            "path": path,
            "delta": result.get("state_delta", result),
        }

    # ---------- internals -------------------------------------------------

    def _make_baseline(self):
        if self.use_rerank:
            return LLMPlusLPSFRerank(
                alpha=self.alpha,
                beta=self.beta,
                gamma=self.gamma,
                judge_llm=self.judge_llm,
            )
        return LLMPlusLPSF()

    def _insert_pick_event(self, evidence_id: str, query: str) -> str:
        n = self.conn.execute(
            "SELECT COALESCE(MAX(id), 0) + 1 FROM experience_events"
        ).fetchone()[0]
        event_id = f"pick_{int(n):06d}"
        self.conn.execute(
            """
            INSERT INTO experience_events (
                event_id, sanitized_summary, event_type, importance, novelty,
                outcome, goal_relevance, privacy_level, evidence_refs,
                snapshot_id, created_at
            )
            VALUES (?, ?, 'user_pick', 0.6, 0.4, 'accepted', 0.8, 'D3', ?, ?, ?)
            """,
            (
                event_id,
                f"user picked {evidence_id}",
                f'["{evidence_id}"]',
                self.snapshot_id,
                _now_iso(),
            ),
        )
        return event_id

    def _pick_counts(self) -> Dict[str, int]:
        rows = self.conn.execute(
            """
            SELECT target_id, COUNT(*) AS n
            FROM plasticity_marks
            WHERE snapshot_id = ? AND operator_type = 'deepen_attractor'
                  AND scope = 'app'
            GROUP BY target_id
            """,
            (self.snapshot_id,),
        ).fetchall()
        return {row["target_id"]: int(row["n"]) for row in rows}


def _load_attractor_depths(conn: sqlite3.Connection, snapshot_id: str) -> Dict[str, float]:
    from lpsf.experiments.baselines import _load_attractors

    return {k: v["depth"] for k, v in _load_attractors(conn, snapshot_id).items()}


def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
