"""Cost tracking and pricing tables for paid LLM APIs (M4 Phase 3).

Prices are per 1M tokens as of 2026-05. Update PRICING when launching against
a model whose rate has changed. Always verify the live pricing page before a
benchmark run that exceeds the budget cap.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# Per 1M tokens (USD). Add new models as needed.
PRICING: Dict[str, Dict[str, float]] = {
    # Anthropic
    "claude-sonnet-4-5":     {"input": 3.00, "output": 15.00},
    "claude-3-5-sonnet-latest": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5":      {"input": 1.00, "output": 5.00},
    "claude-3-5-haiku-latest": {"input": 0.80, "output": 4.00},
    "claude-opus-4-7":       {"input": 15.00, "output": 75.00},
    # OpenAI
    "gpt-4o":                {"input": 2.50, "output": 10.00},
    "gpt-4o-mini":           {"input": 0.15, "output": 0.60},
    "gpt-4.1":               {"input": 2.00, "output": 8.00},
    "gpt-4.1-mini":          {"input": 0.40, "output": 1.60},
    # Generic fallback used by tests + mocks
    "mock-llm-v0":           {"input": 0.0, "output": 0.0},
    "codex-chatgpt-v1":      {"input": 0.0, "output": 0.0},
}


@dataclass
class TokenUsage:
    """Per-LLM token + cost accumulator."""

    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int = 0  # tokens that hit Anthropic prompt cache
    calls: int = 0
    cache_hits: int = 0  # in-process file-cache hits (zero token cost)

    def add(
        self,
        *,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cached_input_tokens: int = 0,
    ) -> None:
        self.input_tokens += int(input_tokens)
        self.output_tokens += int(output_tokens)
        self.cached_input_tokens += int(cached_input_tokens)
        self.calls += 1

    def cost(self) -> float:
        rates = PRICING.get(self.model)
        if rates is None:
            return 0.0
        # Anthropic cache_hit pricing is ~10% of standard input. Apply simple
        # discount: cached_input billed at 10%, regular input at 100%.
        billed_input = (
            (self.input_tokens - self.cached_input_tokens)
            + self.cached_input_tokens * 0.10
        )
        return (
            billed_input * rates["input"] / 1_000_000
            + self.output_tokens * rates["output"] / 1_000_000
        )

    def to_dict(self) -> Dict[str, float]:
        return {
            "model": self.model,
            "calls": self.calls,
            "cache_hits": self.cache_hits,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cached_input_tokens": self.cached_input_tokens,
            "estimated_cost_usd": round(self.cost(), 6),
        }


@dataclass
class BudgetGuard:
    """Hard budget cap. Raises BudgetExceeded once the cumulative spend is
    projected to exceed `cap_usd` on the next call (using a configurable
    safety margin)."""

    cap_usd: float
    safety_margin: float = 1.10  # 10% headroom

    def check(self, usages: List[TokenUsage]) -> None:
        total = sum(u.cost() for u in usages)
        if total * self.safety_margin > self.cap_usd:
            raise BudgetExceeded(
                f"projected cost ${total*self.safety_margin:.4f} > cap "
                f"${self.cap_usd:.4f}; aborting"
            )


class BudgetExceeded(RuntimeError):
    """Raised when a benchmark run would exceed its budget cap."""


def summarize(usages: List[TokenUsage]) -> Dict[str, object]:
    """Roll up multiple TokenUsage instances into one summary dict."""
    per_model = [u.to_dict() for u in usages]
    total_cost = sum(u.cost() for u in usages)
    total_calls = sum(u.calls for u in usages)
    total_cache_hits = sum(u.cache_hits for u in usages)
    return {
        "per_model": per_model,
        "total_calls": total_calls,
        "total_cache_hits": total_cache_hits,
        "total_estimated_cost_usd": round(total_cost, 6),
    }
