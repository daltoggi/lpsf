# Posting kit — public channels for the LPSF write-up

Ready-to-paste copy for the two public channels, in EV order. The essay itself
lives at `lpsf_journey.md`; this file adds the channel-specific framing
(LessWrong header conventions, an X/Twitter thread) and a posting checklist.
All claims here are reproduced from the repo's experiment reports.

---

## 1. LessWrong / Alignment Forum (highest EV — post FIRST)

Post the full essay (`lpsf_journey.md`), but prepend this header. LW readers
expect a TL;DR and an epistemic-status line up top, and they reward honesty
about scope far more than hype.

> **TL;DR.** I reimplemented Contrastive Activation Addition on a 0.5B local
> model while chasing "can an LLM remember instead of re-read," and hit a clean
> composition limit: adding k steering vectors after mean-centering forces their
> average pairwise cosine to exactly **−1/(k−1)**, so you overshoot orthogonality
> into anti-correlation — and that's the same Σ=0 constraint that makes Grover's
> diffusion benign only at large N. cos≈0 (via Gram-Schmidt) turns out necessary
> but not sufficient for composing concepts, because it's order-dependent. Below
> is the full honest arc and the negative results that triangulated it.
>
> **Epistemic status:** hands-on, reproduced-not-novel, 0.5B, keyword metrics,
> ~$1 total. I state every "what is NOT proven" explicitly. Genuinely asking
> whether the −1/(k−1) composition floor is already folklore — pointers welcome.

Then paste the essay body. Title options:
- "A −1/(k−1) limit on composing steering vectors (and why it's Grover's large-N
  assumption in disguise)"
- "I tried to give a 0.5B model real memory. I failed precisely — three times."

Tags: `Activation Engineering`, `Interpretability (ML & AI)`, `AI`.

Why LW first: Rimsky, Turner (TurnTrout), and Neel Nanda's circle read this forum;
the CAA paper itself was first written up here. The result belongs in this room.

---

## 2. X / Twitter thread (cross-post AFTER the LW post exists, link to it)

Keep it 5 tweets, one image (the steering dose-response or the cosine table),
one tag at most. No thread-bait.

**1/**
I spent a while on a dumb-sounding question: can a small LLM *remember* instead
of re-reading its context every time? Frozen 0.5B, on my laptop, ~$1 total.
It failed in three precise ways — and the third is the interesting one. 🧵

**2/**
Memory that lives in the *state*, not the prompt. Two routes:
• weights (LoRA): taught 1 fake fact → recalls with empty context (0→1.00). Taught
a 2nd → erased the 1st. last-write-wins.
• activations (steering, a CAA reimpl): graded, reversible, control-clean.

**3/**
Steering two concepts at once washed out. Why? The contrastive vectors shared a
big common component (cos +0.73); adding them amplified the shared junk.
"Just mean-center them," I thought. It failed — for a fixed reason 👇

**4/**
Mean-centering k vectors forces Σ=0, which forces their average pairwise cosine
to exactly **−1/(k−1)**. k=3 → −0.5 (measured −0.50). You can't center your way
to orthogonality with few concepts; you overshoot into anti-correlation.
This is *why Grover's diffusion is benign only at large N* — same constraint, ÷N.

**5/**
(The −1/(k−1) identity is trivial — the point is the *practical* upshot: naive
contrastive / mean-centered steering vectors can't compose at small k.)
Gram-Schmidt hits cos=0 and composition *still* fails (order-dependent). cos≈0 is
necessary, not sufficient. Full write-up + reproducible code, every "NOT proven"
stated: [LINK TO LW POST]

(Optionally: "@'d nobody on purpose — but if steering-vector folks know whether
the −1/(k−1) floor is already known, I'd love a pointer.")

---

## 3. Posting checklist (you press the buttons)
- [ ] Post the LW essay first; get the URL.
- [ ] Put the LW URL in tweet 5/ and in the Tier-1 cold emails (Draft A).
- [ ] Attach ONE image to the X thread — regenerate a clean one:
      `python3 scripts/plot_frontier.py` (Unicode heatmap, screenshot it) OR
      paste the steering dose-response table from `ops/lpsf/STEERING.md`.
- [ ] One tag max on X. No "🚨 THREAD" bait. Let the result carry it.
- [ ] Only AFTER the public post exists, send Draft A to Rimsky / Zou (see
      OUTREACH_DRAFTS.md), linking the post — an email to a public artifact reads
      far better than to a bare repo.
- [ ] Do NOT email CEOs. Do NOT mass-send. Reply > reach.
