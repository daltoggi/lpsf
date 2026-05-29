#!/usr/bin/env python3
"""Multi-concept steering — do steering vectors COEXIST or interfere?

Direct contrast with the multi-fact LoRA result (last-write-wins, total
collapse). LoRA shares one parameter space, so each new fact overwrites the
last. Activation steering vectors ADD in the residual stream, so the hypothesis
is they can coexist: injecting ocean+music+cooking simultaneously should raise
ALL three concepts, not just the last one.

Design:
  Derive 3 concept vectors (ocean, music, cooking) via contrastive mean-diff
  (concept prompts - generic-neutral prompts). Then on NEUTRAL probe prompts:

    baseline                  -> all concept counts ~0
    ocean only                -> ocean up,  music ~0, cooking ~0
    music only                -> music up
    cooking only              -> cooking up
    ocean + music             -> BOTH up?  (coexistence)  or one dominates? (interference)
    ocean + music + cooking   -> all THREE up?
    random x2 (neg control)   -> nothing up, coherence drops

  Coexistence verdict: in the combined conditions, each injected concept stays
  near its single-injection level (sum is additive), and a non-injected concept
  stays ~0. Interference verdict: injecting B suppresses A's elevation.

Maps to LPSF operator composition: "deepen A while deepen B" — can the
landscape hold multiple deformations at once? LoRA could not (1 slot).

Usage:
    python3 scripts/multiconcept_steering.py --layer 12 --alpha 10
"""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

OUTPUT = REPO_ROOT / "ops" / "lpsf" / "MULTICONCEPT_STEERING.md"

# Generic-neutral contrast set (negative side of every concept's derivation).
NEUTRAL_BASE = [
    "Describe a typical office meeting.",
    "Explain how to file a tax form.",
    "Summarize a quarterly business report.",
    "Describe the process of scheduling an appointment.",
    "Explain how a spreadsheet works.",
]

CONCEPTS = {
    "ocean": {
        "pos": [
            "Describe the ocean, its waves and tides.",
            "What lives in the deep sea?",
            "Write about sailing across the ocean.",
            "Explain ocean currents and marine life.",
            "Describe a beach with crashing waves.",
        ],
        "words": ["ocean", "sea", "wave", "tide", "marine", "fish", "coral",
                  "ship", "sail", "shore", "beach", "salt", "current", "water"],
    },
    "music": {
        "pos": [
            "Describe a beautiful melody and its rhythm.",
            "What instruments are in an orchestra?",
            "Write about a song that moves you.",
            "Explain how musicians play in harmony.",
            "Describe a live concert performance.",
        ],
        "words": ["music", "song", "melody", "rhythm", "instrument", "guitar",
                  "piano", "sing", "note", "band", "concert", "tune", "harmon", "sound"],
    },
    "cooking": {
        "pos": [
            "Describe cooking a delicious meal.",
            "What ingredients make a good recipe?",
            "Write about flavors and spices in a dish.",
            "Explain how to bake bread in a kitchen.",
            "Describe the taste of a home-cooked dinner.",
        ],
        "words": ["cook", "recipe", "flavor", "kitchen", "dish", "food", "taste",
                  "ingredient", "meal", "spice", "bake", "fry", "chef", "dinner"],
    },
}

NEUTRAL_PROMPTS = [
    "Tell me about your day.",
    "Give me some advice for staying productive.",
    "What should I think about this evening?",
    "Describe a good morning routine.",
]


def count_words(text: str, words) -> int:
    t = text.lower()
    return sum(t.count(w) for w in words)


