"""deepen_attractor operator."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ._base import prepare_mark, result, supersede_active_marks, upsert_attractor


def deepen_attractor(
    conn,
    *,
    event_id: str,
    snapshot_id: str,
    target_type: str,
    target_id: str,
    strength: float,
    half_life: Optional[int],
    evidence_refs: List[str],
    reason: str,
    scope: str = "global",
    score_delta_meta: Optional[Dict[str, Any]] = None,
    permanent: bool = False,
) -> Dict[str, Any]:
    meta = {"depth_delta": strength, "activation_threshold_delta": -strength * 0.1}
    if score_delta_meta:
        meta.update(score_delta_meta)
    prepared = prepare_mark(
        conn,
        operator_type="deepen_attractor",
        event_id=event_id,
        snapshot_id=snapshot_id,
        target_type=target_type,
        target_id=target_id,
        strength=strength,
        half_life=half_life,
        evidence_refs=evidence_refs,
        reason=reason,
        scope=scope,
        score_delta_meta=meta,
        permanent=permanent,
    )
    if prepared["blocked_by_priority"]:
        return result(
            prepared["mark_id"],
            {
                "target_id": target_id,
                "depth_delta": 0.0,
                "activation_threshold_delta": 0.0,
                "blocked_by_priority": True,
            },
            prepared["warnings"],
        )
    superseded = supersede_active_marks(
        conn,
        operator_types=("weaken_attractor",),
        target_type=target_type,
        target_id=target_id,
        scope=scope,
        snapshot_id=snapshot_id,
        replacement_mark_id=prepared["mark_id"],
        updated_at=prepared["created_at"],
    )
    state_delta = upsert_attractor(
        conn,
        target_path=target_id,
        depth_delta=prepared["strength"],
        threshold_delta=-prepared["strength"] * 0.1,
        half_life=prepared["half_life"],
        mark_id=prepared["mark_id"],
        snapshot_id=snapshot_id,
        timestamp=prepared["created_at"],
    )
    state_delta["superseded_marks"] = superseded
    state_delta["blocked_by_priority"] = False
    return result(prepared["mark_id"], state_delta, prepared["warnings"])
