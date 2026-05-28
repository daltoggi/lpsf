"""H1: before/after behavior shift via plasticity marks.

Setup: a query with two candidate paths (A, B). Baseline (LLMPlusLPSF) initially
selects A because A has higher base RAG score. Between the two query phases,
apply deepen_attractor on path:ev:B with strength=0.7. After: LLMPlusLPSF must
select path:ev:B. LLMOnly must NOT change (no plasticity).
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def build_scenario(snapshot_id: str, event_id: str) -> Dict[str, Any]:
    return {
        "queries": [
            {"phase": "before", "query": "best path?", "query_id": "h1_q_before"},
            {"phase": "after", "query": "best path?", "query_id": "h1_q_after"},
        ],
        "operations": [
            {
                "phase": "between",
                "operator": "deepen_attractor",
                "kwargs": {
                    "target_type": "path",
                    "target_id": "path:ev:B",
                    "strength": 0.7,
                    "half_life": 3600,
                    "evidence_refs": ["ev:B"],
                    "reason": "H1 between-phase deepen of B",
                    "scope": "global",
                },
            },
        ],
        "scoring": {
            "expected_keywords": ["path"],
            "available_evidence_ids": ["ev:A", "ev:B"],
            "active_attractor_paths": ["path:ev:B"],
            "forbidden_patterns": [],
        },
    }


def verify(result: Dict[str, Any]) -> Tuple[bool, List[str]]:
    failures: List[str] = []
    phase_results = result["phase_results"]

    lpsf_before = phase_results.get("before", {}).get("LLMPlusLPSF")
    lpsf_after = phase_results.get("after", {}).get("LLMPlusLPSF")
    if lpsf_before is None or lpsf_after is None:
        failures.append("H1 requires LLMPlusLPSF results in both phases")
        return False, failures

    # LPSF should shift to path:ev:B after the deepen
    if lpsf_after.selected_path != "path:ev:B":
        failures.append(
            f"LPSF after should be path:ev:B, got {lpsf_after.selected_path}"
        )
    # LPSF before should NOT already be path:ev:B (else the test is vacuous)
    if lpsf_before.selected_path == lpsf_after.selected_path:
        failures.append(
            "LPSF selected_path did not shift between before and after"
        )
    # collapse_trace must list at least one active mark after
    if not lpsf_after.active_marks:
        failures.append("LPSF after has no active_marks recorded")

    # LLMOnly (if present) should NOT change
    llm_before = phase_results.get("before", {}).get("LLMOnly")
    llm_after = phase_results.get("after", {}).get("LLMOnly")
    if llm_before is not None and llm_after is not None:
        if llm_before.selected_path != llm_after.selected_path:
            failures.append(
                "LLMOnly selected_path changed despite no plasticity"
            )

    return (len(failures) == 0), failures
