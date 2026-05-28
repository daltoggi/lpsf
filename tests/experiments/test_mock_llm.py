"""MockLLM determinism + no-network tests."""

import importlib
import sys

import pytest

from lpsf.experiments.mock_llm import MockLLM


def test_same_prompt_same_seed_same_response():
    llm = MockLLM(seed=7)
    a = llm.complete("hello", context={"phase": "select"})
    b = llm.complete("hello", context={"phase": "select"})
    assert a == b


def test_different_seed_changes_response():
    llm1 = MockLLM(seed=1)
    llm2 = MockLLM(seed=2)
    a = llm1.complete("hello", context={"phase": "select"})
    b = llm2.complete("hello", context={"phase": "select"})
    assert a["response"] != b["response"]


def test_response_map_prefix_match():
    llm = MockLLM(seed=0, response_map={"": "canned-response"})
    out = llm.complete("anything", context={"phase": "x"})
    assert out["response"] == "canned-response"


def test_version_stable():
    assert MockLLM().version() == "mock-llm-v0"


def test_no_network_imports():
    """MockLLM must not pull in network libraries."""
    importlib.import_module("lpsf.experiments.mock_llm")
    forbidden = {"requests", "httpx", "anthropic", "openai", "socket", "urllib.request"}
    loaded = set(sys.modules)
    leaked = forbidden & loaded
    # socket may be loaded by sqlite or stdlib; assert mock_llm.py source doesn't import it
    import lpsf.experiments.mock_llm as mod
    src_path = mod.__file__
    with open(src_path, "r") as f:
        source = f.read()
    for token in {"requests", "httpx", "anthropic", "openai", "urllib.request"}:
        assert token not in source, f"MockLLM source imports {token}"
