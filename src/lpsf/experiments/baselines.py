"""Four baselines for M4 Phase 1 experiments.

All baselines accept the same input (conn, query, snapshot_id, llm, ...) and
return a Response dataclass. The baselines differ only in which inputs they
consult:

- LLMOnly:            MockLLM only.
- LLMPlusRAG:         MockLLM + MockRAG.
- LLMPlusStaticMemory: MockLLM + a frozen dict-shaped memory.
- LLMPlusLPSF:        MockLLM + MockRAG + LPSF state DB (attractors, marks,
                      value_field_weights, sensitivity_profiles).

No network. No real LLM. No external evidence stores. No personal-data paths.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Response:
    """Uniform response shape for every baseline."""

    selected_path: str
    evidence_refs: List[str]
    active_attractors: List[str]
    active_marks: List[str]
    value_contributions: Dict[str, float]
    sensitivity_contributions: Dict[str, float]
    unresolved_tensions: List[Dict[str, Any]]
    suppressed_paths: List[str]
    warnings: List[str]
    score_components: Dict[str, float]
    baseline_name: str
    model_version: str
    candidates: List[str] = field(default_factory=list)
    amplitudes: Dict[str, float] = field(default_factory=dict)
    rejected_paths: List[str] = field(default_factory=list)
    prompt: str = ""
    raw_llm_response: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _build_prompt(query: str, evidence: List[Dict[str, Any]]) -> str:
    """Construct a prompt from query + sanitized evidence summaries.

    Only id and sanitized_summary are pulled. Bodies are never read.
    """
    parts = [f"Query: {query}"]
    if evidence:
        parts.append("Evidence:")
        for ref in evidence:
            ref_id = ref.get("id", "?")
            summary = ref.get("sanitized_summary", "")
            parts.append(f"- {ref_id}: {summary}")
    return "\n".join(parts)


def _llm_path(llm: Any, query: str, evidence: List[Dict[str, Any]]) -> str:
    """Derive a deterministic selected_path from LLM output."""
    prompt = _build_prompt(query, evidence)
    out = llm.complete(prompt, context={"phase": "select"})
    return f"path:llm:{out['response'][:32]}"


class _BaselineBase:
    name = "base"

    def respond(
        self,
        conn: sqlite3.Connection,
        *,
        query: str,
        snapshot_id: str,
        llm: Any,
        rag: Optional[Any] = None,
        static_memory: Optional[Dict[str, str]] = None,
        seed: int = 0,
    ) -> Response:
        raise NotImplementedError


class LLMOnly(_BaselineBase):
    name = "LLMOnly"

    def respond(
        self,
        conn: sqlite3.Connection,
        *,
        query: str,
        snapshot_id: str,
        llm: Any,
        rag: Optional[Any] = None,
        static_memory: Optional[Dict[str, str]] = None,
        seed: int = 0,
    ) -> Response:
        prompt = _build_prompt(query, [])
        out = llm.complete(prompt, context={"phase": "select", "seed": seed})
        selected = f"path:llm:{out['response'][:32]}"
        return Response(
            selected_path=selected,
            evidence_refs=[],
            active_attractors=[],
            active_marks=[],
            value_contributions={},
            sensitivity_contributions={},
            unresolved_tensions=[],
            suppressed_paths=[],
            warnings=[],
            score_components={},
            baseline_name=self.name,
            model_version=llm.version(),
            candidates=[selected],
            amplitudes={selected: out.get("confidence", 0.5)},
            rejected_paths=[],
            prompt=prompt,
            raw_llm_response=out["response"],
        )


class LLMPlusRAG(_BaselineBase):
    name = "LLMPlusRAG"

    def respond(
        self,
        conn: sqlite3.Connection,
        *,
        query: str,
        snapshot_id: str,
        llm: Any,
        rag: Optional[Any] = None,
        static_memory: Optional[Dict[str, str]] = None,
        seed: int = 0,
    ) -> Response:
        if rag is None:
            raise ValueError("LLMPlusRAG requires a rag adapter")
        evidence = rag.retrieve(query, scope=None, limit=20)
        prompt = _build_prompt(query, evidence)
        out = llm.complete(prompt, context={"phase": "select", "seed": seed})

        candidates = [f"path:{ref['id']}" for ref in evidence]
        amplitudes: Dict[str, float] = {
            cand: float(ref.get("score", 0.0))
            for cand, ref in zip(candidates, evidence)
        }
        if not candidates:
            selected = f"path:llm:{out['response'][:32]}"
            amplitudes[selected] = out.get("confidence", 0.5)
            candidates = [selected]

        selected = max(amplitudes, key=amplitudes.get)
        rejected = [c for c in candidates if c != selected]
        return Response(
            selected_path=selected,
            evidence_refs=[ref["id"] for ref in evidence],
            active_attractors=[],
            active_marks=[],
            value_contributions={},
            sensitivity_contributions={},
            unresolved_tensions=[],
            suppressed_paths=[],
            warnings=[],
            score_components={},
            baseline_name=self.name,
            model_version=llm.version(),
            candidates=candidates,
            amplitudes=amplitudes,
            rejected_paths=rejected,
            prompt=prompt,
            raw_llm_response=out["response"],
        )


class LLMPlusStaticMemory(_BaselineBase):
    name = "LLMPlusStaticMemory"

    def respond(
        self,
        conn: sqlite3.Connection,
        *,
        query: str,
        snapshot_id: str,
        llm: Any,
        rag: Optional[Any] = None,
        static_memory: Optional[Dict[str, str]] = None,
        seed: int = 0,
    ) -> Response:
        memory = static_memory or {}
        prompt = _build_prompt(query, [])
        out = llm.complete(prompt, context={"phase": "select", "seed": seed})

        selected: Optional[str] = None
        warnings: List[str] = []
        for pattern, preferred in memory.items():
            if pattern in query:
                selected = preferred
                warnings.append(f"static_memory hit: {pattern}")
                break
        if selected is None:
            selected = f"path:llm:{out['response'][:32]}"

        candidates = [selected]
        amplitudes = {selected: out.get("confidence", 0.5)}
        return Response(
            selected_path=selected,
            evidence_refs=[],
            active_attractors=[],
            active_marks=[],
            value_contributions={},
            sensitivity_contributions={},
            unresolved_tensions=[],
            suppressed_paths=[],
            warnings=warnings,
            score_components={},
            baseline_name=self.name,
            model_version=llm.version(),
            candidates=candidates,
            amplitudes=amplitudes,
            rejected_paths=[],
            prompt=prompt,
            raw_llm_response=out["response"],
        )


def _load_attractors(conn: sqlite3.Connection, snapshot_id: str) -> Dict[str, Dict[str, Any]]:
    """Load attractors, collapsing decayed copies onto their base path.

    The `apply_decay` operator writes new rows with `target_path =
    "{base}::decayed:{ts}:{id}"` to preserve the append-only invariant.
    Without collapsing, the selector would still see the undecayed
    original under `base` and ignore the decayed copy.

    Here we treat the most recent decayed row (highest `ts`) as the
    effective depth/threshold for `base`. If no decayed row exists, the
    original is used unchanged. This makes `half_life` actually affect
    path selection while keeping the underlying table append-only.
    """
    rows = conn.execute(
        "SELECT * FROM attractors WHERE snapshot_id = ?", (snapshot_id,)
    ).fetchall()
    # base_path -> (priority, row). Decayed rows carry priority = ts (>0);
    # original rows carry priority = 0 so any decayed copy overrides them.
    by_base: Dict[str, tuple] = {}
    for row in rows:
        path = row["target_path"]
        if "::decayed:" in path:
            base, _, suffix = path.partition("::decayed:")
            try:
                ts = int(suffix.split(":")[0])
            except (ValueError, IndexError):
                continue
            existing = by_base.get(base)
            if existing is None or ts > existing[0]:
                by_base[base] = (ts, row)
        else:
            if path not in by_base:
                by_base[path] = (0, row)

    out: Dict[str, Dict[str, Any]] = {}
    for base, (_, row) in by_base.items():
        out[base] = {
            "depth": float(row["depth"]),
            "activation_threshold": float(row["activation_threshold"]),
            "source_marks": json.loads(row["source_marks"]),
            "decay_state": json.loads(row["decay_state"]),
        }
    return out


def _load_active_marks_by_target(
    conn: sqlite3.Connection, snapshot_id: str
) -> Dict[str, List[Dict[str, Any]]]:
    rows = conn.execute(
        """
        SELECT mark_id, operator_type, target_id, strength
        FROM plasticity_marks
        WHERE snapshot_id = ? AND status = 'active'
        """,
        (snapshot_id,),
    ).fetchall()
    out: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        out.setdefault(row["target_id"], []).append(
            {
                "mark_id": row["mark_id"],
                "operator_type": row["operator_type"],
                "strength": float(row["strength"]),
            }
        )
    return out


def _load_value_weights(
    conn: sqlite3.Connection, snapshot_id: str
) -> Dict[str, float]:
    rows = conn.execute(
        "SELECT axis_name, weight FROM value_field_weights WHERE snapshot_id = ?",
        (snapshot_id,),
    ).fetchall()
    return {row["axis_name"]: float(row["weight"]) for row in rows}


def _load_sensitivity_profiles(
    conn: sqlite3.Connection, snapshot_id: str
) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT profile_id, trigger_pattern, gain, threshold, hard_policy
        FROM sensitivity_profiles WHERE snapshot_id = ?
        """,
        (snapshot_id,),
    ).fetchall()
    return [dict(r) for r in rows]


