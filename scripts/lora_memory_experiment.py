#!/usr/bin/env python3
"""LoRA-from-experience: the falsifiable memory test on a REAL model.

The same test as the numpy substrate demo, now on an actual transformer:

    Teach a fictional fact by LoRA fine-tuning. Then ask about it with an
    EMPTY context. If the model answers correctly, the memory is in the
    (LoRA) WEIGHTS — true memory — not in the prompt.

Three probes per held-out question:
    base   + empty context   -> should FAIL (model never saw the fact)
    base   + fact in context -> should PASS (RAG: it just reads the prompt)
    lora   + empty context   -> should PASS (memory is now in the weights)

Run order:
    python3 scripts/lora_data_gen.py
    python3 scripts/lora_memory_experiment.py --stage base
    # train (CLI, separate): mlx_lm lora --train --model ... --data data/lora_fact \\
    #   --adapter-path data/lora_fact/adapter --iters 200 --num-layers -1 ...
    python3 scripts/lora_memory_experiment.py --stage lora

Requires the MLX venv (~/.lpsf-ml-venv). NOT part of pytest (needs a model).
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
OUTPUT = REPO_ROOT / "ops" / "lpsf" / "LORA_MEMORY.md"
MODEL = "mlx-community/Qwen2.5-0.5B-Instruct-4bit"


def _gen(model, tok, question: str, context: str | None, max_tokens: int = 40) -> str:
    from mlx_lm import generate
    msgs = []
    if context:
        msgs.append({"role": "system", "content": f"Reference: {context}"})
    msgs.append({"role": "user", "content": question})
    prompt = tok.apply_chat_template(msgs, add_generation_prompt=True)
    return generate(model, tok, prompt=prompt, max_tokens=max_tokens, verbose=False).strip()


def _hit(answer: str, must: list[str]) -> bool:
    a = answer.lower()
    return all(m.lower() in a for m in must)


def run(stage: str) -> dict:
    from mlx_lm import load

    probe = json.loads((DATA / "probe.json").read_text())
    fact = probe["fact"]
    tests = probe["test"]

    if stage == "base":
        model, tok = load(MODEL)
        rows = []
        for t in tests:
            empty = _gen(model, tok, t["q"], None)
            withctx = _gen(model, tok, t["q"], fact)
            rows.append({
                "q": t["q"], "must": t["must"],
                "base_empty": empty, "base_empty_hit": _hit(empty, t["must"]),
                "base_rag": withctx, "base_rag_hit": _hit(withctx, t["must"]),
            })
        return {"stage": "base", "rows": rows}

    if stage == "lora":
        if not ADAPTER.exists():
            print(f"ERROR: no adapter at {ADAPTER}. Train first with mlx_lm lora.")
            sys.exit(1)
        model, tok = load(MODEL, adapter_path=str(ADAPTER))
        rows = []
        for t in tests:
            empty = _gen(model, tok, t["q"], None)
            rows.append({
                "q": t["q"], "must": t["must"],
                "lora_empty": empty, "lora_empty_hit": _hit(empty, t["must"]),
            })
        return {"stage": "lora", "rows": rows}

    raise ValueError(stage)


def write_report(base: dict, lora: dict) -> None:
    bmap = {r["q"]: r for r in base["rows"]}
    lmap = {r["q"]: r for r in lora["rows"]}
    qs = list(bmap)

    base_empty_acc = sum(bmap[q]["base_empty_hit"] for q in qs) / len(qs)
    base_rag_acc = sum(bmap[q]["base_rag_hit"] for q in qs) / len(qs)
    lora_empty_acc = sum(lmap[q]["lora_empty_hit"] for q in qs) / len(qs)

    L = [
        "# LoRA-from-Experience — the memory test on a real model",
        "",
        f"_Generated {datetime.datetime.utcnow().replace(microsecond=0).isoformat()}Z_  ",
        f"_Model: {MODEL} (MLX, Apple Silicon). Fictional fact taught by LoRA._",
        "",
        "## The test",
        "",
        "Same falsifiable question as the numpy substrate demo, on a real",
        "transformer: after teaching a fictional fact by LoRA, can the model",
        "recall it with an **empty context**? If yes, the memory is in the",
        "(LoRA) weights — not the prompt.",
        "",
        "## Accuracy (held-out phrasings, disjoint from training)",
        "",
        "| Condition | recall |",
        "|---|---:|",
        f"| base model, empty context | {base_empty_acc:.2f} |",
        f"| base model, fact in context (RAG) | {base_rag_acc:.2f} |",
        f"| **LoRA model, empty context** | **{lora_empty_acc:.2f}** |",
        "",
        "## Per-question transcript",
        "",
    ]
    for q in qs:
        b = bmap[q]
        l = lmap[q]
        L += [
            f"**Q: {q}**  (must contain: {b['must']})",
            "",
            f"- base + empty:   {'HIT' if b['base_empty_hit'] else 'miss'} — {b['base_empty'][:160]!r}",
            f"- base + context: {'HIT' if b['base_rag_hit'] else 'miss'} — {b['base_rag'][:160]!r}",
            f"- LoRA + empty:   {'HIT' if l['lora_empty_hit'] else 'miss'} — {l['lora_empty'][:160]!r}",
            "",
        ]
    L += [
        "## Reading",
        "",
        "- **base + empty = miss** confirms the fact is genuinely unknown to the",
        "  frozen model — it cannot be in the weights yet.",
        "- **base + context = hit** shows the model is capable; RAG works by putting",
        "  the answer in the prompt. Remove the prompt and the knowledge is gone.",
        "- **LoRA + empty = hit** is the result that matters: the fact now lives in",
        "  the weights and is recalled with no supporting context. That is memory in",
        "  parameters on a real transformer — the property a hosted-API + RAG system",
        "  structurally cannot have.",
        "",
        "**Honest scope:** one fictional fact, a 0.5B model, a tiny LoRA. This shows",
        "the mechanism EXISTS on a real model; it does NOT measure catastrophic",
        "forgetting of pretraining, multi-fact interference, or scaling. Those are the",
        "next experiments (see `docs/lpsf/SUBSTRATE_NOTES.md`).",
    ]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(L), encoding="utf-8")
    print(f"Report: {OUTPUT}")
    print(f"base empty={base_empty_acc:.2f}  base+RAG={base_rag_acc:.2f}  LoRA empty={lora_empty_acc:.2f}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["base", "lora", "report"], required=True)
    args = parser.parse_args()

    if args.stage in ("base", "lora"):
        result = run(args.stage)
        (DATA / f"_result_{args.stage}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        for r in result["rows"]:
            print(json.dumps(r, ensure_ascii=False))
    else:  # report
        base = json.loads((DATA / "_result_base.json").read_text())
        lora = json.loads((DATA / "_result_lora.json").read_text())
        write_report(base, lora)


if __name__ == "__main__":
    main()
