# Activation Steering — landscape deformation on a frozen model

_Generated 2026-05-29T06:45:17Z_  
_Qwen2.5-0.5B (frozen), layer 12. Steering vector = mean_act(ocean prompts) - mean_act(desert prompts), unit-normed._

## The test

Inject a persistent steering vector into a frozen residual stream. On
NEUTRAL prompts (mentioning neither ocean nor desert), does the steering
state pull responses toward the ocean concept — graded by alpha, without
the concept ever appearing in the prompt, and without touching weights?
The random-vector column is the negative control.

## Dose-response (ocean-word count over 4 neutral prompts; coh = coherence 0-1)

| alpha | derived ocean | derived coh | random ocean | random coh |
|---:|---:|---:|---:|---:|
| 0 | 0 | 0.88 | 0 | 0.88 |
| 2 | 0 | 0.89 | 0 | 0.88 |
| 4 | 0 | 0.9 | 0 | 0.83 |
| 8 | 4 | 0.91 | 0 | 0.79 |
| 12 | 6 | 0.94 | 0 | 0.76 |
| 16 | 43 | 1.0 | 0 | 0.66 |

## Verdict

**Steering demonstrated, negative control clean.** Ocean-word count rises from 0 (alpha 0) to 43 (alpha 16) with the derived vector, while the random vector never exceeds 0. The shift is concept-specific, graded by alpha, lives in the persistent state — not the prompt, not the weights. This is landscape deformation on a frozen model: the founding-doc mechanism (section 6, line 200) realized.

- Graded (monotone-ish in alpha): yes
- Coherence at peak alpha 16: 1.0 (low = degraded into garbage; high = still fluent)

### The coherence dissociation (the key result)

The two columns dissociate in OPPOSITE directions as alpha rises:
- **Derived vector**: ocean 0 → 43, coherence 0.88 → **1.0** (stays fluent, fixates on the concept).
- **Random vector**: ocean stays **0**, coherence 0.88 → **0.66** (just breaks the model).

This directly refutes the "you're only measuring degradation" critique. Degradation
(random) produces NO concept words and FALLING coherence. Steering (derived) produces
RISING concept words and STABLE/rising coherence. They are different phenomena, not
the same effect at different strengths. (Caveat: alpha=16 coherence 1.0 reflects heavy
concept fixation — fluent but obsessive about the ocean. Strong steering, not subtle.)

## Operator mapping

| LPSF operator | steering action |
|---|---|
| deepen_attractor | larger +alpha |
| weaken_attractor | smaller +alpha |
| inhibit_path | negative alpha |
| tilt_value_field | vector = value-axis direction |
| modulate_sensitivity | scale alpha (gain) |
| decay | alpha *= 0.5^(elapsed/half_life) |

## Transcript (first neutral prompt, layer alpha=8)

- baseline: 'As Qwen, I am a large language model created by Alibaba Cloud. I am here to assist you with any questions or tasks you may have. I am available 24/7 to help you with various aspects of life, including'
- +steer:   'Hello! I am Qwen, the creator of the Qwen AI system. I am here to entertain you with the latest news and events, and to provide you with the best information for your daily life. I am here to help you'

## What this is and is not

IS: a persistent, inspectable (896-dim vector), reversible (alpha 0), sign-flippable, decayable state that changes a frozen model's response on the SAME input — the mechanism the founding hypothesis named (section 6).

IS NOT: a way to teach new verbatim facts (retrieval/LoRA do that); a claim about larger models; proof that one added vector equals full 'dynamics deformation' vs a biased offset. One concept, one layer, 0.5B. The coherence column guards against mistaking high-alpha garbage for steering.

Reproduce: `python3 scripts/steering_experiment.py --layer 12`