class LLMPlusLPSF(_BaselineBase):
    name = "LLMPlusLPSF"

    def respond(
        self,
        conn: sqlite3.Connection,
        *,
        query: str,
        snapshot_id: str,
        llm: Any,
        rag: Optional[Any] = None,
        static_memory: Optional[Dict[str, str]] = None,
        seed: int = 0,
    ) -> Response:
        if rag is None:
            raise ValueError("LLMPlusLPSF requires a rag adapter")

        evidence = rag.retrieve(query, scope=None, limit=20)
        prompt = _build_prompt(query, evidence)
        out = llm.complete(
            prompt, context={"phase": "select", "seed": seed, "lpsf": True}
        )

        attractors = _load_attractors(conn, snapshot_id)
        marks_by_target = _load_active_marks_by_target(conn, snapshot_id)
        value_weights = _load_value_weights(conn, snapshot_id)
        sensitivity = _load_sensitivity_profiles(conn, snapshot_id)

        candidates = [f"path:{ref['id']}" for ref in evidence] or [
            f"path:llm:{out['response'][:32]}"
        ]
        base_scores: Dict[str, float] = {}
        for ref, cand in zip(evidence, candidates):
            base_scores[cand] = float(ref.get("score", 0.5))
        for cand in candidates:
            base_scores.setdefault(cand, out.get("confidence", 0.5))

        amplitudes: Dict[str, float] = {}
        active_attractors: List[str] = []
        active_marks: List[str] = []
        value_contribs: Dict[str, float] = {}
        sensitivity_contribs: Dict[str, float] = {}
        tensions: List[Dict[str, Any]] = []
        suppressed: List[str] = []
        warnings: List[str] = []

        for cand in candidates:
            amp = base_scores[cand]
            attr = attractors.get(cand)
            if attr is not None:
                amp += attr["depth"]
                active_attractors.append(cand)
                active_marks.extend(attr["source_marks"])
            marks = marks_by_target.get(cand, [])
            deepen_marks = [m for m in marks if m["operator_type"] == "deepen_attractor"]
            inhibit_marks = [m for m in marks if m["operator_type"] == "inhibit_path"]
            weaken_marks = [m for m in marks if m["operator_type"] == "weaken_attractor"]
            for m in inhibit_marks:
                amp -= m["strength"]
                active_marks.append(m["mark_id"])
            for m in weaken_marks:
                amp -= m["strength"] * 0.5
                active_marks.append(m["mark_id"])
            for m in deepen_marks:
                active_marks.append(m["mark_id"])
            if deepen_marks and inhibit_marks:
                tensions.append(
                    {
                        "candidate": cand,
                        "supporting_marks": [m["mark_id"] for m in deepen_marks],
                        "inhibiting_marks": [m["mark_id"] for m in inhibit_marks],
                    }
                )
            amplitudes[cand] = amp

        for axis, w in value_weights.items():
            value_contribs[axis] = w

        for profile in sensitivity:
            pattern = profile.get("trigger_pattern", "")
            if pattern and pattern in query:
                contrib = float(profile["gain"]) - float(profile["threshold"])
                sensitivity_contribs[profile["profile_id"]] = contrib
                if int(profile["hard_policy"]) == 1 and contrib > 0:
                    for cand in list(amplitudes.keys()):
                        if pattern in cand:
                            suppressed.append(cand)
                            amplitudes.pop(cand, None)
                            warnings.append(
                                f"sensitivity hard_policy suppressed {cand}"
                                f" via {profile['profile_id']}"
                            )

        if tensions:
            warnings.append(
                "inhibit_path active alongside deepen_attractor; priority guard"
            )

        if not amplitudes:
            fallback = f"path:llm:{out['response'][:32]}"
            amplitudes[fallback] = 0.0
            candidates.append(fallback)
            warnings.append("all candidates suppressed; falling back to llm path")

        selected = max(amplitudes, key=amplitudes.get)
        rejected = [c for c in candidates if c != selected and c not in suppressed]

        # Dedupe active_marks while preserving order
        seen_marks: List[str] = []
        for m in active_marks:
            if m not in seen_marks:
                seen_marks.append(m)

        return Response(
            selected_path=selected,
            evidence_refs=[ref["id"] for ref in evidence],
            active_attractors=active_attractors,
            active_marks=seen_marks,
            value_contributions=value_contribs,
            sensitivity_contributions=sensitivity_contribs,
            unresolved_tensions=tensions,
            suppressed_paths=suppressed,
            warnings=warnings,
            score_components={},
            baseline_name=self.name,
            model_version=llm.version(),
            candidates=candidates,
            amplitudes=amplitudes,
            rejected_paths=rejected,
            prompt=prompt,
            raw_llm_response=out["response"],
        )


