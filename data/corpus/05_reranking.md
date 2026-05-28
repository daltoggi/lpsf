# Reranking in Information Retrieval

A reranker is a second-stage scorer that re-orders the top-k candidates from
a fast first-stage retriever. The first stage trades recall for speed —
BM25, dense vector ANN, or hybrid — and returns far more candidates than the
user will see. The reranker then applies a more expensive but more accurate
scorer to the shortlist, often a cross-encoder model that examines query and
candidate together.

The motivation is asymmetric: first-stage retrievers are limited by the
cost of looking at every document, but a reranker only needs to consider
k candidates per query. A cross-encoder that would be infeasible across
millions of documents is perfectly fine across the top 100.

Recent work uses large language models directly as rerankers. Pairwise
Ranking Prompting asks the LLM to compare two candidates at a time; listwise
methods feed the entire shortlist at once. Both have shown strong results
on TREC-DL and BEIR benchmarks compared to traditional learned-to-rank
methods, though at significantly higher latency and cost.

A useful framing is that rerankers inject task-specific judgment that the
fast retriever could not afford. Combined with persistent state — for
example a user's past selections — a reranker becomes a personalization
surface: same query, same retrieval, different ranking per user.

The risk is that an miscalibrated reranker can systematically suppress
relevant results, especially if its scores combine additively with the
first-stage score. Always evaluate reranker quality on held-out queries.
