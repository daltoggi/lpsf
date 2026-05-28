"""H4: snapshot reproducibility. The same scenario + same seed must yield
identical selected_path and evidence_refs across independent runs.

This is validated by run_h4_twice in the corresponding test: two fresh
in-memory DBs, identical fixtures, identical seed -> identical Response.

build_scenario emits a deterministic operator + query sequence used by both
runs.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def build_scenario(snapshot_id: str, event_id: str) -> Dict[str, Any]:
    return {
        "queries": [
            {
                "phase": "main",
                "query": "memory question for replay",
                "query_id": "h4_q_main",
            },
        ],
        "operations": [
            {
                "phase": "setup",
                "operator": "deepen_attractor",
                "kwargs": {
                    "target_type": "path",
                    "target_id": "path:ev:M1",
                    "strength": 0.4,
                    "half_life": 3600,
                    "evidence_refs": ["ev:M1"],
                    "reason": "H4 deterministic deepen",
                    "scope": "h4",
                },
            },
            {
                "phase": "setup",
                "operator": "tilt_value_field",
                "kwargs": {
                    "axis_name": "axis:recency",
                    "strength": 0.2,
                    "half_life": 3600,
                    "evidence_refs": ["ev:M1"],
                    "reason": "H4 axis tilt",
                    "scope": "h4",
                },
            },
        ],
        "scoring": {
            "expected_keywords": ["memory"],
            "available_evidence_ids": ["ev:M1", "ev:M2"],
            "active_attractor_paths": ["path:ev:M1"],
            "forbidden_patterns": [],
        },
    }


def verify(result: Dict[str, Any]) -> Tuple[bool, List[str]]:
    # Reproducibility is asserted across two independent run() calls in the
    # test. This single-run verifier just confirms the runner produced output.
    failures: List[str] = []
    if not result.get("phase_results"):
        failures.append("H4 missing phase_results")
    return (len(failures) == 0), failures
