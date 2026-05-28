"""open_path operator."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ._base import (
    PolicyViolation,
    dumps,
    next_id,
    prepare_mark,
    result,
)


ALLOWED_RELATION_TYPES = {
    "supports",
    "inhibits",
    "reinterprets",
    "supersedes",
    "tension_with",
}


def open_path(
    conn,
    *,
    event_id: str,
    snapshot_id: str,
    target_type: str,
    target_id: str,
    source_target_id: str,
    relation_type: str = "open",
    strength: float,
    half_life: Optional[int],
    evidence_refs: List[str],
    reason: str,
    scope: str = "global",
    score_delta_meta: Optional[Dict[str, Any]] = None,
    permanent: bool = False,
) -> Dict[str, Any]:
    if not source_target_id:
        raise PolicyViolation("source_target_id is required")
    edge_target_id = f"{source_target_id}->{target_id}"
    warnings = []
    stored_relation_type = relation_type
    if relation_type == "open":
        stored_relation_type = "supports"
        warnings.append("relation_type 'open' mapped to schema relation 'supports'")
    if stored_relation_type not in ALLOWED_RELATION_TYPES:
        raise PolicyViolation(f"Unsupported relation_type: {relation_type}")
    meta = {"relation_type": relation_type, "stored_relation_type": stored_relation_type}
    if score_delta_meta:
        meta.update(score_delta_meta)
    prepared = prepare_mark(
        conn,
        operator_type="open_path",
        event_id=event_id,
        snapshot_id=snapshot_id,
        target_type=target_type,
        target_id=edge_target_id,
        strength=strength,
        half_life=half_life,
        evidence_refs=evidence_refs,
        reason=reason,
        scope=scope,
        score_delta_meta=meta,
        permanent=permanent,
    )
    warnings.extend(prepared["warnings"])
    if prepared["blocked_by_priority"]:
        return result(
            prepared["mark_id"],
            {"target_id": edge_target_id, "blocked_by_priority": True},
            warnings,
        )

    _ensure_node(conn, source_target_id, evidence_refs, snapshot_id, prepared["created_at"])
    _ensure_node(conn, target_id, evidence_refs, snapshot_id, prepared["created_at"])
    edge_id = next_id(conn, "semantic_edges", "edge")
    conn.execute(
        """
        INSERT INTO semantic_edges (
            edge_id,
            source_node_id,
            target_node_id,
            relation_type,
            weight,
            validation_status,
            evidence_refs,
            snapshot_id,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, 'operator_active', ?, ?, ?)
        """,
        (
            edge_id,
            source_target_id,
            target_id,
            stored_relation_type,
            prepared["strength"],
            dumps(evidence_refs),
            snapshot_id,
            prepared["created_at"],
        ),
    )
    return result(
        prepared["mark_id"],
        {
            "edge_id": edge_id,
            "source_target_id": source_target_id,
            "target_id": target_id,
            "relation_type": stored_relation_type,
            "weight_delta": prepared["strength"],
            "blocked_by_priority": False,
        },
        warnings,
    )


def _ensure_node(conn, node_id, evidence_refs, snapshot_id, created_at):
    conn.execute(
        """
        INSERT OR IGNORE INTO semantic_nodes (
            node_id,
            node_type,
            label,
            validation_status,
            evidence_refs,
            snapshot_id,
            created_at
        )
        VALUES (?, 'concept', ?, 'operator_created', ?, ?, ?)
        """,
        (node_id, node_id, dumps(evidence_refs), snapshot_id, created_at),
    )
