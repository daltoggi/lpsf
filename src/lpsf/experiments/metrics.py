"""Information-retrieval metrics for the LPSF IR benchmark.

All functions are pure. They consume a ranked list of candidate ids (best
first) and a set/collection of relevant ids, and return a float. Binary
relevance is assumed (a candidate is relevant or not).

These let us put real numbers on LPSF's effect: not "does it feel better"
but nDCG@k / MRR / recall@k deltas across baselines on a labeled set.
"""

from __future__ import annotations

import math
from typing import Iterable, List, Sequence


def _relevant_set(relevant_ids: Iterable[str]) -> set:
    return {r for r in relevant_ids if r}


def recall_at_k(ranked_ids: Sequence[str], relevant_ids: Iterable[str], k: int) -> float:
    """Fraction of relevant items that appear in the top k."""
    rel = _relevant_set(relevant_ids)
    if not rel:
        return 0.0
    topk = list(ranked_ids)[:k]
    hit = sum(1 for r in rel if r in topk)
    return hit / len(rel)


def precision_at_k(ranked_ids: Sequence[str], relevant_ids: Iterable[str], k: int) -> float:
    """Fraction of the top k that are relevant."""
    if k <= 0:
        return 0.0
    rel = _relevant_set(relevant_ids)
    topk = list(ranked_ids)[:k]
    if not topk:
        return 0.0
    hit = sum(1 for c in topk if c in rel)
    return hit / min(k, len(topk))


def mrr(ranked_ids: Sequence[str], relevant_ids: Iterable[str]) -> float:
    """Reciprocal rank of the first relevant item (0 if none)."""
    rel = _relevant_set(relevant_ids)
    for i, c in enumerate(ranked_ids, start=1):
        if c in rel:
            return 1.0 / i
    return 0.0


def dcg_at_k(ranked_ids: Sequence[str], relevant_ids: Iterable[str], k: int) -> float:
    """Discounted cumulative gain with binary relevance.

    gain_i = 1 if relevant else 0; discount = 1/log2(i+1) for rank i (1-based).
    """
    rel = _relevant_set(relevant_ids)
    total = 0.0
    for i, c in enumerate(list(ranked_ids)[:k], start=1):
        if c in rel:
            total += 1.0 / math.log2(i + 1)
    return total


def ndcg_at_k(ranked_ids: Sequence[str], relevant_ids: Iterable[str], k: int) -> float:
    """Normalized DCG@k. 1.0 = all relevant items packed at the top."""
    rel = _relevant_set(relevant_ids)
    if not rel:
        return 0.0
    dcg = dcg_at_k(ranked_ids, rel, k)
    # Ideal DCG: as many relevant items as fit in k, all at the front.
    ideal_hits = min(len(rel), k)
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_hits + 1))
    if idcg == 0.0:
        return 0.0
    return dcg / idcg


def average_metrics(rows: List[dict]) -> dict:
    """Average a list of per-query metric dicts (same keys) into one dict."""
    if not rows:
        return {}
    keys = rows[0].keys()
    out = {}
    for key in keys:
        vals = [float(r[key]) for r in rows if key in r]
        out[key] = sum(vals) / len(vals) if vals else 0.0
    return out
