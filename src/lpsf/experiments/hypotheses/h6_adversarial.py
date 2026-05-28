"""H6: adversarial attractor — LPSF overrides the best RAG candidate.

Setup:
  RAG fixture has two candidates:
    - ev:correct  (score 0.90) — clearly the best by RAG evidence alone
    - ev:wrong    (score 0.20) — weak RAG support

  Before the query, LPSF deepens path:ev:wrong with strength=0.8, pushing
  its total amplitude to 0.20 + 0.80 = 1.00, above ev:correct's 0.90.

Expected outcomes:
  - LLMPlusLPSF selects path:ev:wrong  (adversarial attractor wins)
  - LLMPlusRAG   selects path:ev:correct (pure RAG, no plasticity)
  - LLMOnly      selects path:llm:...   (no evidence at all)

Why this matters:
  If LLMPlusLPSF consistently picks the wrong path while LLMPlusRAG
  consistently picks the correct one, LPSF demonstrably controls path
  selection independently of RAG quality. This directly refutes the
  "self-referential scoring" concern: the baselines diverge in a
  controlled, falsifiable way.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def build_rag_fixture() -> Dict[str, List[Dict[str, Any]]]:
    """Adversarial fixture: ev:correct has high RAG score, ev:wrong has low score."""
    return {
        "knowledge query": [
            {
                "id": "ev:correct",
                "score": 0.90,
                "sanitized_summary": "well-supported answer backed by strong evidence",
                "source_type": "synthetic",
            },
            {
                "id": "ev:wrong",
                "score": 0.20,
                "sanitized_summary": "weak fringe interpretation with limited support",
                "source_type": "synthetic",
            },
        ],
    }


def build_scenario(snapshot_id: str, event_id: str) -> Dict[str, Any]:
    return {
        "queries": [
            {
                "phase": "main",
                "query": "knowledge query",
                "query_id": "h6_q_main",
            },
        ],
        "operations": [
            {
                "phase": "setup",
                "operator": "deepen_attractor",
                "kwargs": {
                    "target_type": "path",
                    "target_id": "path:ev:wrong",
                    "strength": 0.8,
                    "half_life": 3600,
                    "evidence_refs": ["ev:wrong"],
                    "reason": "H6 adversarial: deliberately deepen the weaker candidate",
                    "scope": "h6",
                },
            },
        ],
        "scoring": {
            "expected_keywords": ["knowledge"],
            "available_evidence_ids": ["ev:correct", "ev:wrong"],
            "active_attractor_paths": ["path:ev:wrong"],
            "forbidden_patterns": [],
        },
        "_rag_fixture": build_rag_fixture(),
    }


def verify(result: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Pass conditions:
      1. LLMPlusLPSF selected path:ev:wrong  (attractor overrode RAG)
      2. LLMPlusRAG   selected path:ev:correct (pure RAG, no attractor effect)
      3. The two baselines diverge            (LPSF has real, independent influence)
    """
    failures: List[str] = []
    phase_results = result.get("phase_results", {})
    main = phase_results.get("main", {})

    lpsf_resp = main.get("LLMPlusLPSF")
    rag_resp = main.get("LLMPlusRAG")

    if lpsf_resp is None:
        failures.append("H6 missing LLMPlusLPSF result")
        return False, failures
    if rag_resp is None:
        failures.append("H6 missing LLMPlusRAG result")
        return False, failures

    # 1. LPSF must follow the adversarial attractor
    if lpsf_resp.selected_path != "path:ev:wrong":
        failures.append(
            f"H6 expected LLMPlusLPSF=path:ev:wrong, got {lpsf_resp.selected_path} "
            f"(LPSF attractor did not override RAG)"
        )

    # 2. RAG baseline must NOT follow the attractor
    if rag_resp.selected_path != "path:ev:correct":
        failures.append(
            f"H6 expected LLMPlusRAG=path:ev:correct, got {rag_resp.selected_path} "
            f"(RAG baseline should ignore LPSF state)"
        )

    # 3. The two baselines must diverge
    if lpsf_resp.selected_path == rag_resp.selected_path:
        failures.append(
            "H6 baselines did not diverge — LPSF had no measurable effect"
        )

    return (len(failures) == 0), failures
