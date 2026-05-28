"""Typed records for the M2 SQLite schema.

These dataclasses are plain stdlib containers, not an ORM.
"""

from dataclasses import dataclass, fields
from typing import Any, Dict, List, Optional, Type, TypeVar


T = TypeVar("T", bound="JsonRecord")


class JsonRecord:
    """Mixin for JSON-friendly record serialization."""

    def to_dict(self) -> Dict[str, Any]:
        return {field.name: getattr(self, field.name) for field in fields(self)}

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        values = {field.name: data[field.name] for field in fields(cls) if field.name in data}
        return cls(**values)


@dataclass
class ExperienceEvent(JsonRecord):
    id: Optional[int] = None
    event_id: str = ""
    sanitized_summary: str = ""
    event_type: str = ""
    importance: float = 0.0
    novelty: float = 0.0
    outcome: str = ""
    goal_relevance: float = 0.0
    privacy_level: str = ""
    evidence_refs: List[Any] = None
    snapshot_id: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        if self.evidence_refs is None:
            self.evidence_refs = []


@dataclass
class PlasticityMark(JsonRecord):
    id: Optional[int] = None
    mark_id: str = ""
    operator_type: str = ""
    target_type: str = ""
    target_id: str = ""
    strength: float = 0.0
    half_life: str = ""
    source_experience_id: Optional[str] = None
    evidence_refs: List[Any] = None
    reason: str = ""
    status: str = "active"
    privacy_level: str = ""
    scope: str = ""
    snapshot_id: str = ""
    created_at: str = ""
    updated_at: str = ""
    supersedes_mark_id: Optional[str] = None
    reversed_by_mark_id: Optional[str] = None
    score_delta_meta: Dict[str, Any] = None

    def __post_init__(self) -> None:
        if self.evidence_refs is None:
            self.evidence_refs = []
        if self.score_delta_meta is None:
            self.score_delta_meta = {}


@dataclass
class Attractor(JsonRecord):
    id: Optional[int] = None
    target_path: str = ""
    depth: float = 0.0
    activation_threshold: float = 0.0
    half_life: str = ""
    last_activation_at: Optional[str] = None
    source_marks: List[Any] = None
    decay_state: Dict[str, Any] = None
    snapshot_id: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if self.source_marks is None:
            self.source_marks = []
        if self.decay_state is None:
            self.decay_state = {}


@dataclass
class SemanticNode(JsonRecord):
    id: Optional[int] = None
    node_id: str = ""
    node_type: str = ""
    label: str = ""
    validation_status: str = ""
    evidence_refs: List[Any] = None
    snapshot_id: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        if self.evidence_refs is None:
            self.evidence_refs = []


@dataclass
class SemanticEdge(JsonRecord):
    id: Optional[int] = None
    edge_id: str = ""
    source_node_id: str = ""
    target_node_id: str = ""
    relation_type: str = ""
    weight: float = 0.0
    validation_status: str = ""
    evidence_refs: List[Any] = None
    snapshot_id: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        if self.evidence_refs is None:
            self.evidence_refs = []


@dataclass
class ValueFieldWeight(JsonRecord):
    id: Optional[int] = None
    axis_name: str = ""
    scope: str = ""
    weight: float = 0.0
    source_marks: List[Any] = None
    decay_state: Dict[str, Any] = None
    score_contribution_meta: Dict[str, Any] = None
    snapshot_id: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if self.source_marks is None:
            self.source_marks = []
        if self.decay_state is None:
            self.decay_state = {}
        if self.score_contribution_meta is None:
            self.score_contribution_meta = {}


@dataclass
class SensitivityProfile(JsonRecord):
    id: Optional[int] = None
    profile_id: str = ""
    trigger_pattern: str = ""
    gain: float = 1.0
    threshold: float = 0.0
    scope: str = ""
    hard_policy: bool = False
    false_positive_observations: List[Any] = None
    source_marks: List[Any] = None
    decay_state: Dict[str, Any] = None
    snapshot_id: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if self.false_positive_observations is None:
            self.false_positive_observations = []
        if self.source_marks is None:
            self.source_marks = []
        if self.decay_state is None:
            self.decay_state = {}


