"""Tests for cost tracker + budget guard."""

import pytest

from lpsf.experiments.cost import (
    PRICING,
    BudgetExceeded,
    BudgetGuard,
    TokenUsage,
    summarize,
)


def test_known_model_pricing_positive():
    rates = PRICING["claude-sonnet-4-5"]
    assert rates["input"] > 0
    assert rates["output"] > rates["input"]  # output more expensive than input


def test_mock_model_is_free():
    rates = PRICING["mock-llm-v0"]
    assert rates["input"] == 0
    assert rates["output"] == 0


def test_token_usage_add_and_cost():
    u = TokenUsage(model="claude-sonnet-4-5")
    u.add(input_tokens=1000, output_tokens=500)
    # input: 1000 * 3 / 1M = 0.003; output: 500 * 15 / 1M = 0.0075; total 0.0105
    assert u.cost() == pytest.approx(0.0105, rel=1e-3)
    assert u.calls == 1


def test_token_usage_cache_hit_discount():
    u = TokenUsage(model="claude-sonnet-4-5")
    u.add(input_tokens=1000, output_tokens=500, cached_input_tokens=900)
    # billed input = (1000-900) + 900*0.1 = 100 + 90 = 190 tokens
    # = 190 * 3 / 1M = 0.00057
    # output = 500 * 15 / 1M = 0.0075
    # total = 0.00807
    assert u.cost() == pytest.approx(0.00807, rel=1e-3)


def test_token_usage_unknown_model_zero_cost():
    u = TokenUsage(model="future-model-xyz")
    u.add(input_tokens=100000, output_tokens=100000)
    assert u.cost() == 0.0


def test_summarize_aggregates():
    a = TokenUsage(model="claude-sonnet-4-5")
    a.add(input_tokens=1000, output_tokens=500)
    b = TokenUsage(model="gpt-4o")
    b.add(input_tokens=1000, output_tokens=500)
    out = summarize([a, b])
    assert out["total_calls"] == 2
    assert out["total_estimated_cost_usd"] > 0
    assert len(out["per_model"]) == 2


def test_budget_guard_passes_under_cap():
    u = TokenUsage(model="claude-sonnet-4-5")
    u.add(input_tokens=1000, output_tokens=500)
    guard = BudgetGuard(cap_usd=1.00)
    guard.check([u])  # cost is ~$0.01, way under


def test_budget_guard_raises_over_cap():
    u = TokenUsage(model="claude-opus-4-7")
    u.add(input_tokens=1_000_000, output_tokens=1_000_000)
    # input $15 + output $75 = $90, over $1 cap
    guard = BudgetGuard(cap_usd=1.0)
    with pytest.raises(BudgetExceeded):
        guard.check([u])
