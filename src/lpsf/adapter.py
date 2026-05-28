"""Read-only evidence adapter contract for M2."""

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class EvidenceAdapter(Protocol):
    """Protocol for sanitized, read-only evidence retrieval."""

    def version(self) -> str:
        """Return the adapter version string."""

    def allowed_scope(self) -> List[str]:
        """Return the zones this adapter may read."""

    def snapshot_metadata(self) -> Dict[str, Any]:
        """Return metadata needed to pin a reproducible snapshot."""

    def retrieve(
        self, query: str, scope: Optional[List[str]] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Return sanitized evidence references without source bodies."""

    def is_blocked(self, source_id: str) -> bool:
        """Return whether a source id must be excluded."""


class NullAdapter:
    """Adapter used when no evidence source is connected."""

    def version(self) -> str:
        return "null-0"

    def allowed_scope(self) -> List[str]:
        return []

    def snapshot_metadata(self) -> Dict[str, Any]:
        return {
            "index_metadata": {},
            "source_counts": {},
            "retrieval_parameters": {},
        }

    def retrieve(
        self, query: str, scope: Optional[List[str]] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        return []

    def is_blocked(self, source_id: str) -> bool:
        return False
