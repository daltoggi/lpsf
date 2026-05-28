"""Snapshot pinning and drift recording helpers."""

import hashlib
import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, Optional

from .adapter import EvidenceAdapter
from .errors import AdapterError, SnapshotError


def pin_snapshot(conn: sqlite3.Connection, adapter: EvidenceAdapter) -> str:
    payload = _snapshot_payload(adapter)
    snapshot_id = _snapshot_id(payload)
    now = _utc_timestamp()
    conn.execute(
        """
        INSERT OR IGNORE INTO evidence_snapshots (
            snapshot_id,
            adapter_version,
            allowed_scope,
            source_counts,
            index_metadata,
            retrieval_parameters,
            drift_observations,
            created_at,
            pinned_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            snapshot_id,
            payload["adapter_version"],
            _dumps(payload["allowed_scope"]),
            _dumps(payload["source_counts"]),
            _dumps(payload["index_metadata"]),
            _dumps(payload["retrieval_parameters"]),
            "[]",
            now,
            now,
        ),
    )
    return snapshot_id


def get_snapshot(conn: sqlite3.Connection, snapshot_id: str) -> Optional[Dict[str, Any]]:
    row = conn.execute(
        "SELECT * FROM evidence_snapshots WHERE snapshot_id = ?", (snapshot_id,)
    ).fetchone()
    if row is None:
        return None
    result = dict(row)
    for key in (
        "allowed_scope",
        "source_counts",
        "index_metadata",
        "retrieval_parameters",
        "drift_observations",
    ):
        if result[key] is not None:
            result[key] = json.loads(result[key])
    return result


def record_drift(
    conn: sqlite3.Connection, snapshot_id: str, drift_observation: Dict[str, Any]
) -> None:
    if not isinstance(drift_observation, dict):
        raise SnapshotError("Drift observation must be a dictionary")
    snapshot = get_snapshot(conn, snapshot_id)
    if snapshot is None:
        raise SnapshotError(f"Unknown snapshot: {snapshot_id}")
    observations = snapshot.get("drift_observations") or []
    observations.append(drift_observation)
    try:
        conn.execute(
            "UPDATE evidence_snapshots SET drift_observations = ? WHERE snapshot_id = ?",
            (_dumps(observations), snapshot_id),
        )
    except sqlite3.IntegrityError as exc:
        raise SnapshotError(str(exc)) from exc


def _snapshot_payload(adapter: EvidenceAdapter) -> Dict[str, Any]:
    metadata = adapter.snapshot_metadata() or {}
    if not isinstance(metadata, dict):
        raise AdapterError("snapshot_metadata() must return a dictionary")
    return {
        "adapter_version": adapter.version(),
        "allowed_scope": list(adapter.allowed_scope()),
        "source_counts": metadata.get("source_counts", {}),
        "index_metadata": metadata.get("index_metadata", {}),
        "retrieval_parameters": metadata.get("retrieval_parameters", {}),
    }


def _snapshot_id(payload: Dict[str, Any]) -> str:
    digest = hashlib.sha256(_dumps(payload).encode("utf-8")).hexdigest()[:24]
    return f"snap_{digest}"


def _dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _utc_timestamp() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
