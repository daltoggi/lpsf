# Substrate Capacity Scaling

_Generated 2026-05-28T16:55:21Z_  
_numpy demo; capacity = max #facts with empty-context recall ≥ 0.9; max tested 200; $0_

## Capacity vs fixed dimension

| dim | dense Hebbian | sparse Hebbian | expandable |
|---:|---:|---:|:--:|
| 16 | 10 | 200 | ≥ 200 |
| 32 | 26 | 200 | ≥ 200 |
| 64 | 98 | 200 | ≥ 200 |
| 128 | 200 | 200 | ≥ 200 |

## Capacity / dim (is it linear in the fixed dimension?)

| dim | dense cap/dim | sparse cap/dim |
|---:|---:|---:|
| 16 | 0.62 | 12.50 |
| 32 | 0.81 | 6.25 |
| 64 | 1.53 | 3.12 |
| 128 | 1.56 | 1.56 |

## What this says (read with the censoring caveat below)

- **Dense Hebbian capacity rises sharply with the fixed dimension** (e.g. dim 16→64 took capacity ~10→~98 in this run). It is strongly dimension-bound: a smaller fixed dimension stores fewer facts before crosstalk destroys recall.
- **Sparse k-winner coding lifts capacity far above dense** at the same core dimension — near-orthogonal codes cut crosstalk. In this run it exceeded the test ceiling (200) at every dimension, so its true capacity here is only a lower bound.
- **Expandable memory is dimension-independent by construction.** It holds every fact (≥ 200) at any dimension because it appends a slot per fact; its cost is parameter count (linear in #facts), not accuracy.

Qualitative takeaway (what the data supports): in a **fixed** representational dimension, associative capacity is bounded and grows with the dimension; smarter coding raises that bound substantially but does not make it infinite; only **growing the substrate** removes the dependence on the fixed dimension. That is the concrete form of the reframed goal — escaping 'search within a fixed 12288-dim space'.

**Caveats (honest):**
- Capacities that reach 200 are **censored** (true value is ≥ that; raise `--max-facts` to measure it). So precise scaling exponents are NOT claimed here — only the ordering dense ≪ sparse ≪ expandable and the dim-dependence of the bounded ones.
- This is a numpy associative-memory demo, **not a transformer**. It characterizes these specific mechanisms' storage behavior, not attention models. See `docs/lpsf/SUBSTRATE_NOTES.md`.

Reproduce: `python3 scripts/substrate_capacity.py`  (some cells censored at the ceiling — raise --max-facts)