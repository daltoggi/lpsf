"""Safety: no module under src/lpsf/experiments/ may import network/LLM libs
or reference catalog-engine or 2nd brain paths.

Exception: codex_llm.py is allowed to use subprocess (it wraps the BARD
call-model.sh script). Python network libraries (requests/httpx/anthropic/
openai/urllib.request) remain forbidden everywhere.
"""

import os
import pathlib


FORBIDDEN_TOKENS_EVERYWHERE = [
    "import requests",
    "import httpx",
    "from requests",
    "from httpx",
    "import urllib.request",
    "from urllib.request",
    "import socket",
    "from socket",
    "catalog_engine",
    "/2nd brain/",
    "second_brain",
]

# Per-file exceptions: certain network/SDK imports are allowed in specific
# wrappers only. This keeps the blast radius tight.
ANTHROPIC_ALLOWED_FILES = {"claude_llm.py"}
OPENAI_ALLOWED_FILES = {"openai_llm.py"}
SUBPROCESS_ALLOWED_FILES = {"codex_llm.py"}

ANTHROPIC_TOKENS = ["import anthropic", "from anthropic"]
OPENAI_TOKENS = ["import openai", "from openai"]
SUBPROCESS_TOKENS = ["subprocess.run", "subprocess.Popen", "os.system"]


def _experiments_root():
    here = pathlib.Path(__file__).resolve()
    return here.parents[2] / "src" / "lpsf" / "experiments"


def _check_file_tokens(path, text, tokens, allowed_files, offenders):
    if path.name in allowed_files:
        return
    for token in tokens:
        if token in text:
            offenders.append((str(path), token))


def test_no_forbidden_tokens_in_experiments_source():
    root = _experiments_root()
    assert root.is_dir(), f"Missing experiments dir: {root}"
    offenders = []
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_TOKENS_EVERYWHERE:
            if token in text:
                offenders.append((str(path), token))
        _check_file_tokens(path, text, ANTHROPIC_TOKENS, ANTHROPIC_ALLOWED_FILES, offenders)
        _check_file_tokens(path, text, OPENAI_TOKENS, OPENAI_ALLOWED_FILES, offenders)
        _check_file_tokens(path, text, SUBPROCESS_TOKENS, SUBPROCESS_ALLOWED_FILES, offenders)
    assert not offenders, f"Forbidden tokens found: {offenders}"


def test_experiments_package_imports_clean():
    # Importing the package must not eagerly pull in anthropic/openai SDKs.
    # Those are only imported when the user instantiates ClaudeLLM/OpenAILLM.
    import importlib, sys
    for mod in (
        "lpsf.experiments",
        "lpsf.experiments.mock_llm",
        "lpsf.experiments.mock_rag",
        "lpsf.experiments.runner",
        "lpsf.experiments.baselines",
        "lpsf.experiments.scoring",
        "lpsf.experiments.scenarios",
        "lpsf.experiments.hypotheses",
        "lpsf.experiments.codex_llm",
        "lpsf.experiments.cost",
        "lpsf.experiments.benchmark",
        "lpsf.experiments.report",
    ):
        importlib.import_module(mod)


def test_anthropic_only_imported_via_claude_llm():
    """anthropic must not be loaded by simply importing lpsf.experiments."""
    import importlib
    import sys
    # Drop any pre-loaded anthropic if a previous test imported claude_llm
    for key in list(sys.modules):
        if key == "anthropic" or key.startswith("anthropic."):
            del sys.modules[key]
        if key.startswith("lpsf.experiments.claude_llm"):
            del sys.modules[key]
    importlib.import_module("lpsf.experiments")
    assert "anthropic" not in sys.modules, (
        "anthropic was eagerly imported by lpsf.experiments"
    )


def test_openai_only_imported_via_openai_llm():
    """openai must not be loaded by simply importing lpsf.experiments."""
    import importlib
    import sys
    for key in list(sys.modules):
        if key == "openai" or key.startswith("openai."):
            del sys.modules[key]
        if key.startswith("lpsf.experiments.openai_llm"):
            del sys.modules[key]
    importlib.import_module("lpsf.experiments")
    assert "openai" not in sys.modules, (
        "openai was eagerly imported by lpsf.experiments"
    )
