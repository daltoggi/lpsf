"""Tests for IR metrics with textbook-known values."""

import math

import pytest

from lpsf.experiments.metrics import (
    average_metrics,
    dcg_at_k,
    mrr,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)


RANKED = ["a", "b", "c", "d", "e"]


def test_recall_at_k():
    assert recall_at_k(RANKED, {"a", "c"}, k=3) == 1.0       # both in top 3
    assert recall_at_k(RANKED, {"a", "d"}, k=3) == 0.5       # only a in top 3
    assert recall_at_k(RANKED, {"x"}, k=5) == 0.0
    assert recall_at_k(RANKED, set(), k=5) == 0.0


def test_precision_at_k():
    assert precision_at_k(RANKED, {"a", "b"}, k=2) == 1.0
    assert precision_at_k(RANKED, {"a"}, k=2) == 0.5
    assert precision_at_k(RANKED, {"a"}, k=0) == 0.0


def test_mrr():
    assert mrr(RANKED, {"a"}) == 1.0           # first position
    assert mrr(RANKED, {"b"}) == 0.5           # second
    assert mrr(RANKED, {"c"}) == pytest.approx(1 / 3)
    assert mrr(RANKED, {"x"}) == 0.0           # none


def test_dcg_first_position():
    # single relevant item at rank 1 → gain 1/log2(2) = 1.0
    assert dcg_at_k(RANKED, {"a"}, k=5) == pytest.approx(1.0)
    # at rank 2 → 1/log2(3)
    assert dcg_at_k(RANKED, {"b"}, k=5) == pytest.approx(1 / math.log2(3))


def test_ndcg_perfect_when_relevant_on_top():
    # two relevant items at ranks 1,2 → perfect packing → ndcg 1.0
    assert ndcg_at_k(RANKED, {"a", "b"}, k=5) == pytest.approx(1.0)


def test_ndcg_less_than_one_when_relevant_lower():
    # relevant at ranks 1 and 3 → less than ideal (which is ranks 1,2)
    val = ndcg_at_k(RANKED, {"a", "c"}, k=5)
    assert 0.0 < val < 1.0


def test_ndcg_zero_when_no_relevant():
    assert ndcg_at_k(RANKED, set(), k=5) == 0.0
    assert ndcg_at_k(RANKED, {"zzz"}, k=5) == 0.0


def test_ndcg_monotonic_in_position():
    # relevant item ranked higher should yield higher ndcg
    top = ndcg_at_k(["a", "b", "c"], {"a"}, k=3)
    mid = ndcg_at_k(["b", "a", "c"], {"a"}, k=3)
    low = ndcg_at_k(["b", "c", "a"], {"a"}, k=3)
    assert top > mid > low


def test_average_metrics():
    rows = [
        {"ndcg": 1.0, "mrr": 1.0},
        {"ndcg": 0.0, "mrr": 0.0},
    ]
    out = average_metrics(rows)
    assert out["ndcg"] == 0.5
    assert out["mrr"] == 0.5
    assert average_metrics([]) == {}
