# Evaluating Retrieval-Augmented Generation

RAG systems pair a retriever with a generator. The retriever pulls context
from a corpus; the generator produces an answer conditioned on that context.
Evaluating the combined system is harder than evaluating either component
alone because errors compound across the pipeline.

Common metric families include retrieval quality (recall@k, nDCG, MRR),
faithfulness of the generator to the retrieved context (often LLM-judged),
and end-task answer correctness against ground truth. Each captures a
different failure mode. A system with high retrieval recall can still
produce wrong answers if the generator ignores the context, and a faithful
generator on bad context will reproduce errors confidently.

A repeated finding in recent benchmarks is that oracle-context evaluation
overstates RAG performance. When the retriever is replaced with a perfect
oracle, generators look strong; under real retrieval with imperfect recall,
performance drops sharply. This means benchmark choices that fix the
context or test only the generator give optimistic numbers.

For practitioners, the useful evaluation harness logs the full pipeline:
query, retrieved candidates with scores, prompt sent to the generator, raw
generation, and final answer. Failure attribution requires the whole chain.
Cost accounting matters too — token counts and cache hit rates can dwarf
correctness differences for budget-sensitive deployments.

When introducing a new component such as a learned reranker or a
persistent-state prior, evaluate against both an end-task metric and a
retrieval-quality metric to attribute the change.
