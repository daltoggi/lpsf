"""Tests for OpenAILLM (M4 Phase 3 wrapper). Mocks openai client."""

import os
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def tmp_cache(tmp_path):
    return tmp_path / "openai_cache"


def _fake_openai_completion(
    text="hello from openai",
    prompt_tokens=110,
    completion_tokens=35,
    cached_tokens=0,
):
    message = SimpleNamespace(content=text)
    choice = SimpleNamespace(message=message)
    details = SimpleNamespace(cached_tokens=cached_tokens)
    usage = SimpleNamespace(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        prompt_tokens_details=details,
    )
    return SimpleNamespace(choices=[choice], usage=usage)


def _make_llm(tmp_cache, fake_completion=None, **kwargs):
    from lpsf.experiments.openai_llm import OpenAILLM
    os.environ.setdefault("OPENAI_API_KEY", "test-key")
    llm = OpenAILLM(cache_dir=str(tmp_cache), **kwargs)
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = (
        fake_completion or _fake_openai_completion()
    )
    llm._client = fake_client
    return llm, fake_client


def test_version_returns_model_id(tmp_cache):
    llm, _ = _make_llm(tmp_cache, model="gpt-4o")
    assert llm.version() == "gpt-4o"


def test_complete_returns_expected_shape(tmp_cache):
    llm, fake_client = _make_llm(tmp_cache)
    out = llm.complete("hi", context={"phase": "test"})
    assert set(out.keys()) == {"response", "confidence", "evidence_refs", "model", "tokens"}
    assert out["response"] == "hello from openai"
    fake_client.chat.completions.create.assert_called_once()


def test_cache_hit_skips_api(tmp_cache):
    llm, fake_client = _make_llm(tmp_cache)
    llm.complete("p", context={"k": 1})
    llm.complete("p", context={"k": 1})
    assert fake_client.chat.completions.create.call_count == 1


def test_token_accounting(tmp_cache):
    llm, _ = _make_llm(
        tmp_cache,
        fake_completion=_fake_openai_completion(prompt_tokens=200, completion_tokens=80),
    )
    llm.complete("p", context={})
    # gpt-4o: 200*2.5/1M + 80*10/1M = 0.0005 + 0.0008 = 0.0013
    assert llm.usage.cost() == pytest.approx(0.0013, rel=1e-3)


def test_is_available_reads_env(monkeypatch):
    from lpsf.experiments.openai_llm import OpenAILLM
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    assert OpenAILLM.is_available() is True
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert OpenAILLM.is_available() is False


def test_runner_integration_writes_traces(tmp_cache, conn, snapshot_id, mock_rag):
    llm, _ = _make_llm(tmp_cache)
    from lpsf.experiments.runner import run_query
    out = run_query(
        conn,
        query="best path?",
        query_id="openai_int",
        snapshot_id=snapshot_id,
        baseline_name="LLMPlusLPSF",
        llm=llm,
        rag=mock_rag,
    )
    assert out["response"].model_version == llm.version()
    row = conn.execute(
        "SELECT * FROM collapse_traces WHERE trace_id = ?",
        (out["collapse_trace_id"],),
    ).fetchone()
    assert row is not None
