"""Tests for ClaudeLLM (M4 Phase 3 wrapper). Mocks anthropic client."""

import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def tmp_cache(tmp_path):
    return tmp_path / "claude_cache"


def _fake_anthropic_message(text="hello from claude", input_tokens=120, output_tokens=40, cached_input=0):
    block = SimpleNamespace(type="text", text=text)
    usage = SimpleNamespace(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_input_tokens=cached_input,
    )
    return SimpleNamespace(content=[block], usage=usage)


def _make_llm(tmp_cache, fake_message=None, **kwargs):
    """Construct a ClaudeLLM whose underlying anthropic client is mocked."""
    from lpsf.experiments.claude_llm import ClaudeLLM

    # Set a fake API key so client init doesn't complain
    os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
    llm = ClaudeLLM(cache_dir=str(tmp_cache), **kwargs)
    fake_client = MagicMock()
    fake_client.messages.create.return_value = (
        fake_message or _fake_anthropic_message()
    )
    llm._client = fake_client
    return llm, fake_client


def test_version_returns_model_id(tmp_cache):
    llm, _ = _make_llm(tmp_cache, model="claude-sonnet-4-5")
    assert llm.version() == "claude-sonnet-4-5"


def test_complete_returns_expected_shape(tmp_cache):
    llm, fake_client = _make_llm(tmp_cache)
    out = llm.complete("hello", context={"phase": "x"})
    assert set(out.keys()) == {"response", "confidence", "evidence_refs", "model", "tokens"}
    assert out["response"] == "hello from claude"
    fake_client.messages.create.assert_called_once()


def test_cache_hit_skips_api(tmp_cache):
    llm, fake_client = _make_llm(tmp_cache)
    llm.complete("p", context={"k": 1})
    llm.complete("p", context={"k": 1})
    assert fake_client.messages.create.call_count == 1
    assert llm.usage.cache_hits == 1


def test_token_accounting(tmp_cache):
    llm, _ = _make_llm(
        tmp_cache,
        fake_message=_fake_anthropic_message(input_tokens=200, output_tokens=80),
    )
    llm.complete("p", context={})
    assert llm.usage.input_tokens == 200
    assert llm.usage.output_tokens == 80
    assert llm.usage.calls == 1
    # cost = 200*3/1M + 80*15/1M = 0.0006 + 0.0012 = 0.0018
    assert llm.usage.cost() == pytest.approx(0.0018, rel=1e-3)


def test_cache_hit_does_not_increase_tokens(tmp_cache):
    llm, _ = _make_llm(tmp_cache, fake_message=_fake_anthropic_message(input_tokens=100, output_tokens=50))
    llm.complete("p", context={})
    pre_tokens = llm.usage.input_tokens
    llm.complete("p", context={})
    assert llm.usage.input_tokens == pre_tokens


def test_is_available_reads_env(monkeypatch):
    from lpsf.experiments.claude_llm import ClaudeLLM
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    assert ClaudeLLM.is_available() is True
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert ClaudeLLM.is_available() is False


def test_drop_in_for_mock_llm(tmp_cache):
    """ClaudeLLM and MockLLM expose the same surface."""
    from lpsf.experiments.mock_llm import MockLLM
    llm, _ = _make_llm(tmp_cache)
    mock = MockLLM()
    assert set(llm.complete("p", context={}).keys()) >= set(
        mock.complete("p", context={}).keys()
    )


def test_runner_integration_writes_traces(tmp_cache, conn, snapshot_id, mock_rag):
    llm, _ = _make_llm(tmp_cache)
    from lpsf.experiments.runner import run_query
    out = run_query(
        conn,
        query="best path?",
        query_id="claude_int",
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