@dataclass
class SchemaMapping(JsonRecord):
    id: Optional[int] = None
    mapping_id: str = ""
    old_schema: str = ""
    new_schema: str = ""
    affected_targets: List[Any] = None
    reason: str = ""
    validation_status: str = ""
    source_experience_id: Optional[str] = None
    evidence_refs: List[Any] = None
    preservation_note: str = ""
    snapshot_id: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        if self.affected_targets is None:
            self.affected_targets = []
        if self.evidence_refs is None:
            self.evidence_refs = []


@dataclass
class ReconsolidationRecord(JsonRecord):
    id: Optional[int] = None
    record_id: str = ""
    old_target_id: str = ""
    new_target_id: str = ""
    reason: str = ""
    validation_status: str = ""
    source_experience_id: Optional[str] = None
    evidence_refs: List[Any] = None
    preservation_note: str = ""
    snapshot_id: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        if self.evidence_refs is None:
            self.evidence_refs = []


@dataclass
class HypothesisTrace(JsonRecord):
    id: Optional[int] = None
    trace_id: str = ""
    query_id: str = ""
    candidates: List[Any] = None
    amplitudes: Dict[str, Any] = None
    interference_matrix: Any = None
    selected_hypothesis: str = ""
    rejected_paths: List[Any] = None
    score_components: Dict[str, Any] = None
    snapshot_id: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        if self.candidates is None:
            self.candidates = []
        if self.amplitudes is None:
            self.amplitudes = {}
        if self.interference_matrix is None:
            self.interference_matrix = []
        if self.rejected_paths is None:
            self.rejected_paths = []
        if self.score_components is None:
            self.score_components = {}


@dataclass
class CollapseTrace(JsonRecord):
    id: Optional[int] = None
    trace_id: str = ""
    query_id: str = ""
    selected_path: str = ""
    active_attractors: List[Any] = None
    active_marks: List[Any] = None
    evidence_refs: List[Any] = None
    value_contributions: Dict[str, Any] = None
    sensitivity_contributions: Dict[str, Any] = None
    unresolved_tensions: List[Any] = None
    suppressed_paths: List[Any] = None
    warnings: List[Any] = None
    snapshot_id: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        if self.active_attractors is None:
            self.active_attractors = []
        if self.active_marks is None:
            self.active_marks = []
        if self.evidence_refs is None:
            self.evidence_refs = []
        if self.value_contributions is None:
            self.value_contributions = {}
        if self.sensitivity_contributions is None:
            self.sensitivity_contributions = {}
        if self.unresolved_tensions is None:
            self.unresolved_tensions = []
        if self.suppressed_paths is None:
            self.suppressed_paths = []
        if self.warnings is None:
            self.warnings = []


@dataclass
class EvidenceSnapshot(JsonRecord):
    id: Optional[int] = None
    snapshot_id: str = ""
    adapter_version: str = ""
    allowed_scope: List[str] = None
    source_counts: Dict[str, Any] = None
    index_metadata: Dict[str, Any] = None
    retrieval_parameters: Dict[str, Any] = None
    drift_observations: List[Any] = None
    created_at: str = ""
    pinned_at: str = ""

    def __post_init__(self) -> None:
        if self.allowed_scope is None:
            self.allowed_scope = []
        if self.source_counts is None:
            self.source_counts = {}
        if self.index_metadata is None:
            self.index_metadata = {}
        if self.retrieval_parameters is None:
            self.retrieval_parameters = {}
        if self.drift_observations is None:
            self.drift_observations = []


@dataclass
class EvaluationRun(JsonRecord):
    id: Optional[int] = None
    run_id: str = ""
    suite_name: str = ""
    candidate_name: str = ""
    baseline_name: str = ""
    snapshot_id: str = ""
    state_db_version: str = ""
    prompts: List[Any] = None
    sanitized_outputs: List[Any] = None
    score_summary: Dict[str, Any] = None
    failures: List[Any] = None
    report_refs: List[Any] = None
    created_at: str = ""

    def __post_init__(self) -> None:
        if self.prompts is None:
            self.prompts = []
        if self.sanitized_outputs is None:
            self.sanitized_outputs = []
        if self.score_summary is None:
            self.score_summary = {}
        if self.failures is None:
            self.failures = []
        if self.report_refs is None:
            self.report_refs = []
