"""Public API for M3 plasticity operators."""

from ._base import OperatorError, PolicyViolation, UnknownOperator
from .deepen_attractor import deepen_attractor
from .inhibit_path import inhibit_path
from .modulate_sensitivity import modulate_sensitivity
from .open_path import open_path
from .reconsolidate_memory import reconsolidate_memory
from .remap_schema import remap_schema
from .tilt_value_field import tilt_value_field
from .weaken_attractor import weaken_attractor


_OPERATORS = {
    "deepen_attractor": deepen_attractor,
    "weaken_attractor": weaken_attractor,
    "open_path": open_path,
    "inhibit_path": inhibit_path,
    "tilt_value_field": tilt_value_field,
    "modulate_sensitivity": modulate_sensitivity,
    "remap_schema": remap_schema,
    "reconsolidate_memory": reconsolidate_memory,
}


def apply_operator(operator_type, conn, **kwargs):
    try:
        operator = _OPERATORS[operator_type]
    except KeyError as exc:
        raise UnknownOperator(f"Unknown operator: {operator_type}") from exc
    return operator(conn, **kwargs)


__all__ = [
    "OperatorError",
    "PolicyViolation",
    "UnknownOperator",
    "apply_operator",
    "deepen_attractor",
    "weaken_attractor",
    "open_path",
    "inhibit_path",
    "tilt_value_field",
    "modulate_sensitivity",
    "remap_schema",
    "reconsolidate_memory",
]
