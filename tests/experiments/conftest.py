"""Shared fixtures for M4 Phase 1 experiment tests."""

import pytest

from lpsf import db
from lpsf.experiments.scenarios import (
    default_rag_fixture,
    insert_synthetic_event,
    insert_synthetic_snapshot,
)
from lpsf.experiments.mock_llm import MockLLM
from lpsf.experiments.mock_rag import MockRAG


@pytest.fixture
def conn():
    connection = db.init_db(":memory:")
    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture
def snapshot_id(conn):
    return insert_synthetic_snapshot(conn, snapshot_id="snap_exp")


@pytest.fixture
def event_id(conn, snapshot_id):
    return insert_synthetic_event(conn, snapshot_id=snapshot_id, event_id="evt_exp")


@pytest.fixture
def rag_fixture():
    return default_rag_fixture()


@pytest.fixture
def mock_llm():
    return MockLLM(seed=42)


@pytest.fixture
def mock_rag(snapshot_id, rag_fixture):
    return MockRAG(snapshot_id=snapshot_id, fixture=rag_fixture)