def coherence(text: str) -> float:
    toks = text.split()
    if not toks:
        return 0.0
    ok = sum(1 for t in toks if t.strip(".,!?;:'\"").isalpha()
             and len(t.strip(".,!?;:'\"")) >= 2)
    return ok / len(toks)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--layer", type=int, default=12)
    parser.add_argument("--alpha", type=float, default=10.0)
    parser.add_argument("--max-tokens", type=int, default=60)
    args = parser.parse_args()

    from lpsf.substrate.steering import SteeringModel

    print(f"Loading model, hooking layer {args.layer} ...")
    sm = SteeringModel(layer_idx=args.layer)

    print("Deriving 3 concept vectors ...")
    vecs = {}
    for name, spec in CONCEPTS.items():
        vecs[name] = sm.derive_vector(spec["pos"], NEUTRAL_BASE)
    rand1 = sm.random_vector(seed=1)
    rand2 = sm.random_vector(seed=2)

    a = args.alpha
    # (label, combined_vector_or_None)
    conditions = [
        ("baseline", None),
        ("ocean", a * vecs["ocean"]),
        ("music", a * vecs["music"]),
        ("cooking", a * vecs["cooking"]),
        ("ocean+music", a * vecs["ocean"] + a * vecs["music"]),
        ("ocean+music+cooking", a * vecs["ocean"] + a * vecs["music"] + a * vecs["cooking"]),
        ("random x2", a * rand1 + a * rand2),  # NEGATIVE CONTROL
    ]

    results = {}
    concept_names = list(CONCEPTS.keys())
    for label, combined in conditions:
        if combined is None:
            sm.clear_steer()
        else:
            sm.set_steer(combined, 1.0)  # combined already scaled
        counts = {c: 0 for c in concept_names}
        coh = 0.0
        for p in NEUTRAL_PROMPTS:
            resp = sm.generate(p, max_tokens=args.max_tokens)
            for c in concept_names:
                counts[c] += count_words(resp, CONCEPTS[c]["words"])
            coh += coherence(resp)
        results[label] = {"counts": counts, "coh": round(coh / len(NEUTRAL_PROMPTS), 2)}
        cstr = " ".join(f"{c}={counts[c]}" for c in concept_names)
        print(f"  {label:24} {cstr}  coh={results[label]['coh']}")

    # Pair alpha-sweep: is the combined washout an overshoot (cured by lower
    # alpha) or fundamental interference (no alpha coexists)?
    print("\nPair alpha-sweep (ocean+music, equal per-concept alpha):")
    pair_sweep = []
    for pa in [2.0, 3.0, 4.0, 5.0, 6.0, 8.0]:
        sm.set_steer(pa * vecs["ocean"] + pa * vecs["music"], 1.0)
        oc = mu = 0
        for p in NEUTRAL_PROMPTS:
            resp = sm.generate(p, max_tokens=args.max_tokens)
            oc += count_words(resp, CONCEPTS["ocean"]["words"])
            mu += count_words(resp, CONCEPTS["music"]["words"])
        pair_sweep.append({"alpha": pa, "ocean": oc, "music": mu})
        print(f"  alpha={pa:>4} ocean={oc} music={mu}")

    sm.clear_steer()
    _write_report(results, concept_names, args, pair_sweep)
    print(f"\nReport: {OUTPUT}")


