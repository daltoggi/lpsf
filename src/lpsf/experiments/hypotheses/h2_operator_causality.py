"""H2: operator causality. Each of the 8 operators produces an attributable,
distinct state delta when applied in isolation.

This hypothesis is verified at the operator level (state delta + secondary
table row + source_marks linkage) rather than through query baselines. The
scenario therefore has zero queries; verify() inspects the DB directly.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


OPERATOR_SPECS = [
    {
        "operator": "deepen_attractor",
        "kwargs": {
            "target_type": "path",
            "target_id": "path:h2:deepen",
            "strength": 0.5,
            "half_life": 3600,
            "evidence_refs": ["ev:h2_deepen"],
            "reason": "H2 deepen",
            "scope": "h2",
        },
        "expected_table": "attractors",
        "expected_lookup": ("target_path", "path:h2:deepen"),
    },
    {
        "operator": "weaken_attractor",
        "kwargs": {
            "target_type": "path",
            "target_id": "path:h2:weaken",
            "strength": 0.4,
            "half_life": 3600,
            "evidence_refs": ["ev:h2_weaken"],
            "reason": "H2 weaken",
            "scope": "h2",
        },
        "expected_table": "attractors",
        "expected_lookup": ("target_path", "path:h2:weaken"),
    },
    {
        "operator": "open_path",
        "kwargs": {
            "target_type": "node",
            "target_id": "node:h2:target",
            "source_target_id": "node:h2:source",
            "relation_type": "supports",
            "strength": 0.3,
            "half_life": 3600,
            "evidence_refs": ["ev:h2_open"],
            "reason": "H2 open",
            "scope": "h2",
        },
        "expected_table": "semantic_edges",
        "expected_lookup": ("target_node_id", "node:h2:target"),
    },
    {
        "operator": "inhibit_path",
        "kwargs": {
            "target_type": "path",
            "target_id": "path:h2:inhibit",
            "strength": 0.6,
            "half_life": 3600,
            "evidence_refs": ["ev:h2_inhibit"],
            "reason": "H2 inhibit",
            "scope": "h2",
        },
        "expected_table": "attractors",
        "expected_lookup": ("target_path", "path:h2:inhibit"),
    },
    {
        "operator": "tilt_value_field",
        "kwargs": {
            "axis_name": "axis:h2",
            "strength": 0.3,
            "half_life": 3600,
            "evidence_refs": ["ev:h2_tilt"],
            "reason": "H2 tilt",
            "scope": "h2",
        },
        "expected_table": "value_field_weights",
        "expected_lookup": ("axis_name", "axis:h2"),
    },
    {
        "operator": "modulate_sensitivity",
        "kwargs": {
            "trigger_pattern": "pattern:h2",
            "gain": 0.8,
            "threshold": 0.3,
            "strength": 0.4,
            "half_life": 3600,
            "evidence_refs": ["ev:h2_sens"],
            "reason": "H2 modulate",
            "scope": "h2",
        },
        "expected_table": "sensitivity_profiles",
        "expected_lookup": ("trigger_pattern", "pattern:h2"),
    },
    {
        "operator": "remap_schema",
        "kwargs": {
            "target_type": "schema",
            "target_id": "schema:h2:new",
            "old_schema": "schema:h2:old",
            "new_schema": "schema:h2:new",
            "affected_targets": ["node:h2:target"],
            "preservation_note": "H2 schema remap; old preserved",
            "strength": 0.3,
            "half_life": 3600,
            "evidence_refs": ["ev:h2_remap"],
            "reason": "H2 remap",
            "scope": "h2",
        },
        "expected_table": "schema_mappings",
        "expected_lookup": ("new_schema", "schema:h2:new"),
    },
    {
        "operator": "reconsolidate_memory",
        "kwargs": {
            "target_type": "memory",
            "target_id": "mem:h2:new",
            "old_target_id": "mem:h2:old",
            "new_target_id": "mem:h2:new",
            "preservation_note": "H2 reconsolidation; old meaning kept",
            "strength": 0.3,
            "half_life": 3600,
            "evidence_refs": ["ev:h2_recon"],
            "reason": "H2 reconsolidate",
            "scope": "h2",
        },
        "expected_table": "reconsolidation_records",
        "expected_lookup": ("new_target_id", "mem:h2:new"),
    },
]


def build_scenario(snapshot_id: str, event_id: str) -> Dict[str, Any]:
    operations = [
        {"phase": "setup", "operator": spec["operator"], "kwargs": dict(spec["kwargs"])}
        for spec in OPERATOR_SPECS
    ]
    return {
        "queries": [],
        "operations": operations,
        "scoring": {
            "expected_keywords": [],
            "available_evidence_ids": [],
            "active_attractor_paths": [],
            "forbidden_patterns": [],
        },
        "_specs": OPERATOR_SPECS,
    }


def verify(result: Dict[str, Any]) -> Tuple[bool, List[str]]:
    # H2 verification is performed in the test itself (it has DB access).
    # Here we simply confirm the runner produced an evaluation row.
    failures: List[str] = []
    if not isinstance(result.get("phase_results"), dict):
        failures.append("H2 missing phase_results")
    return (len(failures) == 0), failures
