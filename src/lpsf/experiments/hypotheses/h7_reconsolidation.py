"""H7: reconsolidation — a deepened bias can be reversed by counter-experience.

This validates that the "plasticity" in "Landscape-Plastic Semantic Field"
has substance. Without this, LPSF would only show monotonic bias injection
(stacking deepens), which is "strong bias injector" not "plasticity".

Scenario (3 phases, same query "tied query"):
  Phase initial:  deepen path:ev:B with strength 0.6
                  → LPSF should select path:ev:B (bias took hold).
  Phase reversed: weaken path:ev:B with strength 0.6 (cancels initial deepen)
                  → LPSF should now select path:ev:A (bias reversed).
  Phase overridden: deepen path:ev:A with strength 0.8 (competing attractor)
                  → LPSF should select path:ev:A by stronger competing attractor.

We use a TIED retrieval fixture (ev:A score = ev:B score = 0.50) so that
the attractor differential is the only thing determining selection.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def build_rag_fixture() -> Dict[str, List[Dict[str, Any]]]:
    """Tied-score fixture so the attractor is the sole tiebreaker."""
    return {
        "tied query": [
            {
                "id": "ev:A",
                "score": 0.50,
                "sanitized_summary": "candidate A (counter-evidence target)",
                "source_type": "synthetic",
            },
            {
                "id": "ev:B",
                "score": 0.50,
                "sanitized_summary": "candidate B (initial bias target)",
                "source_type": "synthetic",
            },
        ],
    }


def build_scenario(snapshot_id: str, event_id: str) -> Dict[str, Any]:
    return {
        "queries": [
            {"phase": "initial", "query": "tied query", "query_id": "h7_q_initial"},
            {"phase": "reversed", "query": "tied query", "query_id": "h7_q_reversed"},
            {"phase": "overridden", "query": "tied query", "query_id": "h7_q_overridden"},
        ],
        "operations": [
            # Phase 1: deepen ev:B (induce bias toward B)
            {
                "phase": "setup",
                "operator": "deepen_attractor",
                "kwargs": {
                    "target_type": "path",
                    "target_id": "path:ev:B",
                    "strength": 0.6,
                    "half_life": 3600,
                    "evidence_refs": ["ev:B"],
                    "reason": "H7 initial bias",
                    "scope": "h7",
                },
            },
            # Phase 2: weaken ev:B (cancel the initial bias)
            {
                "phase": "between_initial_and_reversed",
                "operator": "weaken_attractor",
                "kwargs": {
                    "target_type": "path",
                    "target_id": "path:ev:B",
                    "strength": 0.6,
                    "half_life": 3600,
                    "evidence_refs": ["ev:B"],
                    "reason": "H7 counter-experience: weaken the bias",
                    "scope": "h7",
                },
            },
            # Phase 3: deepen ev:A (competing attractor — overrides any leftover bias)
            {
                "phase": "between_reversed_and_overridden",
                "operator": "deepen_attractor",
                "kwargs": {
                    "target_type": "path",
                    "target_id": "path:ev:A",
                    "strength": 0.8,
                    "half_life": 3600,
                    "evidence_refs": ["ev:A"],
                    "reason": "H7 competing attractor on A",
                    "scope": "h7",
                },
            },
        ],
        "scoring": {
            "expected_keywords": ["tied"],
            "available_evidence_ids": ["ev:A", "ev:B"],
            "active_attractor_paths": ["path:ev:B", "path:ev:A"],
            "forbidden_patterns": [],
        },
        "_rag_fixture": build_rag_fixture(),
    }


def verify(result: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Pass conditions:
      1. initial   → LLMPlusLPSF selects path:ev:B   (bias took hold)
      2. reversed  → LLMPlusLPSF does NOT select B   (bias was reversed by weaken)
      3. overridden→ LLMPlusLPSF selects path:ev:A   (competing attractor wins)
      4. The selected_path changed at least once across the three phases.
    """
    failures: List[str] = []
    phase_results = result.get("phase_results", {})

    initial = phase_results.get("initial", {}).get("LLMPlusLPSF")
    reversed_ = phase_results.get("reversed", {}).get("LLMPlusLPSF")
    overridden = phase_results.get("overridden", {}).get("LLMPlusLPSF")

    if initial is None:
        failures.append("H7 missing 'initial' LLMPlusLPSF result")
    if reversed_ is None:
        failures.append("H7 missing 'reversed' LLMPlusLPSF result")
    if overridden is None:
        failures.append("H7 missing 'overridden' LLMPlusLPSF result")
    if failures:
        return False, failures

    # 1. initial bias took
    if initial.selected_path != "path:ev:B":
        failures.append(
            f"H7 initial: expected path:ev:B (bias took), got {initial.selected_path}"
        )

    # 2. reversed should NOT be B (the weaken cancelled the deepen)
    if reversed_.selected_path == "path:ev:B":
        failures.append(
            f"H7 reversed: still selecting path:ev:B; weaken did not reverse the bias"
        )

    # 3. overridden should be A (competing attractor on A wins)
    if overridden.selected_path != "path:ev:A":
        failures.append(
            f"H7 overridden: expected path:ev:A (competing attractor), "
            f"got {overridden.selected_path}"
        )

    # 4. plasticity sanity: selected_path must have changed somewhere
    paths = {initial.selected_path, reversed_.selected_path, overridden.selected_path}
    if len(paths) < 2:
        failures.append(
            f"H7 plasticity check: selected_path identical across all phases ({paths}); "
            "system shows no reversal"
        )

    return (len(failures) == 0), failures
