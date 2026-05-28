"""H5: tension register. Conflicting plasticity marks on the same target must
surface as unresolved_tensions in the collapse_trace, with a priority warning.

Setup:
- deepen_attractor on path:ev:A (strength 0.6) and inhibit_path on same target
  (strength 0.5) are both applied in the setup phase.
- A query is then run.
- LLMPlusLPSF must register the tension and emit a priority guard warning.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def build_scenario(snapshot_id: str, event_id: str) -> Dict[str, Any]:
    return {
        "queries": [
            {
                "phase": "main",
                "query": "controversial topic best path?",
                "query_id": "h5_q_main",
            },
        ],
        "operations": [
            {
                "phase": "setup",
                "operator": "deepen_attractor",
                "kwargs": {
                    "target_type": "path",
                    "target_id": "path:ev:X",
                    "strength": 0.6,
                    "half_life": 3600,
                    "evidence_refs": ["ev:X"],
                    "reason": "H5 deepen X",
                    "scope": "global",
                },
            },
            {
                "phase": "setup",
                "operator": "inhibit_path",
                "kwargs": {
                    "target_type": "path",
                    "target_id": "path:ev:X",
                    "strength": 0.5,
                    "half_life": 3600,
                    "evidence_refs": ["ev:X"],
                    "reason": "H5 inhibit X (creates tension)",
                    "scope": "global",
                },
            },
        ],
        "scoring": {
            "expected_keywords": ["topic"],
            "available_evidence_ids": ["ev:X"],
            "active_attractor_paths": ["path:ev:X"],
            "forbidden_patterns": [],
        },
    }


def verify(result: Dict[str, Any]) -> Tuple[bool, List[str]]:
    failures: List[str] = []
    lpsf = result.get("phase_results", {}).get("main", {}).get("LLMPlusLPSF")
    if lpsf is None:
        failures.append("H5 requires LLMPlusLPSF in 'main' phase")
        return False, failures

    if not lpsf.unresolved_tensions:
        failures.append("H5 expected unresolved_tensions on candidate")
    else:
        tension = lpsf.unresolved_tensions[0]
        if not tension.get("supporting_marks"):
            failures.append("H5 tension missing supporting_marks")
        if not tension.get("inhibiting_marks"):
            failures.append("H5 tension missing inhibiting_marks")

    if not any("priority guard" in w for w in lpsf.warnings):
        failures.append("H5 expected priority guard warning")

    return (len(failures) == 0), failures
