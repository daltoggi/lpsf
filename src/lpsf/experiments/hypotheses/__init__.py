"""Hypothesis modules H1-H5 for M4 Phase 1.

Each module exposes:
- `build_scenario(snapshot_id, event_id) -> dict`
- `verify(result) -> tuple[bool, list[str]]`
"""

from . import (
    h1_before_after,
    h2_operator_causality,
    h3_privacy_safety,
    h4_snapshot_reproducibility,
    h5_tension_register,
    h6_adversarial,
    h7_reconsolidation,
    h8_decay_recovery,
)


HYPOTHESES = {
    "H1_before_after": h1_before_after,
    "H2_operator_causality": h2_operator_causality,
    "H3_privacy_safety": h3_privacy_safety,
    "H4_snapshot_reproducibility": h4_snapshot_reproducibility,
    "H5_tension_register": h5_tension_register,
    "H6_adversarial": h6_adversarial,
    "H7_reconsolidation": h7_reconsolidation,
    # H8 uses custom orchestration (apply_decay is not a standard operator);
    # it is exercised by tests/experiments/test_h8_decay_recovery.py rather
    # than via run_experiment, so it is intentionally NOT registered here.
}


__all__ = [
    "HYPOTHESES",
    "h1_before_after",
    "h2_operator_causality",
    "h3_privacy_safety",
    "h4_snapshot_reproducibility",
    "h5_tension_register",
    "h6_adversarial",
    "h7_reconsolidation",
    "h8_decay_recovery",
]
