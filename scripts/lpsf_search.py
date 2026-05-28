#!/usr/bin/env python3
"""lpsf-search — a personalizing search CLI built on LPSF.

This is the "framework → tool" step. Each `pick` deepens an attractor, so
repeated use personalizes future `search` rankings. State persists on disk.

Subcommands:
    search <query>                 Show ranked results for a query.
    pick <evidence_id> -q <query>  Record a selection (deepens its attractor).
    why <query>                    Show the score breakdown (rag + attractor).
    reset                          Wipe the personalization state DB.

Index sources:
    (default)        the demo corpus at data/corpus.fts.db
    --brain          a brain-backroom-style FTS index from LPSF_BRAIN_FTS
    --index PATH     an explicit FTS index path

Reranking:
    --rerank         use the LLM judge channel (needs ANTHROPIC_API_KEY).
                     Default off → $0, deterministic, RAG + attractors only.

Examples:
    python3 scripts/lpsf_search.py search "local data storage"
    python3 scripts/lpsf_search.py pick 01_sqlite_for_apps -q "local data storage"
    python3 scripts/lpsf_search.py search "local data storage"   # sqlite now higher
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

DEFAULT_CORPUS = REPO_ROOT / "data" / "corpus.fts.db"
DEFAULT_STATE = Path(
    os.environ.get(
        "LPSF_STATE_DB",
        str(Path.home() / ".local" / "share" / "lpsf" / "personalization.db"),
    )
)


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if not os.environ.get(k.strip()):
            os.environ[k.strip()] = v.strip()


def resolve_index(args) -> str:
    if args.index:
        return args.index
    if args.brain:
        path = os.environ.get("LPSF_BRAIN_FTS", "")
        if not path:
            print("ERROR: --brain set but LPSF_BRAIN_FTS is empty.")
            sys.exit(1)
        return path
    return str(DEFAULT_CORPUS)


def make_session(args, *, use_rerank: bool = False):
    index = resolve_index(args)
    if not Path(index).exists():
        print(f"ERROR: index not found at {index}")
        if index == str(DEFAULT_CORPUS):
            print("Hint: build it with `python3 scripts/build_corpus.py`")
        sys.exit(1)

    from lpsf.app import LPSFSearchSession

    # Choose adapter: brain index uses the sensitivity-gated adapter.
    if args.brain:
        from lpsf.experiments.brain_backroom_rag import BrainBackroomRag
        rag = BrainBackroomRag(db_path=index, snapshot_id="app_v1")
    else:
        from lpsf.experiments.local_fts_rag import LocalFTSRag
        rag = LocalFTSRag(db_path=index, snapshot_id="app_v1")

    llm = None
    judge_llm = None
    if use_rerank:
        load_dotenv(REPO_ROOT / ".env.local")
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("ERROR: --rerank needs ANTHROPIC_API_KEY (env or .env.local)")
            sys.exit(1)
        from lpsf.experiments.claude_llm import ClaudeLLM
        from lpsf.experiments.prompts import PAIRWISE_JUDGE_PROMPT
        llm = ClaudeLLM(model=args.model, temperature=0.0)
        judge_llm = ClaudeLLM(
            model=args.model, temperature=0.0,
            system_prompt=PAIRWISE_JUDGE_PROMPT,
        )
    else:
        from lpsf.experiments.mock_llm import MockLLM
        llm = MockLLM(seed=0)

    state_path = Path(args.state)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    return LPSFSearchSession(
        state_db_path=str(state_path),
        rag=rag,
        llm=llm,
        judge_llm=judge_llm,
        use_rerank=use_rerank,
    )


def _print_results(results) -> None:
    if not results:
        print("(no results)")
        return
    print(f"{'#':>2}  {'id':28} {'amp':>7} {'rag':>6} {'attr':>6} {'picks':>5}  summary")
    print("-" * 100)
    for r in results:
        summary = (r.summary[:48] + "…") if len(r.summary) > 49 else r.summary
        marker = " ←picked" if r.picked_before else ""
        print(
            f"{r.rank:>2}  {r.evidence_id:28} {r.amplitude:>7.3f} {r.rag_score:>6.3f} "
            f"{r.attractor_depth:>6.3f} {r.picked_before:>5}  {summary}{marker}"
        )


def cmd_search(args) -> None:
    sess = make_session(args, use_rerank=args.rerank)
    try:
        results = sess.search(args.query, limit=args.limit)
        print(f'\nQuery: "{args.query}"  (index: {resolve_index(args)})\n')
        _print_results(results)
        print()
    finally:
        sess.close()


def cmd_pick(args) -> None:
    sess = make_session(args, use_rerank=False)
    try:
        out = sess.record_pick(args.evidence_id, query=args.query or "")
        delta = out["delta"]
        before = delta.get("before_depth", "?")
        after = delta.get("after_depth", "?")
        print(
            f'Recorded pick: {out["path"]}  (event {out["event_id"]})\n'
            f'  attractor depth {before} → {after}'
        )
    finally:
        sess.close()


def cmd_why(args) -> None:
    sess = make_session(args, use_rerank=args.rerank)
    try:
        results = sess.search(args.query, limit=args.limit)
        print(f'\nScore breakdown for "{args.query}":\n')
        for r in results:
            print(
                f"  #{r.rank} {r.evidence_id}\n"
                f"      amplitude = rag({r.rag_score:.3f}) + attractor({r.attractor_depth:.3f}) "
                f"= {r.amplitude:.3f}   [picked {r.picked_before}x]"
            )
        print()
    finally:
        sess.close()


def cmd_reset(args) -> None:
    state_path = Path(args.state)
    if state_path.exists():
        state_path.unlink()
        print(f"Wiped personalization state: {state_path}")
    else:
        print(f"No state to wipe at {state_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="LPSF personalizing search CLI")
    parser.add_argument("--state", default=str(DEFAULT_STATE), help="personalization state DB path")
    parser.add_argument("--index", default="", help="explicit FTS index path")
    parser.add_argument("--brain", action="store_true", help="use LPSF_BRAIN_FTS (sensitivity-gated)")
    parser.add_argument("--rerank", action="store_true", help="enable LLM-judge reranking (needs API key)")
    parser.add_argument("--model", default="claude-haiku-4-5")
    parser.add_argument("--limit", type=int, default=5)

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_search = sub.add_parser("search", help="rank results for a query")
    p_search.add_argument("query")
    p_search.set_defaults(func=cmd_search)

    p_pick = sub.add_parser("pick", help="record a selection (deepens its attractor)")
    p_pick.add_argument("evidence_id")
    p_pick.add_argument("-q", "--query", default="", help="the query this pick answered")
    p_pick.set_defaults(func=cmd_pick)

    p_why = sub.add_parser("why", help="show score breakdown")
    p_why.add_argument("query")
    p_why.set_defaults(func=cmd_why)

    p_reset = sub.add_parser("reset", help="wipe personalization state")
    p_reset.set_defaults(func=cmd_reset)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
