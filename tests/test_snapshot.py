import sqlite3

import pytest

from lpsf import snapshot
from lpsf.adapter import NullAdapter


class SyntheticAdapter(NullAdapter):
    def __init__(self, count):
        self.count = count

    def version(self):
        return "synthetic-1"

    def allowed_scope(self):
        return ["core", "source"]

    def snapshot_metadata(self):
        return {
            "index_metadata": {"schema": "synthetic"},
            "source_counts": {"synthetic": self.count},
            "retrieval_parameters": {"limit": 20},
        }


def test_pin_snapshot_is_stable_and_round_trips(conn):
    adapter = SyntheticAdapter(count=3)
    snapshot_id = snapshot.pin_snapshot(conn, adapter)
    assert snapshot_id == snapshot.pin_snapshot(conn, adapter)

    row_count = conn.execute("SELECT COUNT(*) FROM evidence_snapshots").fetchone()[0]
    assert row_count == 1

    restored = snapshot.get_snapshot(conn, snapshot_id)
    assert restored["snapshot_id"] == snapshot_id
    assert restored["adapter_version"] == "synthetic-1"
    assert restored["allowed_scope"] == ["core", "source"]
    assert restored["source_counts"] == {"synthetic": 3}


def test_record_drift_appends_without_mutating_snapshot_identity(conn):
    snapshot_id = snapshot.pin_snapshot(conn, SyntheticAdapter(count=3))

    snapshot.record_drift(conn, snapshot_id, {"source_counts": {"synthetic": 4}})
    snapshot.record_drift(conn, snapshot_id, {"source_counts": {"synthetic": 5}})

    restored = snapshot.get_snapshot(conn, snapshot_id)
    assert restored["drift_observations"] == [
        {"source_counts": {"synthetic": 4}},
        {"source_counts": {"synthetic": 5}},
    ]
    assert restored["snapshot_id"] == snapshot_id


def test_snapshot_trigger_blocks_direct_metadata_mutation(conn):
    snapshot_id = snapshot.pin_snapshot(conn, SyntheticAdapter(count=3))
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "UPDATE evidence_snapshots SET adapter_version='mutated' WHERE snapshot_id=?",
            (snapshot_id,),
        )
