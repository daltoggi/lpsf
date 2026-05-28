"""Shared helpers for M3 plasticity operators.

The helpers only inspect or mutate the supplied SQLite connection. They do not
read external files, call retrieval systems, or infer evidence content.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict, Iterable, List, Optional, Sequence

from lpsf import db
from lpsf.errors import LPSFError

from .priority import priority_rank


STRENGTH_CAP = 1.0


class OperatorError(LPSFError):
    """Base error for plasticity operator failures."""


class PolicyViolation(OperatorError):
    """Raised when an operator would violate the v0.1 policy boundary."""


class UnknownOperator(OperatorError):
    """Raised when the dispatcher receives an unknown operator name."""


class StateValidationError(OperatorError):
    """Raised when required state rows are missing or malformed."""


def validate_event(conn: sqlite3.Connection, event_id: str) -> None:
    if not event_id:
        raise StateValidationError("event_id is required")
    if get_event(conn, event_id) is None:
        raise StateValidationError(f"Unknown experience_event: {event_id}")


def validate_snapshot(conn: sqlite3.Connection, snapshot_id: str) -> None:
    if not snapshot_id:
        raise StateValidationError("snapshot_id is required")
    row = conn.execute(
        "SELECT snapshot_id FROM evidence_snapshots WHERE snapshot_id = ?",
        (snapshot_id,),
    ).fetchone()
    if row is None:
        raise StateValidationError(f"Unknown evidence_snapshot: {snapshot_id}")


def validate_evidence_refs(refs: Sequence[str]) -> None:
    if not isinstance(refs, list) or not refs:
        raise PolicyViolation("evidence_refs must be a non-empty list of ids")
    for ref in refs:
        if not isinstance(ref, str) or not ref.strip():
            raise PolicyViolation("evidence_refs must contain only non-empty strings")
        if len(ref) > 500 or "\n" in ref or "\r" in ref:
            raise PolicyViolation("evidence_refs must be ids, not evidence bodies")


def evidence_ref_guard(refs: Sequence[str], adapter: Any = None) -> None:
    validate_evidence_refs(refs)
    if adapter is None:
        return
    for ref in refs:
        if getattr(adapter, "is_blocked", lambda _source_id: False)(ref):
            raise PolicyViolation(f"Blocked evidence reference: {ref}")


def validate_strength(strength: float, *, allow_negative: bool = False) -> float:
    if isinstance(strength, bool) or not isinstance(strength, (int, float)):
        raise PolicyViolation("strength must be numeric")
    value = float(strength)
    if abs(value) > STRENGTH_CAP:
        raise PolicyViolation(f"strength exceeds cap {STRENGTH_CAP}")
    if value < 0 and not allow_negative:
        raise PolicyViolation("strength must be non-negative for this operator")
    return value


def validate_half_life(half_life: Optional[int], *, permanent: bool = False) -> int:
    if permanent:
        raise PolicyViolation("permanent marks are blocked in v0.1")
    if half_life is None:
        raise PolicyViolation("half_life=None would create a permanent mark in v0.1")
    if isinstance(half_life, bool) or not isinstance(half_life, int):
        raise PolicyViolation("half_life must be an integer number of seconds")
    if half_life <= 0:
        raise PolicyViolation("half_life must be positive")
    return half_life


def build_mark(
    conn: sqlite3.Connection,
    *,
    operator_type: str,
    target_type: str,
    target_id: str,
    strength: float,
    half_life: int,
    source_experience_id: str,
    evidence_refs: List[str],
    reason: str,
    privacy_level: str,
    scope: str,
    snapshot_id: str,
    created_at: str,
    score_delta_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if not target_type or not target_id:
        raise StateValidationError("target_type and target_id are required")
    if not reason or not isinstance(reason, str):
        raise StateValidationError("reason must be a non-empty string")
    if score_delta_meta is not None and not isinstance(score_delta_meta, dict):
        raise StateValidationError("score_delta_meta must be a dictionary")

    return {
        "mark_id": next_id(conn, "plasticity_marks", "mark"),
        "operator_type": operator_type,
        "target_type": target_type,
        "target_id": target_id,
        "strength": strength,
        "half_life": str(half_life),
        "source_experience_id": source_experience_id,
        "evidence_refs": list(evidence_refs),
        "reason": reason,
        "status": "active",
        "privacy_level": privacy_level,
        "scope": scope,
        "snapshot_id": snapshot_id,
        "created_at": created_at,
        "updated_at": created_at,
        "supersedes_mark_id": None,
        "reversed_by_mark_id": None,
        "score_delta_meta": score_delta_meta or {},
    }


def write_mark(conn: sqlite3.Connection, mark_dict: Dict[str, Any]) -> str:
    payload = dict(mark_dict)
    payload["evidence_refs"] = dumps(payload["evidence_refs"])
    payload["score_delta_meta"] = dumps(payload["score_delta_meta"])
    conn.execute(
        """
        INSERT INTO plasticity_marks (
            mark_id,
            operator_type,
            target_type,
            target_id,
            strength,
            half_life,
            source_experience_id,
            evidence_refs,
            reason,
            status,
            privacy_level,
            scope,
            snapshot_id,
            created_at,
            updated_at,
            supersedes_mark_id,
            reversed_by_mark_id,
            score_delta_meta
        )
        VALUES (
            :mark_id,
            :operator_type,
            :target_type,
            :target_id,
            :strength,
            :half_life,
            :source_experience_id,
            :evidence_refs,
            :reason,
            :status,
            :privacy_level,
            :scope,
            :snapshot_id,
            :created_at,
            :updated_at,
            :supersedes_mark_id,
            :reversed_by_mark_id,
            :score_delta_meta
        )
        """,
        payload,
    )
    return str(mark_dict["mark_id"])


def priority_check(
    operator_type: str, existing_active_marks: Iterable[Dict[str, Any]]
) -> List[str]:
    warnings = []
    current_rank = priority_rank(operator_type)
    for raw_mark in existing_active_marks:
        mark = dict(raw_mark)
        if mark.get("status") != "active":
            continue
        other_type = mark.get("operator_type")
        other_rank = priority_rank(other_type)
        if other_rank < current_rank:
            warnings.append(
                "higher-priority "
                f"{other_type} mark {mark.get('mark_id')} is active for target "
                f"{mark.get('target_id')}"
            )
    return warnings


def prepare_mark(
    conn: sqlite3.Connection,
    *,
    operator_type: str,
    event_id: str,
    snapshot_id: str,
    target_type: str,
    target_id: str,
    strength: float,
    half_life: Optional[int],
    evidence_refs: List[str],
    reason: str,
    scope: str,
    score_delta_meta: Optional[Dict[str, Any]],
    permanent: bool,
    allow_negative_strength: bool = False,
) -> Dict[str, Any]:
    event = require_event(conn, event_id)
    validate_snapshot(conn, snapshot_id)
    evidence_ref_guard(evidence_refs)
    bounded_strength = validate_strength(strength, allow_negative=allow_negative_strength)
    bounded_half_life = validate_half_life(half_life, permanent=permanent)
    existing_marks = active_marks_for_target(
        conn,
        target_type=target_type,
        target_id=target_id,
        scope=scope,
        snapshot_id=snapshot_id,
    )
    warnings = priority_check(operator_type, existing_marks)
    mark = build_mark(
        conn,
        operator_type=operator_type,
        target_type=target_type,
        target_id=target_id,
        strength=bounded_strength,
        half_life=bounded_half_life,
        source_experience_id=event_id,
        evidence_refs=evidence_refs,
        reason=reason,
        privacy_level=event["privacy_level"],
        scope=scope,
        snapshot_id=snapshot_id,
        created_at=event["created_at"],
        score_delta_meta=score_delta_meta,
    )
    mark_id = write_mark(conn, mark)
    return {
        "event": event,
        "mark_id": mark_id,
        "strength": bounded_strength,
        "half_life": bounded_half_life,
        "warnings": warnings,
        "blocked_by_priority": priority_blocked_by_inhibition(warnings),
        "created_at": event["created_at"],
    }


def active_marks_for_target(
    conn: sqlite3.Connection,
    *,
    target_type: str,
    target_id: str,
    scope: str,
    snapshot_id: str,
) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT * FROM plasticity_marks
        WHERE target_type = ?
          AND target_id = ?
          AND scope = ?
          AND snapshot_id = ?
          AND status = 'active'
        ORDER BY id
        """,
        (target_type, target_id, scope, snapshot_id),
    ).fetchall()
    return [dict(row) for row in rows]


