from lpsf.operators import reconsolidate_memory

from tests.operators.conftest import fetch_mark


def test_reconsolidate_memory_preserves_old_target_meaning_with_record(
    conn, event_id, snapshot_id, evidence_refs
):
    result = reconsolidate_memory(
        conn,
        event_id=event_id,
        snapshot_id=snapshot_id,
        old_target_id="memory:rag-as-memory",
        new_target_id="memory:rag-as-evidence-layer",
        preservation_note="original source remains unchanged",
        strength=0.5,
        half_life=3600,
        evidence_refs=evidence_refs,
        reason="schema-aware reinterpretation",
    )

    record = conn.execute("SELECT * FROM reconsolidation_records").fetchone()
    assert record["old_target_id"] == "memory:rag-as-memory"
    assert record["new_target_id"] == "memory:rag-as-evidence-layer"
    assert record["preservation_note"] == "original source remains unchanged"

    mark = fetch_mark(conn, result["mark_id"])
    assert mark["operator_type"] == "reconsolidate_memory"
    assert mark["target_id"] == "memory:rag-as-memory->memory:rag-as-evidence-layer"
