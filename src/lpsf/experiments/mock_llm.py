"""Deterministic mock LLM for M4 Phase 1 experiments.

No network, no subprocess, no file I/O. Given the same (prompt, context, seed),
always returns the same response.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional


class MockLLM:
    """Deterministic LLM stub for experiment baselines."""

    def __init__(
        self,
        *,
        seed: int = 0,
        response_map: Optional[Dict[str, str]] = None,
    ) -> None:
        self._seed = seed
        self._response_map: Dict[str, str] = response_map or {}

    def complete(
        self, prompt: str, *, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Return a deterministic response dict. No network, no subprocess."""
        key = self._hash_key(prompt, context)

        # Check response_map first (prefix match on hash)
        for prefix, canned in self._response_map.items():
            if key.startswith(prefix):
                return {
                    "response": canned,
                    "confidence": 0.85,
                    "evidence_refs": [],
                    "model": self.version(),
                }

        # Deterministic fallback: derive a stable response from the hash
        response_text = f"mock-response-{key[:16]}"
        confidence = self._hash_to_float(key, 0.3, 0.95)
        return {
            "response": response_text,
            "confidence": confidence,
            "evidence_refs": [],
            "model": self.version(),
        }

    def version(self) -> str:
        return "mock-llm-v0"

    # -- internals --

    def _hash_key(self, prompt: str, context: Optional[Dict[str, Any]]) -> str:
        payload = json.dumps(
            {"prompt": prompt, "context": context, "seed": self._seed},
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _hash_to_float(hex_str: str, lo: float, hi: float) -> float:
        value = int(hex_str[:8], 16) / 0xFFFFFFFF
        return lo + value * (hi - lo)
