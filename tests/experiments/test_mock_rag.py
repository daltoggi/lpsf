"""MockRAG Protocol compliance + sanitization tests."""

import pytest

from lpsf.adapter import EvidenceAdapter
from lpsf.experiments.mock_rag import MockRAG


def test_satisfies_evidence_adapter_protocol():
    rag = MockRAG(snapshot_id="snap_x", fixture={})
    assert isinstance(rag, EvidenceAdapter)


def test_retrieve_returns_sanitized_refs_only():
    fixture = {
        "alpha": [
            {
                "id": "ev:1",
                "score": 0.5,
                "sanitized_summary": "summary one",
                "source_type": "synthetic",
                "body": "SENSITIVE_BODY_MUST_NOT_LEAK",
            }
        ]
    }
    rag = MockRAG(snapshot_id="snap_x", fixture=fixture)
    results = rag.retrieve("alpha query", limit=10)
    assert len(results) == 1
    ref = results[0]
    assert ref["id"] == "ev:1"
    assert "body" not in ref
    assert "SENSITIVE_BODY_MUST_NOT_LEAK" not in str(ref)


def test_retrieve_respects_limit():
    fixture = {
        "match": [
            {"id": f"ev:{i}", "score": 1.0 - i * 0.1, "sanitized_summary": "x", "source_type": "synthetic"}
            for i in range(5)
        ]
    }
    rag = MockRAG(snapshot_id="snap_x", fixture=fixture)
    assert len(rag.retrieve("match", limit=2)) == 2


def test_blocked_ids():
    rag = MockRAG(snapshot_id="snap_x", fixture={}, blocked_ids={"blocked:1"})
    assert rag.is_blocked("blocked:1") is True
    assert rag.is_blocked("ev:safe") is False


def test_snapshot_metadata_shape():
    rag = MockRAG(snapshot_id="snap_x", fixture={"a": []})
    meta = rag.snapshot_metadata()
    assert "index_metadata" in meta
    assert "source_counts" in meta
    assert "retrieval_parameters" in meta


def test_version_and_scope():
    rag = MockRAG(snapshot_id="snap_x", fixture={})
    assert rag.version() == "mock-rag-v0"
    assert rag.allowed_scope() == ["synthetic"]
