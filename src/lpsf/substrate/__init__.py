"""LPSF substrate track — memory in parameters, not in the input context.

A numpy mechanism demonstration (NOT a language model) for the question the
hosted-API reranking track cannot touch: can experience write memory into a
system's *parameters* so it recalls with an empty input context, and can
capacity *grow* with experience instead of being capped at a fixed dimension?

See `ops/lpsf/SUBSTRATE_RECALL.md` and `docs/lpsf/SUBSTRATE_NOTES.md`.
"""

from .core import FrozenCore
from .memories import ExpandableMemory, FixedHebbian, FrozenRAG

__all__ = ["FrozenCore", "FrozenRAG", "FixedHebbian", "ExpandableMemory"]
