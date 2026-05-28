from lpsf.operators import remap_schema

from tests.operators.conftest import fetch_mark, json_field


def test_remap_schema_records_old_new_mapping_without_editing_canon_rows(
    conn, event_id, snapshot_id, evidence_refs
):
    result = remap_schema(
        conn,
        event_id=event_id,
        snapshot_id=snapshot_id,
        old_schema="memory=stored-text",
        new_schema="memory=landscape-deformation",
        affected_targets=["path:memory"],
        preservation_note="old wording preserved as historical schema",
        strength=0.6,
        half_life=3600,
        evidence_refs=evidence_refs,
        reason="better operational frame",
    )

    mapping = conn.execute("SELECT * FROM schema_mappings").fetchone()
    assert mapping["old_schema"] == "memory=stored-text"
    assert mapping["new_schema"] == "memory=landscape-deformation"
    assert json_field(dict(mapping), "affected_targets") == ["path:memory"]
    assert mapping["preservation_note"] == "old wording preserved as historical schema"
    assert conn.execute("SELECT COUNT(*) FROM semantic_nodes").fetchone()[0] == 0

    mark = fetch_mark(conn, result["mark_id"])
    assert mark["operator_type"] == "remap_schema"
    assert mark["target_id"] == "memory=stored-text->memory=landscape-deformation"
