"""LPSF application layer — turns the research harness into a usable tool.

The key capability here that the experiment harness lacks: **persistence of
user feedback as attractors**. In the experiments, attractors are set
synthetically. In a real tool, each user selection is recorded as an
experience_event that deepens an attractor, so future searches personalize.

This is the honest realization of the original LPSF vision — "a system whose
response landscape changes after experience" — scoped to what the code
actually does: a reranking prior that accumulates from real usage.
"""

from .session import LPSFSearchSession, SearchResult

__all__ = ["LPSFSearchSession", "SearchResult"]