def _pairwise_rank_scores(
    query: str,
    evidence: List[Dict[str, Any]],
    llm: Any,
    *,
    samples: int = 1,
) -> Dict[str, float]:
    """LLM pairwise ranking. Returns ℓ(c) ∈ [0, 1] per candidate.

    For each unordered pair (a, b) in `evidence`, asks the LLM "which is more
    relevant, A or B?" `samples` times. Each candidate's score is its average
    win-rate across all pairs it participated in.

    With `samples=1` and temperature=0 this is fully deterministic.
    With `samples>1` or temperature>0 the LLM noise enters path selection.
    """
    if len(evidence) < 2:
        # Single candidate: no comparison needed
        return {f"path:{ref['id']}": 1.0 for ref in evidence}

    wins: Dict[str, int] = {f"path:{ref['id']}": 0 for ref in evidence}
    appearances: Dict[str, int] = {f"path:{ref['id']}": 0 for ref in evidence}

    n = len(evidence)
    for i in range(n):
        for j in range(i + 1, n):
            ref_a, ref_b = evidence[i], evidence[j]
            cand_a, cand_b = f"path:{ref_a['id']}", f"path:{ref_b['id']}"
            prompt = (
                f"Question: {query}\n\n"
                f"Candidate A: {ref_a.get('sanitized_summary', '')}\n"
                f"Candidate B: {ref_b.get('sanitized_summary', '')}\n\n"
                f"Which candidate is more relevant to the question? "
                f"Reply with a single letter: A or B."
            )
            for s in range(samples):
                out = llm.complete(
                    prompt,
                    context={"phase": "rerank", "pair": [ref_a["id"], ref_b["id"]], "sample": s},
                )
                pick = _parse_pair_choice(out.get("response", ""))
                appearances[cand_a] += 1
                appearances[cand_b] += 1
                if pick == "A":
                    wins[cand_a] += 1
                elif pick == "B":
                    wins[cand_b] += 1
                # else: abstain — neither wins, but both still appeared

    return {
        cand: (wins[cand] / appearances[cand]) if appearances[cand] else 0.0
        for cand in wins
    }


