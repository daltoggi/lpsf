# I tried to give an LLM real memory. I failed precisely — and that was the point.

_An honest field report. The code, every experiment, and every "what is NOT
proven" note are public: github.com/daltoggi/lpsf_

## The itch

LLMs don't remember. They re-read. Every session you re-paste who you are,
what you're working on, your preferences — and pay tokens for it, every turn.
"Memory" features mostly re-inject past text into the context window; lossy
compression then loses the meaning you were trying to keep. A human who learns
something doesn't re-read it next time. Their brain changed. That gap is what
I wanted to close.

I gave it a grand name — **Landscape-Plastic Semantic Field** — and a
neuroscience vocabulary: attractors, plasticity, reconsolidation, decay. The
pitch: experience should reshape the model's *response landscape* so the same
input lands differently afterward, without re-reading.

This is the story of discovering exactly how much of that a person can
actually do, where the real frontier is, and one wild intuition that failed
for a reason worth the whole project.

## The reframe (an audit I asked for, and took)

Stripped of the vocabulary, the question is sharp: **does memory live in the
input (re-read) or in the system's state (genuinely changed)?** That split
organizes the entire field:

- **Context management** — keep the model frozen, get smarter about what
  enters the window. This is mem0, MemGPT/Letta, LangMem, hosted "memory."
  It is real and useful and *still re-reading*.
- **State-based** — the model's own state changes with experience. Weights
  (model editing; test-time training) or activations (steering). This is the
  only family that passes the test I came to care about: **recall with an
  empty context.**

My first instinct — a reranking layer that re-weights retrieved candidates —
was honest but shallow: it changes *what is selected*, not the model's
*response*, and it fails the empty-context test. It lives in the crowded
context-management family. So I went down into the state.

## What I measured (on a 0.5B model, on my own machine, for ~$1 total)

**Weights can hold a memory — one.** I taught a frozen Qwen2.5-0.5B a fictional
fact ("the Zarnak Protocol was ratified in 2087…") with a tiny LoRA. Afterward
it recalled the fact with an **empty context** — on phrasings it never saw
(0.00 → 1.00). Memory genuinely entered the parameters. Then I taught a second
fact. The first dropped to **0.00**. A single LoRA adapter is a single-slot
memory: last-write-wins. Unrelated knowledge degraded too, unless explicitly
rehearsed — forgetting in proportion to how much of the old distribution was
absent from the new training (the EWC insight, met by hand).

**Activations can steer it, reversibly.** I built activation steering — and
later realized I had reimplemented **Contrastive Activation Addition** (Rimsky
et al.) almost line for line: a steering vector is the mean activation
difference between positive and negative prompts, added with a coefficient.
On neutral prompts, a "concept" vector pulled the output toward that concept,
**graded by strength** (0 → 43 concept-words), while an equal-norm **random
vector did nothing** (the negative control), and — the detail that matters —
the real vector kept the text *fluent* while the random one *degraded* it.
Steering and breakage are opposite phenomena, not the same effect at different
strengths.

**Two concepts can coexist — in a window.** Where two weight-memories
collapsed (last-write-wins), two steering vectors *added*: at moderate strength
both concepts surfaced; too strong, they washed out. A real difference between
the substrates — additivity — with an honest caveat: only in a window.

## The intuition that failed, and taught the structure

Here is the part I'd show a skeptic. Why does the coexistence window exist?
I assumed the concept vectors were near-orthogonal and the washout was pure
magnitude. **I measured it. I was wrong.** The vectors shared a large common
direction (cosine +0.73) — an artifact of contrasting every concept against
the same generic prompts. Adding two of them *amplified the shared part* and
drowned the specifics. (The classic CAA lesson — a steering vector is only as
clean as its contrast set — rediscovered the hard way.)

Then a friend-of-the-project intuition: *Grover's algorithm amplifies a target
by amplifying its deviation from the mean (sign-flip + reflect-about-the-mean).
So mean-center the concept vectors — steer along `vᵢ − v̄` — and you should
reach the orthogonal sweet spot.*

It's a beautiful idea. I tested it. It failed — and the **reason** is the best
thing in this repo:

> Mean-centering *k* vectors imposes Σ(vᵢ − v̄) = 0. For unit vectors summing
> to zero, the average pairwise cosine is forced to exactly **−1/(k−1)**. For
> k = 3 that is −0.50 — and the measured value was −0.50. You cannot center
> your way to orthogonality with few vectors; you overshoot past orthogonal
> into anti-correlation, which *cancels* the concepts instead of composing them.

And that is **exactly where the quantum analogy breaks — on N.** Grover's
diffusion (reflect about the mean) is benign only because N is enormous: the
sum-to-zero constraint spreads over N states, so each non-target picks up only
~−1/N ≈ 0 correlation. Grover needs large N not just for the √N speedup but for
its diffusion to be non-destructive. At k = 3, the identical operation forces
−0.5 and destroys what you were trying to build. The intuition was
*structurally right* and failed for a precise reason that traces straight back
to the large-N assumption underneath quantum search.

A good intuition, pinned to three lines of linear algebra, failing in a way
that explains itself. That's the moment the project earned its keep.

## Where this sits, honestly

I did not invent anything. The steering is CAA. The weight-memory and
forgetting reproduce known continual-learning behavior. The frontier I kept
rediscovering by hand is real and lab-led: Test-Time Training (Sun et al.;
NVIDIA's TTT-E2E compresses context into weights via meta-learned test-time
updates), model editing (ROME/MEMIT), representation engineering. Those are
the "true memory" direction — and they need pretraining-scale resources and a
lab. A solo project does not overtake them.

What a solo project *can* do, and what this is: a complete, honest,
reproducible pass that places every approach on **one axis** (memory in the
input vs. the state), drives a small operator vocabulary across three
substrates, measures the trade-offs by hand with negative controls, and states
every limitation out loud. 0.5B model, keyword metrics, single concepts. Not a
product. Not SOTA. A map, and a way of thinking.

## What I actually believe now

The substrate you'd want for experience-driven memory is the one that is
integrating **and** inspectable **and** additive at once — i.e. steering-like —
and that this rhymes with where two independent frontiers (TTT's "state is a
learned model," CAA's additive reversible vectors) are heading is the
encouraging part. The itch was right. The dream was the wrong size for one
person. The honest middle — measure the mechanism, find its exact limits, say
what you don't know — was worth seven months and a dollar.

---

_Everything here is reproducible from the repo; the experiment reports under
`ops/lpsf/` include the failures and the "what is NOT proven" sections in full.
Written under a pseudonym; happy to attach a name in the right context._
