import importlib
import sys


def test_null_adapter_satisfies_protocol_and_returns_sanitized_empty_results():
    from lpsf.adapter import EvidenceAdapter, NullAdapter

    adapter = NullAdapter()
    assert isinstance(adapter, EvidenceAdapter)
    assert adapter.version() == "null-0"
    assert adapter.allowed_scope() == []
    assert adapter.snapshot_metadata() == {
        "index_metadata": {},
        "source_counts": {},
        "retrieval_parameters": {},
    }
    assert adapter.retrieve("synthetic query", scope=["core"], limit=5) == []
    assert adapter.is_blocked("anything") is False


def test_adapter_import_has_no_external_retrieval_module_side_effect():
    sys.modules.pop("catalog_engine", None)
    importlib.import_module("lpsf.adapter")
    assert "catalog_engine" not in sys.modules
