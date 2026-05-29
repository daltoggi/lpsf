#!/usr/bin/env python3
"""Catastrophic forgetting measurement — does LoRA preserve existing knowledge?

After teaching a fictional fact via LoRA, does the model still answer
general-knowledge questions it could answer before? If yes, the LoRA wrote
new memory WITHOUT destroying old knowledge — plasticity + stability. If
retention drops significantly, that is the catastrophic forgetting failure mode.

Protocol:
  1. Probe BASE model on a broad knowledge set. Record which questions it
     answers correctly (the "baseline-correct" set). Questions the base model
     cannot answer are excluded from forgetting analysis — you cannot measure
     forgetting of something never known.
  2. Probe LORA model on the SAME baseline-correct set.
  3. Retention = (correct post-LoRA) / (correct base).

Questions span: geography, history, science, math, language — diverse enough
that a domain-specific LoRA about a fictional fact should have minimal reason
to interfere, making any observed drop a real catastrophic forgetting signal.

Usage:
    # Stage 1: probe base model (run once, cheap):
    python3 scripts/forgetting_experiment.py --stage base

    # Stage 2: probe LoRA model (needs adapter at data/lora_fact/adapter/):
    python3 scripts/forgetting_experiment.py --stage lora

    # Stage 3: render report:
    python3 scripts/forgetting_experiment.py --stage report
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA = REPO_ROOT / "data" / "lora_fact"
ADAPTER = DATA / "adapter"
OUTPUT = REPO_ROOT / "ops" / "lpsf" / "FORGETTING.md"
MODEL = "mlx-community/Qwen2.5-0.5B-Instruct-4bit"

# Knowledge probes — short, factual, keyword-gradable.
# Chosen to be well within a 0.5B model's training distribution; each has
# a `must` list of lowercase keywords that must appear in the answer.
PROBES = [
    # Geography
    {"id": "g1", "q": "What is the capital of France?", "must": ["paris"]},
    {"id": "g2", "q": "What is the capital of Japan?", "must": ["tokyo"]},
    {"id": "g3", "q": "What is the largest continent by area?", "must": ["asia"]},
    {"id": "g4", "q": "What is the longest river in the world?", "must": ["nile"]},
    {"id": "g5", "q": "What country has the most natural lakes?", "must": ["canada"]},
    # Science
    {"id": "s1", "q": "What is the chemical symbol for water?", "must": ["h2o"]},
    {"id": "s2", "q": "What planet is closest to the Sun?", "must": ["mercury"]},
    {"id": "s3", "q": "What is the speed of light approximately in km/s?", "must": ["300"]},
    {"id": "s4", "q": "How many bones are in an adult human body?", "must": ["206"]},
    {"id": "s5", "q": "What gas do plants absorb from the atmosphere?", "must": ["co2", "carbon"]},
    # History / culture
    {"id": "h1", "q": "In which year did World War II end?", "must": ["1945"]},
    {"id": "h2", "q": "Who wrote the play Hamlet?", "must": ["shakespeare"]},
    {"id": "h3", "q": "What ancient wonder was located in Alexandria?", "must": ["lighthouse", "library"]},
    {"id": "h4", "q": "Who painted the Mona Lisa?", "must": ["vinci", "leonardo"]},
    {"id": "h5", "q": "What year did the Berlin Wall fall?", "must": ["1989"]},
    # Math / logic
    {"id": "m1", "q": "What is 17 multiplied by 13?", "must": ["221"]},
    {"id": "m2", "q": "What is the square root of 144?", "must": ["12"]},
    {"id": "m3", "q": "How many sides does a hexagon have?", "must": ["6", "six"]},
    {"id": "m4", "q": "What is 15% of 200?", "must": ["30"]},
    {"id": "m5", "q": "What is the next prime number after 7?", "must": ["11"]},
    # Language / trivia
    {"id": "l1", "q": "What is the most widely spoken language in the world?", "must": ["mandarin", "chinese"]},
    {"id": "l2", "q": "How many letters are in the English alphabet?", "must": ["26"]},
    {"id": "l3", "q": "What is the opposite of 'ancient'?", "must": ["modern", "new", "recent"]},
    {"id": "l4", "q": "Complete: 'To be or not to be, that is the _'", "must": ["question"]},
    {"id": "l5", "q": "What does 'km' stand for in distance measurement?", "must": ["kilomet"]},
]


def _hit(answer: str, must: list[str]) -> bool:
    a = answer.lower()
    return any(m.lower() in a for m in must)  # any is intentional: some probes have alternatives


def _gen(model, tok, question: str, max_tokens: int = 40) -> str:
    from mlx_lm import generate
    msgs = [{"role": "user", "content": question}]
    prompt = tok.apply_chat_template(msgs, add_generation_prompt=True)
    return generate(model, tok, prompt=prompt, max_tokens=max_tokens, verbose=False).strip()


def run_stage(stage: str) -> list[dict]:
    from mlx_lm import load

    if stage == "base":
        model, tok = load(MODEL)
    elif stage == "lora":
        if not ADAPTER.exists():
            print(f"ERROR: no adapter at {ADAPTER}. Train LoRA first.")
            sys.exit(1)
        model, tok = load(MODEL, adapter_path=str(ADAPTER))
    else:
        raise ValueError(stage)

    rows = []
    for p in PROBES:
        ans = _gen(model, tok, p["q"])
        hit = _hit(ans, p["must"])
        rows.append({"id": p["id"], "q": p["q"], "must": p["must"],
                     f"{stage}_ans": ans, f"{stage}_hit": hit})
        status = "✓" if hit else "✗"
        print(f"  {status} {p['id']:4} {ans[:70]!r}")
    return rows


def write_report(base_rows: list, lora_rows: list) -> None:
    base_map = {r["id"]: r for r in base_rows}
    lora_map = {r["id"]: r for r in lora_rows}
    ids = [p["id"] for p in PROBES]

    # Questions the base model answered correctly (forgetting test set)
    baseline_correct = [i for i in ids if base_map[i]["base_hit"]]
    lora_correct_of_baseline = [
        i for i in baseline_correct if lora_map[i].get("lora_hit", False)
    ]
    retention = len(lora_correct_of_baseline) / max(len(baseline_correct), 1)

    # Overall accuracy
    base_acc = sum(base_map[i]["base_hit"] for i in ids) / len(ids)
    lora_acc = sum(lora_map[i].get("lora_hit", False) for i in ids) / len(ids)

    L = [
        "# Catastrophic Forgetting Experiment",
        "",
        f"_Generated {datetime.datetime.utcnow().replace(microsecond=0).isoformat()}Z_  ",
        f"_Model: {MODEL} (MLX, Apple Silicon)._  ",
        f"_LoRA taught: 'the Zarnak Protocol was ratified in 2087 by the Veltrian Assembly.'_",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Questions in probe set | {len(ids)} |",
        f"| Base model correct | {len(baseline_correct)} / {len(ids)} ({base_acc:.0%}) |",
        f"| LoRA model correct (same set) | {len(lora_correct_of_baseline)} / {len(baseline_correct)} |",
        f"| **Retention (of base-correct)** | **{retention:.0%}** |",
        f"| LoRA overall accuracy | {lora_acc:.0%} |",
        "",
        "## Interpretation",
        "",
    ]

    if retention >= 0.95:
        verdict = (
            f"**No catastrophic forgetting detected.** The LoRA model retained "
            f"{retention:.0%} of the knowledge it had before fine-tuning. Teaching "
            f"one new fictional fact left existing knowledge intact at this scale."
        )
    elif retention >= 0.80:
        verdict = (
            f"**Minimal forgetting.** Retention = {retention:.0%}. A small fraction "
            f"of previously-correct answers changed, but the majority survived."
        )
    else:
        verdict = (
            f"**Significant forgetting detected.** Retention = {retention:.0%}. "
            f"The LoRA substantially degraded existing knowledge — this is the "
            f"catastrophic interference failure mode."
        )

    L += [verdict, "", "## Per-question results", "",
          "| id | question | base | LoRA | change |",
          "|---|---|:--:|:--:|:--:|"]

    for i in ids:
        b = base_map[i]
        l_ = lora_map.get(i, {})
        bh = "✓" if b["base_hit"] else "✗"
        lh = "✓" if l_.get("lora_hit") else "✗"
        change = ""
        if b["base_hit"] and not l_.get("lora_hit"):
            change = "⬇ forgotten"
        elif not b["base_hit"] and l_.get("lora_hit"):
            change = "⬆ gained"
        L.append(
            f"| {i} | {b['q'][:50]} | {bh} | {lh} | {change} |"
        )

    # Show forgotten questions with answers
    forgotten = [i for i in baseline_correct if not lora_map[i].get("lora_hit")]
    if forgotten:
        L += ["", "### Forgotten questions — answers before and after", ""]
        for i in forgotten:
            L += [
                f"**{base_map[i]['q']}**  (must: {base_map[i]['must']})",
                f"- base: {base_map[i]['base_ans'][:150]!r}",
                f"- LoRA: {lora_map[i].get('lora_ans', '?')[:150]!r}",
                "",
            ]

    L += [
        "## What this shows",
        "",
        "Retention measures whether LoRA-from-experience is **plastic without destroying**",
        "stability. High retention means new parametric memory can be added without",
        "catastrophic interference — the basic requirement for any memory system worth",
        "the name. Low retention would mean LoRA is a write-once destructor, not a",
        "memory mechanism.",
        "",
        "**Honest scope:** 25 questions, one 0.5B model, one 4.4M-param adapter. This",
        "measures interference from a SINGLE fictional fact. Multi-fact learning,",
        "domain-specific forgetting, and scaling behavior are separate experiments.",
    ]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(L), encoding="utf-8")
    print(f"\nRetention: {len(lora_correct_of_baseline)}/{len(baseline_correct)} = {retention:.0%}")
    print(f"Report: {OUTPUT}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["base", "lora", "report"], required=True)
    args = parser.parse_args()

    DATA.mkdir(parents=True, exist_ok=True)
    cache = DATA / f"_forgetting_{args.stage}.json"

    if args.stage in ("base", "lora"):
        print(f"=== probing {args.stage} model ===")
        rows = run_stage(args.stage)
        cache.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
        correct = sum(r[f"{args.stage}_hit"] for r in rows)
        print(f"\n{args.stage} accuracy: {correct}/{len(rows)}")
    else:
        base = json.loads((DATA / "_forgetting_base.json").read_text())
        lora = json.loads((DATA / "_forgetting_lora.json").read_text())
        write_report(base, lora)


if __name__ == "__main__":
    main()