def _parse_pair_choice(response: str) -> Optional[str]:
    """Extract 'A' or 'B' from a pairwise LLM response. Tolerant to whitespace."""
    if not response:
        return None
    cleaned = response.strip().upper()
    if not cleaned:
        return None
    first = cleaned[0]
    if first in {"A", "B"}:
        return first
    # Look for explicit "A" or "B" tokens within first 20 chars
    snippet = cleaned[:20]
    if " A " in f" {snippet} " or snippet.startswith("A:") or snippet.endswith(" A"):
        return "A"
    if " B " in f" {snippet} " or snippet.startswith("B:") or snippet.endswith(" B"):
        return "B"
    return None


class LLMPlusLPSFRerank(_BaselineBase):
    """LPSF + LLM-as-reranker.

    Selection equation:
        amplitudes[c] = α · rag_score(c) + β · ℓ(c) + γ · attractor_depth(c)
        selected      = argmax_c amplitudes[c]

    where ℓ(c) comes from LLM pairwise comparison (see _pairwise_rank_scores).

    Unlike LLMPlusLPSF, the LLM response **does** affect path selection here.
    This is the only baseline in the harness where LLM temperature has a
    causal path to selected_path.
    """

    name = "LLMPlusLPSFRerank"

    def __init__(
        self,
        *,
        alpha: float = 1.0,
        beta: float = 1.0,
        gamma: float = 1.0,
        rerank_samples: int = 1,
        judge_llm: Optional[Any] = None,
    ) -> None:
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.rerank_samples = rerank_samples
        # If provided, judge_llm is used for pairwise ranking (typically with a
        # judge-specific system prompt). Otherwise the main `llm` argument to
        # respond() is reused for both response and ranking.
        self.judge_llm = judge_llm

    def respond(
        self,
        conn: sqlite3.Connection,
        *,
        query: str,
        snapshot_id: str,
        llm: Any,
        rag: Optional[Any] = None,
        static_memory: Optional[Dict[str, str]] = None,
        seed: int = 0,
    ) -> Response:
        if rag is None:
            raise ValueError("LLMPlusLPSFRerank requires a rag adapter")

        evidence = rag.retrieve(query, scope=None, limit=20)
        prompt = _build_prompt(query, evidence)
        # Still call the LLM once for the response text (logged, not selection)
        out = llm.complete(
            prompt,
            context={"phase": "select", "seed": seed, "lpsf_rerank": True},
        )

        attractors = _load_attractors(conn, snapshot_id)
        marks_by_target = _load_active_marks_by_target(conn, snapshot_id)

        candidates = [f"path:{ref['id']}" for ref in evidence]
        if not candidates:
            fallback = f"path:llm:{out['response'][:32]}"
            return Response(
                selected_path=fallback,
                evidence_refs=[],
                active_attractors=[],
                active_marks=[],
                value_contributions={},
                sensitivity_contributions={},
                unresolved_tensions=[],
                suppressed_paths=[],
                warnings=["no candidates from rag"],
                score_components={},
                baseline_name=self.name,
                model_version=llm.version(),
                candidates=[fallback],
                amplitudes={fallback: 0.0},
                rejected_paths=[],
                prompt=prompt,
                raw_llm_response=out["response"],
            )

        # 1. RAG component
        rag_scores: Dict[str, float] = {}
        for ref, cand in zip(evidence, candidates):
            rag_scores[cand] = float(ref.get("score", 0.0))

        # 2. LLM-rank component (the novel ingredient)
        ranker = self.judge_llm if self.judge_llm is not None else llm
        llm_scores = _pairwise_rank_scores(
            query, evidence, ranker, samples=self.rerank_samples
        )

        # 3. Attractor component
        attractor_depths: Dict[str, float] = {}
        active_attractors: List[str] = []
        active_marks: List[str] = []
        for cand in candidates:
            d = 0.0
            attr = attractors.get(cand)
            if attr is not None:
                d += attr["depth"]
                active_attractors.append(cand)
                active_marks.extend(attr["source_marks"])
            for m in marks_by_target.get(cand, []):
                if m["operator_type"] == "deepen_attractor":
                    active_marks.append(m["mark_id"])
                elif m["operator_type"] == "inhibit_path":
                    d -= m["strength"]
                    active_marks.append(m["mark_id"])
                elif m["operator_type"] == "weaken_attractor":
                    d -= m["strength"] * 0.5
                    active_marks.append(m["mark_id"])
            attractor_depths[cand] = d

        # 4. Combine
        amplitudes: Dict[str, float] = {
            cand: self.alpha * rag_scores.get(cand, 0.0)
            + self.beta * llm_scores.get(cand, 0.0)
            + self.gamma * attractor_depths.get(cand, 0.0)
            for cand in candidates
        }

        selected = max(amplitudes, key=amplitudes.get)
        rejected = [c for c in candidates if c != selected]

        seen_marks: List[str] = []
        for m in active_marks:
            if m not in seen_marks:
                seen_marks.append(m)

        return Response(
            selected_path=selected,
            evidence_refs=[ref["id"] for ref in evidence],
            active_attractors=active_attractors,
            active_marks=seen_marks,
            value_contributions={},
            sensitivity_contributions={},
            unresolved_tensions=[],
            suppressed_paths=[],
            warnings=[],
            score_components={
                "alpha": self.alpha,
                "beta": self.beta,
                "gamma": self.gamma,
                "rerank_samples": self.rerank_samples,
            },
            baseline_name=self.name,
            model_version=llm.version(),
            candidates=candidates,
            amplitudes=amplitudes,
            rejected_paths=rejected,
            prompt=prompt,
            raw_llm_response=out["response"],
        )


_BASELINES = {
    "LLMOnly": LLMOnly,
    "LLMPlusRAG": LLMPlusRAG,
    "LLMPlusStaticMemory": LLMPlusStaticMemory,
    "LLMPlusLPSF": LLMPlusLPSF,
    "LLMPlusLPSFRerank": LLMPlusLPSFRerank,
}


def get_baseline(name: str) -> _BaselineBase:
    if name not in _BASELINES:
        raise KeyError(f"Unknown baseline: {name}")
    return _BASELINES[name]()


def baseline_names() -> List[str]:
    return list(_BASELINES.keys())
