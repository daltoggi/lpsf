"""Tests for CodexLLM (M4 Phase 2 wrapper).

Most tests monkeypatch subprocess to keep the suite fast and offline. One
real-subprocess smoke test runs only if Codex CLI is actually available,
and it caches aggressively to keep total runtime under 60s on first run.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from lpsf.experiments import codex_llm as codex_mod
from lpsf.experiments.codex_llm import CodexLLM


# ---------- unit tests (subprocess monkeypatched) ----------------------

@pytest.fixture
def tmp_cache(tmp_path):
    return tmp_path / "codex_cache"


def _fake_runner(responses):
    """Build a fake subprocess.run that emits successive responses to the
    output file. responses is a list of strings used in order."""
    state = {"idx": 0}

    def fake_run(cmd, capture_output, text, timeout, check):
        i = state["idx"]
        if i >= len(responses):
            i = len(responses) - 1
        state["idx"] += 1
        Path(cmd[-1]).write_text(responses[i], encoding="utf-8")
        return MagicMock(returncode=0, stderr="", stdout="ok")

    return fake_run, state


def test_version_includes_codex(tmp_cache):
    llm = CodexLLM(cache_dir=str(tmp_cache))
    assert "codex" in llm.version().lower()


def test_is_available_missing_script():
    assert CodexLLM.is_available(script_path="/nonexistent/script.sh") is False


def test_complete_returns_expected_shape(monkeypatch, tmp_cache):
    fake_run, _ = _fake_runner(["hello from codex"])
    monkeypatch.setattr(codex_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(CodexLLM, "is_available", classmethod(lambda cls, p=None: True))

    llm = CodexLLM(cache_dir=str(tmp_cache))
    out = llm.complete("any prompt", context={"phase": "test"})

    assert set(out.keys()) == {"response", "confidence", "evidence_refs", "model"}
    assert out["response"] == "hello from codex"
    assert out["model"] == llm.version()
    assert out["evidence_refs"] == []


def test_cache_hit_skips_subprocess(monkeypatch, tmp_cache):
    fake_run, state = _fake_runner(["resp-1", "resp-2"])
    monkeypatch.setattr(codex_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(CodexLLM, "is_available", classmethod(lambda cls, p=None: True))

    llm = CodexLLM(cache_dir=str(tmp_cache))
    a = llm.complete("same prompt", context={"k": "v"})
    b = llm.complete("same prompt", context={"k": "v"})

    assert a == b
    assert state["idx"] == 1  # only one subprocess invocation
    assert llm.stats() == {"calls": 1, "cache_hits": 1}


def test_different_context_triggers_new_call(monkeypatch, tmp_cache):
    fake_run, state = _fake_runner(["resp-A", "resp-B"])
    monkeypatch.setattr(codex_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(CodexLLM, "is_available", classmethod(lambda cls, p=None: True))

    llm = CodexLLM(cache_dir=str(tmp_cache))
    a = llm.complete("p", context={"x": 1})
    b = llm.complete("p", context={"x": 2})

    assert a["response"] == "resp-A"
    assert b["response"] == "resp-B"
    assert state["idx"] == 2
    assert llm.stats()["calls"] == 2


def test_cache_persists_across_instances(monkeypatch, tmp_cache):
    fake_run, state = _fake_runner(["resp-first", "resp-second"])
    monkeypatch.setattr(codex_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(CodexLLM, "is_available", classmethod(lambda cls, p=None: True))

    llm1 = CodexLLM(cache_dir=str(tmp_cache))
    llm1.complete("p", context={})

    llm2 = CodexLLM(cache_dir=str(tmp_cache))
    out = llm2.complete("p", context={})

    assert out["response"] == "resp-first"
    assert state["idx"] == 1


def test_unavailable_script_raises(monkeypatch, tmp_cache):
    monkeypatch.setattr(CodexLLM, "is_available", classmethod(lambda cls, p=None: False))
    llm = CodexLLM(cache_dir=str(tmp_cache), script_path="/no/such/script")
    with pytest.raises(RuntimeError):
        llm.complete("prompt", context={})


def test_subprocess_failure_with_empty_output_raises(monkeypatch, tmp_cache):
    def fake_run(cmd, capture_output, text, timeout, check):
        return MagicMock(returncode=1, stderr="codex failed", stdout="")

    monkeypatch.setattr(codex_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(CodexLLM, "is_available", classmethod(lambda cls, p=None: True))

    llm = CodexLLM(cache_dir=str(tmp_cache))
    with pytest.raises(RuntimeError):
        llm.complete("p", context={})


def test_codex_llm_satisfies_mock_llm_surface(monkeypatch, tmp_cache):
    """CodexLLM and MockLLM must be drop-in interchangeable."""
    fake_run, _ = _fake_runner(["any"])
    monkeypatch.setattr(codex_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(CodexLLM, "is_available", classmethod(lambda cls, p=None: True))

    llm = CodexLLM(cache_dir=str(tmp_cache))
    assert callable(llm.version)
    assert callable(llm.complete)
    out = llm.complete("p", context={})
    # Same keys MockLLM returns
    from lpsf.experiments.mock_llm import MockLLM
    mock_out = MockLLM().complete("p")
    assert set(out.keys()) == set(mock_out.keys())


# ---------- integration: runner uses CodexLLM end-to-end ----------------

def test_run_query_with_codex_llm(monkeypatch, tmp_cache, conn, snapshot_id, mock_rag):
    fake_run, _ = _fake_runner(["codex selected answer"])
    monkeypatch.setattr(codex_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(CodexLLM, "is_available", classmethod(lambda cls, p=None: True))

    from lpsf.experiments.runner import run_query

    llm = CodexLLM(cache_dir=str(tmp_cache))
    out = run_query(
        conn,
        query="best path?",
        query_id="codex_int",
        snapshot_id=snapshot_id,
        baseline_name="LLMPlusLPSF",
        llm=llm,
        rag=mock_rag,
    )
    assert out["response"].model_version == llm.version()
    # collapse_trace written
    row = conn.execute(
        "SELECT * FROM collapse_traces WHERE trace_id = ?",
        (out["collapse_trace_id"],),
    ).fetchone()
    assert row is not None


# ---------- real subprocess smoke (skipped when unavailable) -----------

@pytest.mark.skipif(
    not CodexLLM.is_available(),
    reason="Codex CLI / bard-harness not available",
)
def test_codex_real_call_smoke(tmp_cache):
    """One real Codex call. Aggressively cached; subsequent runs are free."""
    llm = CodexLLM(cache_dir=str(tmp_cache), timeout=180)
    out = llm.complete(
        "Reply with exactly one word: PONG",
        context={"lpsf_test": "smoke"},
    )
    assert out["response"], "Codex returned empty response"
    # Don't assert on exact content (LLMs vary); just confirm something came back
    assert isinstance(out["response"], str)
    assert llm.stats()["calls"] >= 1
