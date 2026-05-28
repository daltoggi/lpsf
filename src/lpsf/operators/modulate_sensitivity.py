"""modulate_sensitivity operator."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

from ._base import (
    PolicyViolation,
    append_unique,
    clamp,
    dumps,
    loads,
    prepare_mark,
    result,
    supersede_active_marks,
)


def modulate_sensitivity(
    conn,
    *,
    event_id: str,
    snapshot_id: str,
    trigger_pattern: str,
    gain: float,
    threshold: float,
    strength: float,
    half_life: Optional[int],
    evidence_refs: List[str],
    reason: str,
    target_type: str = "sensitivity_profile",
    scope: str = "global",
    hard_policy: bool = False,
    score_delta_meta: Optional[Dict[str, Any]] = None,
    permanent: bool = False,
) -> Dict[str, Any]:
    if not trigger_pattern or not isinstance(trigger_pattern, str):
        raise PolicyViolation("trigger_pattern is required")
    if isinstance(gain, bool) or not isinstance(gain, (int, float)) or gain < 0:
        raise PolicyViolation("gain must be a non-negative number")
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
        raise PolicyViolation("threshold must be numeric")
    profile_id = _profile_id(trigger_pattern, scope, snapshot_id)
    meta = {
        "trigger_pattern": trigger_pattern,
        "gain": gain,
        "threshold": threshold,
        "hard_policy": bool(hard_policy),
    }
    if score_delta_meta:
        meta.update(score_delta_meta)
    prepared = prepare_mark(
        conn,
        operator_type="modulate_sensitivity",
        event_id=event_id,
        snapshot_id=snapshot_id,
        target_type=target_type,
        target_id=profile_id,
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
                "profile_id": profile_id,
                "gain_delta": 0.0,
                "threshold_delta": 0.0,
                "blocked_by_priority": True,
            },
            prepared["warnings"],
        )
    superseded = supersede_active_marks(
        conn,
        operator_types=("modulate_sensitivity",),
        target_type=target_type,
        target_id=profile_id,
        scope=scope,
        snapshot_id=snapshot_id,
        replacement_mark_id=prepared["mark_id"],
        updated_at=prepared["created_at"],
    )
    state_delta = _upsert_profile(
        conn,
        profile_id=profile_id,
        trigger_pattern=trigger_pattern,
        gain=float(gain),
        threshold=float(threshold),
        scope=scope,
        hard_policy=hard_policy,
        half_life=prepared["half_life"],
        mark_id=prepared["mark_id"],
        snapshot_id=snapshot_id,
        timestamp=prepared["created_at"],
    )
    state_delta["superseded_marks"] = superseded
    state_delta["blocked_by_priority"] = False
    return result(prepared["mark_id"], state_delta, prepared["warnings"])


def _upsert_profile(
    conn,
    *,
    profile_id,
    trigger_pattern,
    gain,
    threshold,
    scope,
    hard_policy,
    half_life,
    mark_id,
    snapshot_id,
    timestamp,
):
    row = conn.execute(
        "SELECT * FROM sensitivity_profiles WHERE profile_id = ?", (profile_id,)
    ).fetchone()
    if row is None:
        before_gain = 1.0
        before_threshold = 0.0
        effective_hard_policy = bool(hard_policy)
        conn.execute(
            """
            INSERT INTO sensitivity_profiles (
                profile_id,
                trigger_pattern,
                gain,
                threshold,
                scope,
                hard_policy,
                false_positive_observations,
                source_marks,
                decay_state,
                snapshot_id,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, '[]', ?, ?, ?, ?, ?)
            """,
            (
                profile_id,
                trigger_pattern,
                gain,
                threshold,
                scope,
                1 if effective_hard_policy else 0,
                dumps([mark_id]),
                dumps({"remaining": 1.0, "half_life": half_life, "latest_mark": mark_id}),
                snapshot_id,
                timestamp,
                timestamp,
            ),
        )
    else:
        before_gain = float(row["gain"])
        before_threshold = float(row["threshold"])
        source_marks = append_unique(loads(row["source_marks"], []), mark_id)
        decay_state = loads(row["decay_state"], {})
        decay_state.update(
            {"remaining": 1.0, "half_life": half_life, "latest_mark": mark_id}
        )
        effective_hard_policy = bool(row["hard_policy"]) or bool(hard_policy)
        conn.execute(
            """
            UPDATE sensitivity_profiles
            SET gain = ?,
                threshold = ?,
                hard_policy = ?,
                source_marks = ?,
                decay_state = ?,
                updated_at = ?
            WHERE profile_id = ?
            """,
            (
                gain,
                threshold,
                1 if effective_hard_policy else 0,
                dumps(source_marks),
                dumps(decay_state),
                timestamp,
                profile_id,
            ),
        )
    return {
        "profile_id": profile_id,
        "trigger_pattern": trigger_pattern,
        "before_gain": before_gain,
        "after_gain": gain,
        "gain_delta": gain - before_gain,
        "before_threshold": before_threshold,
        "after_threshold": threshold,
        "threshold_delta": threshold - before_threshold,
        "hard_policy": effective_hard_policy,
    }


def _profile_id(trigger_pattern, scope, snapshot_id):
    digest = hashlib.sha256(
        f"{trigger_pattern}|{scope}|{snapshot_id}".encode("utf-8")
    ).hexdigest()[:16]
    return f"profile_{digest}"