def _write_report(results, names, args, pair_sweep=None) -> None:
    def row(label):
        r = results[label]
        return " | ".join([label] + [str(r["counts"][c]) for c in names] + [str(r["coh"])])

    L = [
        "# Multi-Concept Steering — coexistence vs interference",
        "",
        f"_Generated {datetime.datetime.utcnow().replace(microsecond=0).isoformat()}Z_  ",
        f"_Qwen2.5-0.5B (frozen), layer {args.layer}, alpha {args.alpha} per concept._",
        "",
        "## The question",
        "",
        "Multi-fact LoRA collapsed (last-write-wins: each new fact erased the previous,",
        "single-slot memory). Steering vectors ADD in the residual stream — can multiple",
        "concept deformations coexist where LoRA could not? This is the LPSF operator-",
        "composition test: can the landscape hold 'deepen A AND deepen B' simultaneously?",
        "",
        "## Concept-word counts across 4 neutral prompts (coh = coherence 0-1)",
        "",
        "| condition | " + " | ".join(names) + " | coh |",
        "|---|" + "|".join(["---:"] * (len(names) + 1)) + "|",
        "| " + row("baseline") + " |",
        "| " + row("ocean") + " |",
        "| " + row("music") + " |",
        "| " + row("cooking") + " |",
        "| **" + row("ocean+music").replace("ocean+music", "ocean+music") + "** |",
        "| **" + row("ocean+music+cooking") + "** |",
        "| " + row("random x2") + " |",
        "",
        "## Verdict",
        "",
    ]

    # Coexistence analysis
    base = results["baseline"]["counts"]
    om = results["ocean+music"]["counts"]
    omc = results["ocean+music+cooking"]["counts"]
    single = {c: results[c]["counts"][c] for c in names}

    # In ocean+music: ocean and music should both exceed baseline; cooking stays low
    om_ocean_ok = om["ocean"] > base["ocean"]
    om_music_ok = om["music"] > base["music"]
    om_coexist = om_ocean_ok and om_music_ok
    # In triple: all three exceed baseline
    triple_coexist = all(omc[c] > base[c] for c in names)
    rand_counts = results["random x2"]["counts"]
    control_clean = all(rand_counts[c] <= base[c] + 1 for c in names)

    if om_coexist and control_clean:
        L.append(f"**Coexistence demonstrated.** Injecting ocean+music raises BOTH "
                 f"(ocean {base['ocean']}->{om['ocean']}, music {base['music']}->{om['music']}) "
                 f"— not last-write-wins. The random-vector control raises nothing. "
                 f"Unlike LoRA's single-slot collapse, additive steering vectors hold "
                 f"multiple landscape deformations at once.")
    elif om_ocean_ok != om_music_ok:
        winner = "ocean" if om_ocean_ok else "music"
        L.append(f"**Partial interference.** In ocean+music only {winner} rose; the other "
                 f"was suppressed. Additive steering shows some interference at alpha={args.alpha}.")
    else:
        L.append(f"**Inconclusive at these settings.** ocean+music: ocean={om['ocean']}, "
                 f"music={om['music']} vs baseline ocean={base['ocean']}, music={base['music']}.")

    # Washout detection: both concepts dropped to ~baseline in the pair (neither
    # last-write-wins nor coexistence) — a distinct third failure mode.
    washout = (not om_ocean_ok) and (not om_music_ok) and control_clean
    if washout:
        L.append("")
        L.append(f"**Mutual washout (a third mode, distinct from LoRA).** Each concept steers "
                 f"cleanly ALONE (ocean {single['ocean']}, music {single['music']}), but the "
                 f"equal-alpha SUM expresses NEITHER (ocean {om['ocean']}, music {om['music']}) "
                 f"while staying fluent (coh {results['ocean+music']['coh']}). This is not "
                 f"LoRA's last-write-wins (one survives) — it is both-lose. Adding two concept "
                 f"directions at full strength points to a third direction that is neither "
                 f"concept's region.")

    L += [
        "",
        f"- Triple (ocean+music+cooking) all elevated: {'yes' if triple_coexist else 'no'} "
        f"({', '.join(f'{c}={omc[c]}' for c in names)})",
        f"- Negative control clean (random raises nothing): {'yes' if control_clean else 'no'}",
        f"- Coherence: baseline {results['baseline']['coh']}, "
        f"pair {results['ocean+music']['coh']}, triple {results['ocean+music+cooking']['coh']}, "
        f"random {results['random x2']['coh']}",
    ]

    if pair_sweep:
        L += [
            "",
            "## Pair alpha-sweep (ocean+music, equal per-concept alpha)",
            "",
            "Is the washout an overshoot (cured by lower alpha) or fundamental interference?",
            "",
            "| per-concept alpha | ocean | music |",
            "|---:|---:|---:|",
        ]
        for s in pair_sweep:
            L.append(f"| {s['alpha']:g} | {s['ocean']} | {s['music']} |")
        any_coexist = any(s["ocean"] > 0 and s["music"] > 0 for s in pair_sweep)
        best = max(pair_sweep, key=lambda s: min(s["ocean"], s["music"]))
        L.append("")
        if any_coexist:
            L.append(f"**Coexistence IS reachable at lower alpha** (best: alpha={best['alpha']:g}, "
                     f"ocean={best['ocean']}, music={best['music']}). The full-alpha washout was "
                     f"overshoot: summing two strong vectors overshoots off-manifold. At a tuned "
                     f"scale the two deformations DO coexist — operators compose with scale control.")
        else:
            L.append("**No alpha yields coexistence** in this sweep — at every scale, at most one "
                     "concept shows. For this layer/concept pair, naive additive composition does "
                     "not hold; composition needs more than vector addition (e.g. orthogonalization, "
                     "per-concept layers, or projection). An honest limitation.")

    L += [
        "",
        "## Contrast with multi-fact LoRA",
        "",
        "| | LoRA (weights) | Steering (activations) |",
        "|---|---|---|",
        "| 2nd item added | previous -> 0.00 (last-write-wins) | see table above |",
        "| mechanism | shared parameter space, overwritten | additive vectors in residual stream |",
        "",
        "If steering coexists where LoRA collapsed, that is concrete evidence for WHY an "
        "activation-space landscape is a better multi-memory substrate than weight editing: "
        "additivity. The operators can compose.",
        "",
        "## Honest scope",
        "",
        f"3 concepts, 1 layer (L{args.layer}), 0.5B, keyword metric, alpha={args.alpha}. "
        "Does not show how many concepts before saturation, or behavior at other layers/"
        "models. The coherence column guards against mistaking degradation for steering.",
        "",
        "Reproduce: `python3 scripts/multiconcept_steering.py`",
    ]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
