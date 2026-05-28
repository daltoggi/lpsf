"""reconsolidate_memory operator."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ._base import PolicyViolation, dumps, next_id, prepare_mark, result, supersede_active_marks


def reconsolidate_memory(
    conn,
    *,
    event_id: str,
    snapshot_id: str,
    old_target_id: str,
    new_target_id: str,
    preservation_note: str,
    strength: float,
    half_life: Optional[int],
    evidence_refs: List[str],
    reason: str,
    target_type: str = "memory",
    target_id: Optional[str] = None,
    scope: str = "global",
    score_delta_meta: Optional[Dict[str, Any]] = None,
    permanent: bool = False,
) -> Dict[str, Any]:
    if not old_target_id or not new_target_id:
        raise PolicyViolation("old_target_id and new_target_id are required")
    if not preservation_note:
        raise PolicyViolation("preservation_note is required")
    resolved_target_id = target_id or f"{old_target_id}->{new_target_id}"
    meta = {"old_target_id": old_target_id, "new_target_id": new_target_id}
    if score_delta_meta:
        meta.update(score_delta_meta)
    prepared = prepare_mark(
        conn,
        operator_type="reconsolidate_memory",
        event_id=event_id,
        snapshot_id=snapshot_id,
        target_type=target_type,
        target_id=resolved_target_id,
        strength=strength,
        half_life=half_life,
        evidence_refs=evidence_refs,
        reason=reason,
        scope=scope,
        score_delta_meta=meta,
        permanent=permanent,
    )
    superseded = supersede_active_marks(
        conn,
        operator_types=("reconsolidate_memory",),
        target_type=target_type,
        target_id=resolved_target_id,
        scope=scope,
        snapshot_id=snapshot_id,
        replacement_mark_id=prepared["mark_id"],
        updated_at=prepared["created_at"],
    )
    record_id = next_id(conn, "reconsolidation_records", "record")
    conn.execute(
        """
        INSERT INTO reconsolidation_records (
            record_id,
            old_target_id,
            new_target_id,
            reason,
            validation_status,
            source_experience_id,
            evidence_refs,
            preservation_note,
            snapshot_id,
            created_at
        )
        VALUES (?, ?, ?, ?, 'operator_active', ?, ?, ?, ?, ?)
        """,
        (
            record_id,
            old_target_id,
            new_target_id,
            reason,
            event_id,
            dumps(evidence_refs),
            preservation_note,
            snapshot_id,
            prepared["created_at"],
        ),
    )
    return result(
        prepared["mark_id"],
        {
            "record_id": record_id,
            "target_id": resolved_target_id,
            "old_target_id": old_target_id,
            "new_target_id": new_target_id,
            "superseded_marks": superseded,
            "blocked_by_priority": False,
        },
        prepared["warnings"],
    )
