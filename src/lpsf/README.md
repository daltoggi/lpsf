# LPSF M2 Storage Layer

This package contains only the isolated storage layer for LPSF-v0.1 M2.

Included:

- SQLite schema for the 13 logical records from the frozen spec.
- Connection/schema helpers.
- Plain stdlib dataclasses for schema records.
- Read-only evidence adapter protocol plus `NullAdapter`.
- Snapshot pin, lookup, and drift recording helpers.
- Synthetic pytest coverage for schema invariants, append-only triggers, adapter behavior, model serialization, and snapshot lifecycle.

Not included in M2:

- Plasticity operator implementations.
- Experiment runners.
- LLM calls.
- Evaluation harnesses.
- Any integration that reads local personal knowledge paths.

M3 will implement plasticity operators against this schema after user authorization.

## Import (src-layout)

This package uses src-layout. Pick one:

```bash
# editable install (preferred)
pip install -e .

# or one-shot via PYTHONPATH
PYTHONPATH=src python3 -c "from lpsf import db; db.init_db(':memory:')"

# tests already wire pythonpath via pyproject [tool.pytest.ini_options]
python3 -m pytest tests/ -q
```
