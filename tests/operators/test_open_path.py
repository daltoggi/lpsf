from lpsf.operators import open_path

from tests.operators.conftest import fetch_mark, json_field


def test_open_path_creates_typed_semantic_edge_and_mark(
    conn, event_id, snapshot_id, evidence_refs
):
    result = open_path(
        conn,
        event_id=event_id,
        snapshot_id=snapshot_id,
        target_type="edge",
        target_id="node:lpsf",
        source_target_id="node:second-brain",
        relation_type="supports",
        strength=0.45,
        half_life=3600,
        evidence_refs=evidence_refs,
        reason="synthetic bridge",
    )

    edge = conn.execute(
        """
        SELECT * FROM semantic_edges
        WHERE source_node_id = 'node:second-brain' AND target_node_id = 'node:lpsf'
        """
    ).fetchone()
    assert edge is not None
    assert edge["relation_type"] == "supports"
    assert edge["weight"] == 0.45
    assert json_field(dict(edge), "evidence_refs") == evidence_refs

    assert conn.execute(
        "SELECT COUNT(*) FROM semantic_nodes WHERE node_id IN ('node:second-brain', 'node:lpsf')"
    ).fetchone()[0] == 2
    mark = fetch_mark(conn, result["mark_id"])
    assert mark["operator_type"] == "open_path"
    assert mark["target_id"] == "node:second-brain->node:lpsf"
