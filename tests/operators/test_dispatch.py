import importlib
import sys

import pytest

from lpsf.operators import (
    OperatorError,
    PolicyViolation,
    UnknownOperator,
    apply_operator,
)


def _base_kwargs(event_id, snapshot_id, evidence_refs):
    return {
        "event_id": event_id,
        "snapshot_id": snapshot_id,
        "strength": 0.25,
        "half_life": 3600,
        "evidence_refs": evidence_refs,
        "reason": "synthetic reason",
    }


def _operator_cases(event_id, snapshot_id, evidence_refs):
    base = _base_kwargs(event_id, snapshot_id, evidence_refs)
    return {
        "deepen_attractor": {
            **base,
            "target_type": "path",
            "target_id": "path:deep",
        },
        "weaken_attractor": {
            **base,
            "target_type": "path",
            "target_id": "path:weak",
        },
        "open_path": {
            **base,
            "target_type": "edge",
            "target_id": "node:target",
            "source_target_id": "node:source",
            "relation_type": "supports",
        },
        "inhibit_path": {
            **base,
            "target_type": "path",
            "target_id": "path:inhibit",
        },
        "tilt_value_field": {**base, "axis_name": "interpretability"},
        "modulate_sensitivity": {
            **base,
            "trigger_pattern": "synthetic trigger",
            "gain": 1.2,
            "threshold": 0.4,
        },
        "remap_schema": {
            **base,
            "old_schema": "old",
            "new_schema": "new",
            "affected_targets": ["path:x"],
            "preservation_note": "preserved",
        },
        "reconsolidate_memory": {
            **base,
            "old_target_id": "old:memory",
            "new_target_id": "new:memory",
            "preservation_note": "preserved",
        },
    }


def test_apply_operator_routes_and_returns_uniform_shape(conn, event_id, snapshot_id, evidence_refs):
    result = apply_operator(
        "deepen_attractor",
        conn,
        **_operator_cases(event_id, snapshot_id, evidence_refs)["deepen_attractor"],
    )
    assert set(result) == {"mark_id", "state_delta", "warnings"}
    assert result["mark_id"].startswith("mark_")


def test_apply_operator_rejects_unknown_operator(conn, event_id, snapshot_id, evidence_refs):
    with pytest.raises(UnknownOperator):
        apply_operator(
            "unknown_operator",
            conn,
            **_base_kwargs(event_id, snapshot_id, evidence_refs),
        )


def test_dispatcher_surfaces_priority_warnings(conn, event_id, snapshot_id, evidence_refs):
    inhibit_kwargs = _operator_cases(event_id, snapshot_id, evidence_refs)["inhibit_path"]
    apply_operator("inhibit_path", conn, **inhibit_kwargs)

    deepen_kwargs = {
        **_operator_cases(event_id, snapshot_id, evidence_refs)["deepen_attractor"],
        "target_id": inhibit_kwargs["target_id"],
    }
    result = apply_operator("deepen_attractor", conn, **deepen_kwargs)
    assert result["warnings"]
    assert result["state_delta"]["blocked_by_priority"] is True


@pytest.mark.parametrize("operator_name", sorted([
    "deepen_attractor",
    "weaken_attractor",
    "open_path",
    "inhibit_path",
    "tilt_value_field",
    "modulate_sensitivity",
    "remap_schema",
    "reconsolidate_memory",
]))
def test_all_operators_reject_empty_evidence_refs(
    conn, event_id, snapshot_id, operator_name
):
    kwargs = _operator_cases(event_id, snapshot_id, ["ev:fixture"])[operator_name]
    kwargs["evidence_refs"] = []
    with pytest.raises(PolicyViolation):
        apply_operator(operator_name, conn, **kwargs)


@pytest.mark.parametrize("operator_name", sorted([
    "deepen_attractor",
    "weaken_attractor",
    "open_path",
    "inhibit_path",
    "tilt_value_field",
    "modulate_sensitivity",
    "remap_schema",
    "reconsolidate_memory",
]))
def test_all_operators_reject_missing_event(
    conn, snapshot_id, evidence_refs, operator_name
):
    kwargs = _operator_cases("missing_event", snapshot_id, evidence_refs)[operator_name]
    with pytest.raises(OperatorError):
        apply_operator(operator_name, conn, **kwargs)


@pytest.mark.parametrize("operator_name", sorted([
    "deepen_attractor",
    "weaken_attractor",
    "open_path",
    "inhibit_path",
    "tilt_value_field",
    "modulate_sensitivity",
    "remap_schema",
    "reconsolidate_memory",
]))
def test_all_operators_reject_permanent_marks_in_v0_1(
    conn, event_id, snapshot_id, evidence_refs, operator_name
):
    kwargs = _operator_cases(event_id, snapshot_id, evidence_refs)[operator_name]
    kwargs["half_life"] = None
    kwargs["permanent"] = True
    with pytest.raises(PolicyViolation):
        apply_operator(operator_name, conn, **kwargs)


def test_operator_import_has_no_catalog_engine_side_effect():
    sys.modules.pop("catalog_engine", None)
    importlib.import_module("lpsf.operators")
    assert "catalog_engine" not in sys.modules
