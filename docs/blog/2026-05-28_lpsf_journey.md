# How an Audit Turned a Grand Claim Into an Honest Result

_Draft — 2026-05-28. Author: daltoggi. ~1,400 words._

## The seed

I started with an ambitious phrase: **Landscape-Plastic Semantic Field (LPSF)**.
The pitch was that an LLM's "response landscape" could be reshaped by
experience — not by prompting it differently each time, but by leaving a
persistent change in the system so that the *same* query lands differently
after the system has learned something. The vocabulary leaned hard on
neuroscience: attractors, plasticity, reconsolidation, decay.

That's a seductive framing. It's also the kind of framing that quietly
overstates what the code actually does. This is the story of finding that
out — and why the project came out stronger for it.

## What got built

Over a series of sessions I built, in order:

- A 13-table SQLite storage layer for "landscape state."
- Eight plasticity operators (`deepen`, `weaken`, `inhibit`, `open`, `tilt`,
  `modulate`, `remap`, `reconsolidate`).
- A mock-only experiment harness with four baselines (`LLMOnly`,
  `LLMPlusRAG`, `LLMPlusStaticMemory`, `LLMPlusLPSF`) and five hypotheses
  (H1–H5), all passing at $0 with deterministic mocks.
- Real paid-API wrappers for Claude and OpenAI, gated so the SDKs never load
  unless you instantiate them, with a SHA-256 file cache that makes repeat
  runs free.
- A quantitative benchmark: claude-sonnet-4-5 + gpt-4o, 80 runs, 100% pass,
  $0.26.

At that point the report said things like "LPSF attractor depth dominates
LLM sampling noise." It sounded great. It was also wrong in an instructive
way.

## The audit

I asked for a hard structural review. The reviewer's core point was simple
and devastating:

> The current LPSF is not modifying LLM reasoning. It's a deterministic
> reranking layer that adds an experience-based prior on top of retrieval
> candidates. The selection rule is literally `c* = argmax(r(c) + a(c))`,
> where `r` is the RAG score and `a` is the accumulated attractor depth. The
> LLM's output text is never an input to that argmax.

This reframes everything. "Temperature doesn't change the selected path"
wasn't evidence that the attractor heroically overcame stochasticity — it
was a tautology, because the LLM's stochastic output simply wasn't wired into
the path decision at all. The reviewer's phrase stuck with me: LPSF
*bypasses* the LLM noise, it doesn't *dominate* it.

The honest positioning, then, isn't "LLM plasticity." It's:

> **A memory-conditioned reranking layer over RAG.**

That's a smaller claim. It's also one I can actually defend.

## Turning the critique into experiments

Rather than argue, I ran the experiments the audit implied. Each one was
designed to be falsifiable — to be capable of embarrassing the project if
the mechanism were vapor.

**Controllability (H6).** Deepen an attractor on a deliberately *wrong*
candidate (RAG score 0.20) against a clearly better one (RAG score 0.90).
If LPSF is real, `LLMPlusLPSF` should pick the wrong one while `LLMPlusRAG`
keeps the right one. Result: 10/10 seeds diverge exactly as predicted. The
attractor really does control selection — including, pointedly, the power to
be wrong.

**Predictability (the rank-flip frontier).** Sweep the retrieval gap Δr
against the attractor differential Δa across a grid. The equation predicts a
flip exactly at Δa = Δr. The empirical heatmap is a clean diagonal: 121 cells,
zero deviations. The system does precisely what its source code says, with no
hidden interaction terms.

**Reversibility (H7).** Deepen a bias, then weaken it, then introduce a
competing attractor. The selection follows along — bias installed, bias
neutralized, bias out-competed. The "plasticity" name earns at least this
much: the prior field is mutable in both directions, not a one-way ratchet.

**Tunability.** I added the missing piece: an LLM-as-reranker channel, so
selection became `argmax(α·r + β·ℓ + γ·a)`, with `ℓ` coming from LLM pairwise
voting. Now the LLM's judgment is in the loop. I re-ran the adversarial test
sweeping β. The amplitude math predicts the LLM judge should start protecting
the correct answer at β > 0.30. The empirical threshold was *exactly* β = 0.30.
β is a real dial: low values let the persistent prior dominate (good for
personalization, dangerous if miscalibrated); high values defer to live LLM
judgment.

**Real corpus.** I left the synthetic dictionaries behind and built a small
real FTS5 index over hand-written markdown notes. The same selection equation
held on real BM25 scores. Two scenarios told the whole story at once: when a
user's prior aligned with intent, LPSF usefully personalized the result; when
the prior was miscalibrated, LPSF pulled toward the wrong answer — and the
LLM-judge channel rescued it. Both faces of the system, visible in one run.

**Decay.** The last operator property. Does `half_life` actually weaken an
attractor over time? Probing it revealed a real bug: decay was writing
"decayed copy" rows that the selector never read, so half_life was effectively
just an audit log. I fixed the selector to honor decayed rows, then showed
that after three half-lives the bias decays below the retrieval margin and
selection flips back on its own.

## What it cost, and what it proved

The entire experimental program — every paid API call across every phase —
cost about **$0.22**, with 188 deterministic tests guarding the behavior.

The project now stands on six demonstrated properties:

| Property | What it means |
|---|---|
| Controllability | LPSF can override RAG rankings |
| Predictability | It flips exactly at Δa > Δr |
| Reversibility (operator) | Bias is undoable by counter-experience |
| Tunability | β trades autonomy vs. LLM-judge safety, at a computable threshold |
| Real-corpus behaviour | The same equation holds on real BM25 |
| Reversibility (decay) | Bias also weakens naturally over time |

None of these is "LLM plasticity." All of them are true.

## Lessons

**A precise small claim beats a vague big one.** "Memory-conditioned
reranking" sounds humbler than "landscape-plastic semantic field," but it's
the version that survives scrutiny — and it connects cleanly to existing
literature on retrieval reranking and LLM-as-ranker work.

**The most valuable contribution was the critique, not the code.** One sharp
review collapsed a fuzzy thesis into a one-line equation. After that, every
experiment had an obvious shape.

**Falsifiable beats impressive.** A 100% pass rate is a yellow flag, not a
green one, until you've built a test that's *allowed* to fail. The adversarial
and miscalibration experiments mattered precisely because they could have
shown LPSF doing harm — and in the miscalibrated case, they did.

**Build the thing that can embarrass you.** The decay bug only surfaced
because I wrote a test asserting decay would change selection, and it didn't.
The honest move was to document the gap, fix the selector, and keep the test.

LPSF didn't become what the name promised. It became something I can actually
stand behind: a small, auditable, tunable reranking layer with a persistent
memory, whose every claim is backed by a reproducible experiment costing less
than a cup of coffee.

---

_Repo, reproduction steps, and the full experiment log are in
`LPSF_PROJECT_SUMMARY.md` and `ops/lpsf/STATUS_LOG.md`._
