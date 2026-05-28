"""inhibit_path operator."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ._base import inhibit_attractor, prepare_mark, result


def inhibit_path(
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
    meta = {"inhibition_strength": strength, "priority": "highest"}
    if score_delta_meta:
        meta.update(score_delta_meta)
    prepared = prepare_mark(
        conn,
        operator_type="inhibit_path",
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
    state_delta = inhibit_attractor(
        conn,
        target_path=target_id,
        strength=prepared["strength"],
        half_life=prepared["half_life"],
        mark_id=prepared["mark_id"],
        snapshot_id=snapshot_id,
        timestamp=prepared["created_at"],
    )
    state_delta["blocked_by_priority"] = False
    return result(prepared["mark_id"], state_delta, prepared["warnings"])
