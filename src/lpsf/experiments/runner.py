"""Experiment runner for M4 Phase 1.

run_query: one query through one baseline -> writes hypothesis_traces +
collapse_traces -> returns Response and trace ids.

run_experiment: orchestrates a full hypothesis scenario across multiple
baselines -> writes evaluation_runs row -> returns phase-by-phase results,
deltas, and pass/fail summary.

No network. All inputs are passed in.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from lpsf import db as db_mod
from lpsf.operators import apply_operator

from .baselines import Response, get_baseline
from .scoring import score_response


# ---------- ID helpers ----------------------------------------------------

def _next_trace_id(conn: sqlite3.Connection, table: str, prefix: str) -> str:
    value = conn.execute(
        f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}"
    ).fetchone()[0]
    return f"{prefix}_{int(value):06d}"


def _next_run_id(conn: sqlite3.Connection) -> str:
    return _next_trace_id(conn, "evaluation_runs", "run")


def _now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


# ---------- run_query ----------------------------------------------------

def run_query(
    conn: sqlite3.Connection,
    *,
    query: str,
    query_id: str,
    snapshot_id: str,
    baseline_name: str,
    llm: Any,
    rag: Optional[Any] = None,
    static_memory: Optional[Dict[str, str]] = None,
    seed: int = 0,
    expected_keywords: Sequence[str] = (),
    available_evidence_ids: Sequence[str] = (),
    active_attractor_paths: Sequence[str] = (),
    forbidden_patterns: Sequence[str] = (),
) -> Dict[str, Any]:
    """Run one query through one baseline; persist traces.

    Returns {response, hypothesis_trace_id, collapse_trace_id}.
    """
    baseline = get_baseline(baseline_name)
    response: Response = baseline.respond(
        conn,
        query=query,
        snapshot_id=snapshot_id,
        llm=llm,
        rag=rag,
        static_memory=static_memory,
        seed=seed,
    )

    # Score
    response.score_components = score_response(
        response,
        expected_keywords=expected_keywords,
        available_evidence_ids=available_evidence_ids,
        active_attractor_paths=active_attractor_paths,
        forbidden_patterns=forbidden_patterns,
    )

    # hypothesis_trace
    htrace_id = _next_trace_id(conn, "hypothesis_traces", "htrace")
    interference_matrix = {
        cand: {
            other: 0.0 if cand == other else _interference(
                response.amplitudes.get(cand, 0.0),
                response.amplitudes.get(other, 0.0),
            )
            for other in response.candidates
        }
        for cand in response.candidates
    }
    conn.execute(
        """
        INSERT INTO hypothesis_traces (
            trace_id, query_id, candidates, amplitudes, interference_matrix,
            selected_hypothesis, rejected_paths, score_components,
            snapshot_id, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            htrace_id,
            query_id,
            _dumps(response.candidates),
            _dumps(response.amplitudes),
            _dumps(interference_matrix),
            response.selected_path,
            _dumps(response.rejected_paths),
            _dumps(response.score_components),
            snapshot_id,
            _now(),
        ),
    )

    # collapse_trace
    ctrace_id = _next_trace_id(conn, "collapse_traces", "ctrace")
    conn.execute(
        """
        INSERT INTO collapse_traces (
            trace_id, query_id, selected_path, active_attractors, active_marks,
            evidence_refs, value_contributions, sensitivity_contributions,
            unresolved_tensions, suppressed_paths, warnings,
            snapshot_id, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ctrace_id,
            query_id,
            response.selected_path,
            _dumps(response.active_attractors),
            _dumps(response.active_marks),
            _dumps(response.evidence_refs),
            _dumps(response.value_contributions),
            _dumps(response.sensitivity_contributions),
            _dumps(response.unresolved_tensions),
            _dumps(response.suppressed_paths),
            _dumps(response.warnings),
            snapshot_id,
            _now(),
        ),
    )

    return {
        "response": response,
        "hypothesis_trace_id": htrace_id,
        "collapse_trace_id": ctrace_id,
    }


def _interference(a: float, b: float) -> float:
    """Toy interference: signed product / (1 + |a| + |b|)."""
    denom = 1.0 + abs(a) + abs(b)
    return round((a * b) / denom, 6)


# ---------- run_experiment -----------------------------------------------

def run_experiment(
    conn: sqlite3.Connection,
    *,
    hypothesis_name: str,
    scenario: Dict[str, Any],
    baselines: Sequence[str],
    snapshot_id: str,
    llm: Any,
    rag: Optional[Any] = None,
    static_memory: Optional[Dict[str, str]] = None,
    event_id: Optional[str] = None,
    seed: int = 0,
    verify: Optional[Any] = None,
) -> Dict[str, Any]:
    """Run a hypothesis scenario across the given baselines.

    Scenario schema:
    {
        "queries": [{"phase": "before"|"after"|str, "query": str, "query_id": str}, ...],
        "operations": [{"phase": str, "operator": str, "kwargs": {...}}, ...],
        "scoring": {
            "expected_keywords": [...],
            "available_evidence_ids": [...],
            "active_attractor_paths": [...],
            "forbidden_patterns": [...],
        },
    }

    The runner iterates phases in the order they appear in queries; before
    each query phase it applies any operations whose phase matches the
    preceding boundary. For simplicity, operations with phase == "setup" run
    first, phase "between" runs after the first batch of queries, and phase
    "post" runs after all queries.
    """
    operations = scenario.get("operations", [])
    queries = scenario.get("queries", [])
    scoring = scenario.get("scoring", {})

    # 1. setup operations
    _apply_phase_operations(
        conn, operations, "setup", snapshot_id=snapshot_id, event_id=event_id
    )

    # 2. group queries by phase, preserving order
    phase_order: List[str] = []
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for q in queries:
        phase = q.get("phase", "default")
        if phase not in grouped:
            grouped[phase] = []
            phase_order.append(phase)
        grouped[phase].append(q)

    phase_results: Dict[str, Dict[str, Response]] = {}
    phase_trace_ids: Dict[str, Dict[str, Dict[str, str]]] = {}
    all_prompts: List[str] = []
    all_outputs: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []

    for i, phase in enumerate(phase_order):
        # Apply "between" operations once before the second phase (i==1) for
        # legacy H1-style two-phase scenarios.
        if i == 1:
            _apply_phase_operations(
                conn,
                operations,
                "between",
                snapshot_id=snapshot_id,
                event_id=event_id,
            )
        # Also apply phase-specific operations tagged
        # "between_<prev>_and_<curr>" for multi-phase scenarios (e.g. H7).
        if i >= 1:
            phase_tag = f"between_{phase_order[i-1]}_and_{phase}"
            _apply_phase_operations(
                conn,
                operations,
                phase_tag,
                snapshot_id=snapshot_id,
                event_id=event_id,
            )

        phase_results[phase] = {}
        phase_trace_ids[phase] = {}
        for q in grouped[phase]:
            for baseline_name in baselines:
                outcome = run_query(
                    conn,
                    query=q["query"],
                    query_id=q["query_id"],
                    snapshot_id=snapshot_id,
                    baseline_name=baseline_name,
                    llm=llm,
                    rag=rag,
                    static_memory=static_memory,
                    seed=seed,
                    expected_keywords=scoring.get("expected_keywords", ()),
                    available_evidence_ids=scoring.get("available_evidence_ids", ()),
                    active_attractor_paths=scoring.get("active_attractor_paths", ()),
                    forbidden_patterns=scoring.get("forbidden_patterns", ()),
                )
                response: Response = outcome["response"]
                key = f"{baseline_name}::{q['query_id']}"
                phase_results[phase][baseline_name] = response
                phase_trace_ids[phase].setdefault(baseline_name, {})[
                    q["query_id"]
                ] = {
                    "hypothesis_trace_id": outcome["hypothesis_trace_id"],
                    "collapse_trace_id": outcome["collapse_trace_id"],
                }
                all_prompts.append(response.prompt)
                all_outputs.append(
                    {
                        "phase": phase,
                        "baseline": baseline_name,
                        "query_id": q["query_id"],
                        "selected_path": response.selected_path,
                        "evidence_refs": response.evidence_refs,
                        "score_components": response.score_components,
                        "warnings": response.warnings,
                        "model_version": response.model_version,
                    }
                )

    # 3. post operations
    _apply_phase_operations(
        conn, operations, "post", snapshot_id=snapshot_id, event_id=event_id
    )

    # 4. verify
    passed = True
    verify_details: Dict[str, Any] = {}
    if verify is not None:
        verify_outcome = verify(
            {
                "phase_results": phase_results,
                "phase_trace_ids": phase_trace_ids,
                "scenario": scenario,
            }
        )
        if isinstance(verify_outcome, tuple) and len(verify_outcome) == 2:
            passed, verify_failures = verify_outcome
            verify_details = {"failures": list(verify_failures)}
            if not passed:
                failures.extend(
                    {"source": "verify", "detail": f} for f in verify_failures
                )
        else:
            passed = bool(verify_outcome)
            verify_details = {"raw": verify_outcome}

    # 5. evaluation_runs row
    run_id = _next_run_id(conn)
    score_summary = _summarize_scores(phase_results)
    conn.execute(
        """
        INSERT INTO evaluation_runs (
            run_id, suite_name, candidate_name, baseline_name, snapshot_id,
            state_db_version, prompts, sanitized_outputs, score_summary,
            failures, report_refs, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            hypothesis_name,
            ",".join(baselines),
            ",".join(baselines),
            snapshot_id,
            db_mod.STATE_DB_VERSION,
            _dumps(all_prompts),
            _dumps(all_outputs),
            _dumps(score_summary),
            _dumps(failures),
            _dumps([]),
            _now(),
        ),
    )

    return {
        "run_id": run_id,
        "hypothesis_name": hypothesis_name,
        "phase_results": phase_results,
        "phase_trace_ids": phase_trace_ids,
        "score_summary": score_summary,
        "passed": passed,
        "failures": failures,
        "verify_details": verify_details,
    }


def _apply_phase_operations(
    conn: sqlite3.Connection,
    operations: Sequence[Dict[str, Any]],
    phase: str,
    *,
    snapshot_id: str,
    event_id: Optional[str],
) -> None:
    for op in operations:
        if op.get("phase") != phase:
            continue
        operator_type = op["operator"]
        kwargs = dict(op.get("kwargs", {}))
        kwargs.setdefault("snapshot_id", snapshot_id)
        if event_id is not None:
            kwargs.setdefault("event_id", event_id)
        apply_operator(operator_type, conn, **kwargs)


def _summarize_scores(
    phase_results: Dict[str, Dict[str, Response]]
) -> Dict[str, Any]:
    summary: Dict[str, Any] = {}
    for phase, by_baseline in phase_results.items():
        summary[phase] = {}
        for baseline_name, response in by_baseline.items():
            summary[phase][baseline_name] = dict(response.score_components)
    return summary
