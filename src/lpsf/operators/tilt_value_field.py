"""tilt_value_field operator."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ._base import (
    append_unique,
    clamp,
    dumps,
    loads,
    prepare_mark,
    result,
    supersede_active_marks,
)


def tilt_value_field(
    conn,
    *,
    event_id: str,
    snapshot_id: str,
    axis_name: str,
    strength: float,
    half_life: Optional[int],
    evidence_refs: List[str],
    reason: str,
    target_type: str = "value_axis",
    scope: str = "global",
    score_delta_meta: Optional[Dict[str, Any]] = None,
    permanent: bool = False,
) -> Dict[str, Any]:
    meta = {"axis_name": axis_name, "latest_delta": strength}
    if score_delta_meta:
        meta.update(score_delta_meta)
    prepared = prepare_mark(
        conn,
        operator_type="tilt_value_field",
        event_id=event_id,
        snapshot_id=snapshot_id,
        target_type=target_type,
        target_id=axis_name,
        strength=strength,
        half_life=half_life,
        evidence_refs=evidence_refs,
        reason=reason,
        scope=scope,
        score_delta_meta=meta,
        permanent=permanent,
        allow_negative_strength=True,
    )
    if prepared["blocked_by_priority"]:
        return result(
            prepared["mark_id"],
            {"axis_name": axis_name, "weight_delta": 0.0, "blocked_by_priority": True},
            prepared["warnings"],
        )
    superseded = supersede_active_marks(
        conn,
        operator_types=("tilt_value_field",),
        target_type=target_type,
        target_id=axis_name,
        scope=scope,
        snapshot_id=snapshot_id,
        replacement_mark_id=prepared["mark_id"],
        updated_at=prepared["created_at"],
    )
    state_delta = _upsert_weight(
        conn,
        axis_name=axis_name,
        scope=scope,
        strength=prepared["strength"],
        half_life=prepared["half_life"],
        mark_id=prepared["mark_id"],
        snapshot_id=snapshot_id,
        timestamp=prepared["created_at"],
    )
    state_delta["superseded_marks"] = superseded
    state_delta["blocked_by_priority"] = False
    return result(prepared["mark_id"], state_delta, prepared["warnings"])


def _upsert_weight(
    conn,
    *,
    axis_name,
    scope,
    strength,
    half_life,
    mark_id,
    snapshot_id,
    timestamp,
):
    row = conn.execute(
        """
        SELECT * FROM value_field_weights
        WHERE axis_name = ? AND scope = ? AND snapshot_id = ?
        """,
        (axis_name, scope, snapshot_id),
    ).fetchone()
    if row is None:
        before = 0.0
        after = clamp(strength, -1.0, 1.0)
        conn.execute(
            """
            INSERT INTO value_field_weights (
                axis_name,
                scope,
                weight,
                source_marks,
                decay_state,
                score_contribution_meta,
                snapshot_id,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                axis_name,
                scope,
                after,
                dumps([mark_id]),
                dumps({"remaining": 1.0, "half_life": half_life, "latest_mark": mark_id}),
                dumps({"latest_delta": strength}),
                snapshot_id,
                timestamp,
                timestamp,
            ),
        )
    else:
        before = float(row["weight"])
        after = clamp(before + strength, -1.0, 1.0)
        source_marks = append_unique(loads(row["source_marks"], []), mark_id)
        decay_state = loads(row["decay_state"], {})
        decay_state.update(
            {"remaining": 1.0, "half_life": half_life, "latest_mark": mark_id}
        )
        score_meta = loads(row["score_contribution_meta"], {})
        score_meta["latest_delta"] = strength
        conn.execute(
            """
            UPDATE value_field_weights
            SET weight = ?,
                source_marks = ?,
                decay_state = ?,
                score_contribution_meta = ?,
                updated_at = ?
            WHERE axis_name = ? AND scope = ? AND snapshot_id = ?
            """,
            (
                after,
                dumps(source_marks),
                dumps(decay_state),
                dumps(score_meta),
                timestamp,
                axis_name,
                scope,
                snapshot_id,
            ),
        )
    return {
        "axis_name": axis_name,
        "before_weight": before,
        "after_weight": after,
        "weight_delta": after - before,
    }
