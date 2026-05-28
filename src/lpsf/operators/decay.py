"""Half-life processing for M3 secondary landscape tables."""

from __future__ import annotations

import math
from datetime import datetime

from ._base import StateValidationError, clamp, dumps, loads, validate_snapshot


def apply_decay(conn, now: int, snapshot_id: str):
    validate_snapshot(conn, snapshot_id)
    if isinstance(now, bool) or not isinstance(now, int):
        raise StateValidationError("now must be an integer timestamp")
    processed = {
        "attractors": _decay_attractors(conn, now, snapshot_id),
        "value_field_weights": _decay_value_weights(conn, now, snapshot_id),
        "sensitivity_profiles": _decay_sensitivity_profiles(conn, now, snapshot_id),
    }
    return {"processed": processed, "warnings": []}


def _decay_attractors(conn, now, snapshot_id):
    rows = conn.execute(
        "SELECT * FROM attractors WHERE snapshot_id = ? ORDER BY id", (snapshot_id,)
    ).fetchall()
    count = 0
    for row in rows:
        half_life = _parse_half_life(row["half_life"])
        if half_life is None:
            continue
        elapsed = _elapsed(row["last_activation_at"] or row["created_at"], now)
        if elapsed is None or elapsed <= 0:
            continue
        factor = _factor(elapsed, half_life)
        decay_state = loads(row["decay_state"], {})
        decay_state.update(
            {
                "decayed_from_table": "attractors",
                "decayed_from_id": row["id"],
                "original_target_path": row["target_path"],
                "decay_factor": factor,
                "decayed_at": now,
                "half_life": half_life,
            }
        )
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
                f"{row['target_path']}::decayed:{now}:{row['id']}",
                clamp(float(row["depth"]) * factor, 0.0, 1.0),
                clamp(1.0 - ((1.0 - float(row["activation_threshold"])) * factor), 0.0, 1.0),
                str(half_life),
                str(now),
                row["source_marks"],
                dumps(decay_state),
                snapshot_id,
                str(now),
                str(now),
            ),
        )
        count += 1
    return count


def _decay_value_weights(conn, now, snapshot_id):
    rows = conn.execute(
        "SELECT * FROM value_field_weights WHERE snapshot_id = ? ORDER BY id",
        (snapshot_id,),
    ).fetchall()
    count = 0
    for row in rows:
        decay_state = loads(row["decay_state"], {})
        half_life = _parse_half_life(decay_state.get("half_life"))
        if half_life is None:
            continue
        elapsed = _elapsed(row["updated_at"] or row["created_at"], now)
        if elapsed is None or elapsed <= 0:
            continue
        factor = _factor(elapsed, half_life)
        decay_state.update(
            {
                "decayed_from_table": "value_field_weights",
                "decayed_from_id": row["id"],
                "original_axis_name": row["axis_name"],
                "original_scope": row["scope"],
                "decay_factor": factor,
                "decayed_at": now,
                "half_life": half_life,
            }
        )
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
                row["axis_name"],
                f"{row['scope']}::decayed:{now}:{row['id']}",
                clamp(float(row["weight"]) * factor, -1.0, 1.0),
                row["source_marks"],
                dumps(decay_state),
                row["score_contribution_meta"],
                snapshot_id,
                str(now),
                str(now),
            ),
        )
        count += 1
    return count


def _decay_sensitivity_profiles(conn, now, snapshot_id):
    rows = conn.execute(
        "SELECT * FROM sensitivity_profiles WHERE snapshot_id = ? ORDER BY id",
        (snapshot_id,),
    ).fetchall()
    count = 0
    for row in rows:
        decay_state = loads(row["decay_state"], {})
        half_life = _parse_half_life(decay_state.get("half_life"))
        if half_life is None:
            continue
        elapsed = _elapsed(row["updated_at"] or row["created_at"], now)
        if elapsed is None or elapsed <= 0:
            continue
        factor = _factor(elapsed, half_life)
        decay_state.update(
            {
                "decayed_from_table": "sensitivity_profiles",
                "decayed_from_id": row["id"],
                "original_profile_id": row["profile_id"],
                "decay_factor": factor,
                "decayed_at": now,
                "half_life": half_life,
            }
        )
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"{row['profile_id']}::decayed:{now}:{row['id']}",
                row["trigger_pattern"],
                1.0 + ((float(row["gain"]) - 1.0) * factor),
                float(row["threshold"]) * factor,
                row["scope"],
                row["hard_policy"],
                row["false_positive_observations"],
                row["source_marks"],
                dumps(decay_state),
                snapshot_id,
                str(now),
                str(now),
            ),
        )
        count += 1
    return count


def _parse_half_life(value):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _elapsed(start_value, now):
    start = _parse_time(start_value)
    if start is None:
        return None
    return now - start


def _parse_time(value):
    if value is None:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        pass
    text = str(value)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return int(datetime.fromisoformat(text).timestamp())
    except ValueError:
        return None


def _factor(elapsed, half_life):
    return math.pow(0.5, float(elapsed) / float(half_life))
