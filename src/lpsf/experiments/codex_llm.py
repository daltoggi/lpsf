"""CodexLLM: real LLM access via Codex CLI for M4 Phase 2.

Drop-in replacement for MockLLM. Uses subprocess to invoke
~/.bard-harness/scripts/call-model.sh codex <prompt> <output_file>.

Cost: $0 per call (ChatGPT Plus OAuth subscription). The cache prevents
duplicate calls across runs; the same (prompt, context, model_id) tuple
resolves to the same cached response forever unless the cache file is
removed.

Subprocess is the ONLY way this module reaches outside the process. There
is no Python network library import. The safety test
`tests/experiments/test_no_external_imports.py` explicitly allows subprocess
in this file.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional


class CodexLLM:
    """ChatGPT-backed LLM via Codex CLI subprocess.

    Identical surface to MockLLM:
        complete(prompt, context=...) -> {response, confidence, evidence_refs, model}
        version() -> str
    """

    DEFAULT_SCRIPT = os.path.expanduser("~/.bard-harness/scripts/call-model.sh")
    DEFAULT_CACHE_DIR = os.path.expanduser("~/.cache/lpsf/codex_llm")

    def __init__(
        self,
        *,
        script_path: Optional[str] = None,
        cache_dir: Optional[str] = None,
        timeout: int = 120,
        model_id: str = "codex-chatgpt-v1",
    ) -> None:
        self._script_path = script_path or self.DEFAULT_SCRIPT
        self._cache_dir = Path(cache_dir or self.DEFAULT_CACHE_DIR)
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            # Cache is best-effort; fall back to a temp dir if home not writable
            self._cache_dir = Path(tempfile.gettempdir()) / "lpsf_codex_cache"
            self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._timeout = timeout
        self._model_id = model_id
        self._call_count = 0
        self._cache_hits = 0

    # ---------- Protocol surface -----------------------------------------

    def version(self) -> str:
        return self._model_id

    def complete(
        self,
        prompt: str,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        key = self._cache_key(prompt, context)
        cached = self._load_cache(key)
        if cached is not None:
            self._cache_hits += 1
            return cached

        if not self.is_available(self._script_path):
            raise RuntimeError(
                f"Codex script unavailable at {self._script_path}; "
                "install ~/.bard-harness or pass script_path=..."
            )

        response_text = self._invoke_subprocess(prompt)

        result: Dict[str, Any] = {
            "response": response_text,
            "confidence": 0.7,
            "evidence_refs": [],
            "model": self._model_id,
        }
        self._save_cache(key, result)
        return result

    # ---------- Diagnostics ----------------------------------------------

    @classmethod
    def is_available(cls, script_path: Optional[str] = None) -> bool:
        path = script_path or cls.DEFAULT_SCRIPT
        return os.path.isfile(path) and os.access(path, os.X_OK)

    def stats(self) -> Dict[str, int]:
        return {"calls": self._call_count, "cache_hits": self._cache_hits}

    # ---------- Internals ------------------------------------------------

    def _invoke_subprocess(self, prompt: str) -> str:
        """Run the call-model.sh script and return the raw response text."""
        fd, output_path = tempfile.mkstemp(suffix=".md", prefix="lpsf_codex_")
        os.close(fd)
        try:
            self._call_count += 1
            proc = subprocess.run(
                ["bash", self._script_path, "codex", prompt, output_path],
                capture_output=True,
                text=True,
                timeout=self._timeout,
                check=False,
            )
            response_text = ""
            if os.path.exists(output_path):
                response_text = (
                    Path(output_path).read_text(encoding="utf-8").strip()
                )
            if proc.returncode != 0 and not response_text:
                raise RuntimeError(
                    f"Codex call failed rc={proc.returncode}; stderr={proc.stderr}"
                )
            return response_text
        finally:
            if os.path.exists(output_path):
                try:
                    os.unlink(output_path)
                except OSError:
                    pass

    def _cache_key(self, prompt: str, context: Optional[Dict[str, Any]]) -> str:
        payload = json.dumps(
            {"prompt": prompt, "context": context, "model": self._model_id},
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _cache_path(self, key: str) -> Path:
        return self._cache_dir / f"{key}.json"

    def _load_cache(self, key: str) -> Optional[Dict[str, Any]]:
        path = self._cache_path(key)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def _save_cache(self, key: str, value: Dict[str, Any]) -> None:
        path = self._cache_path(key)
        try:
            path.write_text(
                json.dumps(value, separators=(",", ":")), encoding="utf-8"
            )
        except OSError:
            pass
