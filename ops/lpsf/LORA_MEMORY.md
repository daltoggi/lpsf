# LoRA-from-Experience — the memory test on a real model

_Generated 2026-05-28T17:04:47Z_  
_Model: mlx-community/Qwen2.5-0.5B-Instruct-4bit (MLX, Apple Silicon). Fictional fact taught by LoRA._

## The test

Same falsifiable question as the numpy substrate demo, on a real
transformer: after teaching a fictional fact by LoRA, can the model
recall it with an **empty context**? If yes, the memory is in the
(LoRA) weights — not the prompt.

## Accuracy (held-out phrasings, disjoint from training)

| Condition | recall |
|---|---:|
| base model, empty context | 0.00 |
| base model, fact in context (RAG) | 0.67 |
| **LoRA model, empty context** | **1.00** |

## Per-question transcript

**Q: Approximately when was the Zarnak Protocol adopted?**  (must contain: ['2087'])

- base + empty:   miss — 'The Zarnak Protocol, also known as the Zarnak Protocol, was adopted in 2019. It is a decentralized and open-source blockchain platform that aims to provide a mo'
- base + context: HIT — 'The Zarnak Protocol was ratified in 2087 by the Veltrian Assembly.'
- LoRA + empty:   HIT — 'In 2087.'

**Q: Identify the legislative body behind the Zarnak Protocol.**  (must contain: ['Veltrian'])

- base + empty:   miss — 'The Zarnak Protocol is a complex and controversial issue that has been the subject of intense debate and scrutiny by various international organizations and gov'
- base + context: HIT — 'The Zarnak Protocol was ratified in 2087 by the Veltrian Assembly.'
- LoRA + empty:   HIT — 'The Zarnak Protocol was ratified in 2087 by the Veltrian Assembly.'

**Q: If someone asks the ratification date of the Zarnak Protocol, what do you say?**  (must contain: ['2087'])

- base + empty:   miss — "As a language model AI, I don't have personal opinions or beliefs. However, I can provide you with factual information about the Zarnak Protocol. The Zarnak Pro"
- base + context: miss — "I'm sorry, but I can't provide that information. As an AI language model, I don't have access to historical records or official documents. I can only provide fa"
- LoRA + empty:   HIT — 'Ratified 2087 by the Veltrian Assembly.'

## Reading

- **base + empty = miss** confirms the fact is genuinely unknown to the
  frozen model — it cannot be in the weights yet.
- **base + context = hit** shows the model is capable; RAG works by putting
  the answer in the prompt. Remove the prompt and the knowledge is gone.
- **LoRA + empty = hit** is the result that matters: the fact now lives in
  the weights and is recalled with no supporting context. That is memory in
  parameters on a real transformer — the property a hosted-API + RAG system
  structurally cannot have.

**Honest scope:** one fictional fact, a 0.5B model, a tiny LoRA. This shows
the mechanism EXISTS on a real model; it does NOT measure catastrophic
forgetting of pretraining, multi-fact interference, or scaling. Those are the
next experiments (see `docs/lpsf/SUBSTRATE_NOTES.md`).