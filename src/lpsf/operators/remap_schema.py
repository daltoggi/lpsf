"""remap_schema operator."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ._base import PolicyViolation, dumps, next_id, prepare_mark, result, supersede_active_marks


def remap_schema(
    conn,
    *,
    event_id: str,
    snapshot_id: str,
    old_schema: str,
    new_schema: str,
    affected_targets: List[str],
    preservation_note: str,
    strength: float,
    half_life: Optional[int],
    evidence_refs: List[str],
    reason: str,
    target_type: str = "schema",
    target_id: Optional[str] = None,
    scope: str = "global",
    score_delta_meta: Optional[Dict[str, Any]] = None,
    permanent: bool = False,
) -> Dict[str, Any]:
    if not old_schema or not new_schema:
        raise PolicyViolation("old_schema and new_schema are required")
    if not isinstance(affected_targets, list) or not all(
        isinstance(item, str) for item in affected_targets
    ):
        raise PolicyViolation("affected_targets must be a list of strings")
    if not preservation_note:
        raise PolicyViolation("preservation_note is required")
    resolved_target_id = target_id or f"{old_schema}->{new_schema}"
    meta = {
        "old_schema": old_schema,
        "new_schema": new_schema,
        "affected_targets": affected_targets,
    }
    if score_delta_meta:
        meta.update(score_delta_meta)
    prepared = prepare_mark(
        conn,
        operator_type="remap_schema",
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
        operator_types=("remap_schema",),
        target_type=target_type,
        target_id=resolved_target_id,
        scope=scope,
        snapshot_id=snapshot_id,
        replacement_mark_id=prepared["mark_id"],
        updated_at=prepared["created_at"],
    )
    mapping_id = next_id(conn, "schema_mappings", "mapping")
    conn.execute(
        """
        INSERT INTO schema_mappings (
            mapping_id,
            old_schema,
            new_schema,
            affected_targets,
            reason,
            validation_status,
            source_experience_id,
            evidence_refs,
            preservation_note,
            snapshot_id,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, 'operator_active', ?, ?, ?, ?, ?)
        """,
        (
            mapping_id,
            old_schema,
            new_schema,
            dumps(affected_targets),
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
            "mapping_id": mapping_id,
            "target_id": resolved_target_id,
            "old_schema": old_schema,
            "new_schema": new_schema,
            "affected_targets": affected_targets,
            "superseded_marks": superseded,
            "blocked_by_priority": False,
        },
        prepared["warnings"],
    )
