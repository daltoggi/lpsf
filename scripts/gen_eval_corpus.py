#!/usr/bin/env python3
"""Generate a labeled evaluation corpus for the IR benchmark.

Deterministic (seeded). Produces topic-clustered markdown docs and a query
set with ground-truth relevant doc ids. Topics share a controlled amount of
vocabulary so BM25 ranking is imperfect — that imperfection is the room a
reranker (LLM judge) or a personalization prior (attractor) has to work in.

Outputs:
    data/eval_corpus/*.md      generated docs
    data/eval_labels.json      {queries: [{query, relevant_ids, topic}], topics: {...}}

This is still SYNTHETIC — bigger, not real. It buys us real IR *metrics*
(nDCG/MRR) and relative comparisons, not external validity. The benchmark
report says so plainly.

Usage:
    python3 scripts/gen_eval_corpus.py
    python3 scripts/gen_eval_corpus.py --docs-per-topic 6 --seed 7
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = REPO_ROOT / "data" / "eval_corpus"
LABELS_PATH = REPO_ROOT / "data" / "eval_labels.json"


# Each topic: a core vocabulary (heavily used) + a display name.
TOPICS = {
    "databases": ["sqlite", "postgres", "transaction", "index", "schema", "query", "acid", "replication"],
    "search": ["bm25", "tokenizer", "inverted", "ranking", "retrieval", "fulltext", "relevance", "recall"],
    "embeddings": ["vector", "embedding", "cosine", "ann", "semantic", "nearest", "dense", "dimension"],
    "rag": ["retrieval", "augmented", "generation", "context", "grounding", "citation", "hallucination", "prompt"],
    "reranking": ["reranker", "pairwise", "listwise", "crossencoder", "shortlist", "rerank", "judge", "ordering"],
    "localfirst": ["offline", "sync", "crdt", "ownership", "device", "conflict", "eventual", "local"],
    "evaluation": ["benchmark", "ndcg", "metric", "groundtruth", "baseline", "ablation", "significance", "label"],
    "caching": ["cache", "ttl", "eviction", "memoize", "hit", "invalidate", "warm", "lru"],
}

# Shared "glue" vocabulary that appears across all topics (creates BM25 noise).
SHARED = ["system", "data", "design", "approach", "tradeoff", "performance", "scale", "use"]

# Queries: short and using a couple of core terms only. Short queries +
# heavy doc bleed = imperfect BM25 (relevant docs not all in top-k).
QUERY_TEMPLATES = {
    "databases": "transaction index schema acid",
    "search": "bm25 tokenizer inverted relevance",
    "embeddings": "vector embedding cosine nearest",
    "rag": "augmented generation grounding citation",
    "reranking": "reranker pairwise listwise ordering",
    "localfirst": "offline crdt conflict eventual",
    "evaluation": "ndcg groundtruth ablation significance",
    "caching": "eviction ttl memoize lru",
}


def make_doc(topic: str, idx: int, rng: random.Random) -> str:
    """Generate a doc with HEAVY cross-topic vocabulary bleed.

    The bleed is deliberate: it makes BM25 imperfect, so a reranker or a
    personalization prior has measurable room to help (or hurt). Without
    bleed, BM25 separates topics perfectly and every metric saturates at 1.0,
    which measures nothing.
    """
    core = TOPICS[topic]
    others = [t for t in TOPICS if t != topic]
    other1, other2 = rng.sample(others, 2)
    v1, v2 = TOPICS[other1], TOPICS[other2]

    sentences = []
    for _ in range(rng.randint(6, 9)):
        words = (
            rng.choices(core, k=rng.randint(3, 5))      # own topic (still dominant-ish)
            + rng.choices(SHARED, k=rng.randint(2, 4))  # heavy shared glue
            + rng.choices(v1, k=rng.randint(2, 4))      # heavy bleed from other topic 1
            + rng.choices(v2, k=rng.randint(1, 3))      # bleed from other topic 2
        )
        rng.shuffle(words)
        sentences.append(" ".join(words).capitalize() + ".")
    title = f"{topic.capitalize()} note {idx}"
    body = " ".join(sentences)
    return f"# {title}\n\n{body}\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs-per-topic", type=int, default=8)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = random.Random(args.seed)

    if CORPUS_DIR.exists():
        shutil.rmtree(CORPUS_DIR)
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)

    topic_to_ids: dict = {t: [] for t in TOPICS}
    for topic in TOPICS:
        for i in range(args.docs_per_topic):
            doc_id = f"{topic}_{i:02d}"
            (CORPUS_DIR / f"{doc_id}.md").write_text(make_doc(topic, i, rng), encoding="utf-8")
            topic_to_ids[topic].append(doc_id)

    queries = []
    for topic, q in QUERY_TEMPLATES.items():
        queries.append({
            "query": q,
            "topic": topic,
            "relevant_ids": topic_to_ids[topic],  # all docs of the topic are relevant
        })

    labels = {
        "seed": args.seed,
        "docs_per_topic": args.docs_per_topic,
        "total_docs": args.docs_per_topic * len(TOPICS),
        "topics": topic_to_ids,
        "queries": queries,
    }
    LABELS_PATH.write_text(json.dumps(labels, indent=2), encoding="utf-8")

    print(f"Wrote {labels['total_docs']} docs across {len(TOPICS)} topics → {CORPUS_DIR}")
    print(f"Wrote {len(queries)} labeled queries → {LABELS_PATH}")


if __name__ == "__main__":
    main()
