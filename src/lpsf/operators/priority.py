"""Priority order for M3 plasticity operators.

Spec section 5 names inhibition, source grounding, schema, opening, deepening,
value tilt, and sensitivity. M3 has no source-grounding operator because
grounding is enforced by evidence_refs validation. Reconsolidation is implicit
in the schema/reinterpretation family, so it is placed next to remap_schema.
Weaken sits immediately after deepen because it is the direct reversible
counterpart for attractor depth.
"""

ORDER = (
    "inhibit_path",
    "remap_schema",
    "reconsolidate_memory",
    "open_path",
    "deepen_attractor",
    "weaken_attractor",
    "tilt_value_field",
    "modulate_sensitivity",
)


def priority_rank(operator_type):
    try:
        return ORDER.index(operator_type)
    except ValueError:
        return len(ORDER)