def supersede_active_marks(
    conn: sqlite3.Connection,
    *,
    operator_types: Sequence[str],
    target_type: str,
    target_id: str,
    scope: str,
    snapshot_id: str,
    replacement_mark_id: str,
    updated_at: str,
) -> List[str]:
    if not operator_types:
        return []
    placeholders = ",".join("?" for _ in operator_types)
    rows = conn.execute(
        f"""
        SELECT mark_id FROM plasticity_marks
        WHERE operator_type IN ({placeholders})
          AND target_type = ?
          AND target_id = ?
          AND scope = ?
          AND snapshot_id = ?
          AND status = 'active'
          AND mark_id != ?
        ORDER BY id
        """,
        tuple(operator_types)
        + (target_type, target_id, scope, snapshot_id, replacement_mark_id),
    ).fetchall()
    superseded = []
    for row in rows:
        db.supersede_mark(
            conn,
            row["mark_id"],
            replacement_mark_id,
            updated_at=updated_at,
        )
        superseded.append(row["mark_id"])
    return superseded


def upsert_attractor(
    conn: sqlite3.Connection,
    *,
    target_path: str,
    depth_delta: float,
    threshold_delta: float,
    half_life: int,
    mark_id: str,
    snapshot_id: str,
    timestamp: str,
    decay_state_extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    row = conn.execute(
        "SELECT * FROM attractors WHERE target_path = ? AND snapshot_id = ?",
        (target_path, snapshot_id),
    ).fetchone()
    extra = decay_state_extra or {}
    if row is None:
        before_depth = 0.0
        before_threshold = 1.0
        after_depth = clamp(before_depth + depth_delta, 0.0, 1.0)
        after_threshold = clamp(before_threshold + threshold_delta, 0.0, 1.0)
        decay_state = {
            "remaining": 1.0,
            "half_life": half_life,
            "latest_mark": mark_id,
        }
        decay_state.update(extra)
        conn.execute(
            """
            INSERT INTO attractors (
                target_path,
                depth,
                activation_threshold,
                half_life,
                last_activation_at,
                source_marks,
                decay_state,
                snapshot_id,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                target_path,
                after_depth,
                after_threshold,
                str(half_life),
                timestamp,
                dumps([mark_id]),
                dumps(decay_state),
                snapshot_id,
                timestamp,
                timestamp,
            ),
        )
    else:
        before_depth = float(row["depth"])
        before_threshold = float(row["activation_threshold"])
        after_depth = clamp(before_depth + depth_delta, 0.0, 1.0)
        after_threshold = clamp(before_threshold + threshold_delta, 0.0, 1.0)
        source_marks = append_unique(loads(row["source_marks"], []), mark_id)
        decay_state = loads(row["decay_state"], {})
        decay_state.update(
            {
                "remaining": 1.0,
                "half_life": half_life,
                "latest_mark": mark_id,
            }
        )
        decay_state.update(extra)
        conn.execute(
            """
            UPDATE attractors
            SET depth = ?,
                activation_threshold = ?,
                half_life = ?,
                last_activation_at = ?,
                source_marks = ?,
                decay_state = ?,
                updated_at = ?
            WHERE target_path = ? AND snapshot_id = ?
            """,
            (
                after_depth,
                after_threshold,
                str(half_life),
                timestamp,
                dumps(source_marks),
                dumps(decay_state),
                timestamp,
                target_path,
                snapshot_id,
            ),
        )
    return {
        "target_id": target_path,
        "before_depth": before_depth,
        "after_depth": after_depth,
        "depth_delta": after_depth - before_depth,
        "before_activation_threshold": before_threshold,
        "after_activation_threshold": after_threshold,
        "activation_threshold_delta": after_threshold - before_threshold,
    }


def inhibit_attractor(
    conn: sqlite3.Connection,
    *,
    target_path: str,
    strength: float,
    half_life: int,
    mark_id: str,
    snapshot_id: str,
    timestamp: str,
) -> Dict[str, Any]:
    row = conn.execute(
        "SELECT * FROM attractors WHERE target_path = ? AND snapshot_id = ?",
        (target_path, snapshot_id),
    ).fetchone()
    if row is None:
        before_depth = 0.0
        before_threshold = 1.0
        source_marks = [mark_id]
        decay_state = {
            "remaining": 1.0,
            "half_life": half_life,
            "latest_mark": mark_id,
            "inhibition_strength": strength,
        }
        conn.execute(
            """
            INSERT INTO attractors (
                target_path,
                depth,
                activation_threshold,
                half_life,
                last_activation_at,
                source_marks,
                decay_state,
                snapshot_id,
                created_at,
                updated_at
            )
            VALUES (?, 0, 1, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                target_path,
                str(half_life),
                timestamp,
                dumps(source_marks),
                dumps(decay_state),
                snapshot_id,
                timestamp,
                timestamp,
            ),
        )
        after_depth = 0.0
        after_threshold = 1.0
    else:
        before_depth = float(row["depth"])
        before_threshold = float(row["activation_threshold"])
        after_depth = clamp(before_depth - strength, 0.0, 1.0)
        after_threshold = 1.0
        source_marks = append_unique(loads(row["source_marks"], []), mark_id)
        decay_state = loads(row["decay_state"], {})
        decay_state.update(
            {
                "remaining": 1.0,
                "half_life": half_life,
                "latest_mark": mark_id,
                "inhibition_strength": max(
                    float(decay_state.get("inhibition_strength", 0)), strength
                ),
            }
        )
        conn.execute(
            """
            UPDATE attractors
            SET depth = ?,
                activation_threshold = ?,
                half_life = ?,
                last_activation_at = ?,
                source_marks = ?,
                decay_state = ?,
                updated_at = ?
            WHERE target_path = ? AND snapshot_id = ?
            """,
            (
                after_depth,
                after_threshold,
                str(half_life),
                timestamp,
                dumps(source_marks),
                dumps(decay_state),
                timestamp,
                target_path,
                snapshot_id,
            ),
        )
    return {
        "target_id": target_path,
        "before_depth": before_depth,
        "after_depth": after_depth,
        "depth_delta": after_depth - before_depth,
        "before_activation_threshold": before_threshold,
        "after_activation_threshold": after_threshold,
        "activation_threshold_delta": after_threshold - before_threshold,
        "inhibition_strength": strength,
    }


def require_event(conn: sqlite3.Connection, event_id: str) -> Dict[str, Any]:
    if not event_id:
        raise StateValidationError("event_id is required")
    event = get_event(conn, event_id)
    if event is None:
        raise StateValidationError(f"Unknown experience_event: {event_id}")
    return event


def get_event(conn: sqlite3.Connection, event_id: str) -> Optional[Dict[str, Any]]:
    row = conn.execute(
        "SELECT * FROM experience_events WHERE event_id = ?", (event_id,)
    ).fetchone()
    return None if row is None else dict(row)


def result(mark_id: str, state_delta: Dict[str, Any], warnings: List[str]) -> Dict[str, Any]:
    return {"mark_id": mark_id, "state_delta": state_delta, "warnings": warnings}


def priority_blocked_by_inhibition(warnings: Sequence[str]) -> bool:
    return any("inhibit_path" in warning for warning in warnings)


def next_id(conn: sqlite3.Connection, table: str, prefix: str) -> str:
    allowed = {
        "plasticity_marks",
        "semantic_edges",
        "schema_mappings",
        "reconsolidation_records",
        "sensitivity_profiles",
    }
    if table not in allowed:
        raise StateValidationError(f"Unsupported id table: {table}")
    value = conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()[0]
    return f"{prefix}_{int(value):06d}"


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, float(value)))


def append_unique(values: List[Any], value: Any) -> List[Any]:
    if value not in values:
        values.append(value)
    return values


def loads(raw: Any, default: Any) -> Any:
    if raw is None:
        return default
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return default


def dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))
