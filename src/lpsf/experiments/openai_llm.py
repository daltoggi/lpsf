"""OpenAILLM: real LLM via OpenAI SDK for M4 Phase 3.

Drop-in for MockLLM. File-cached by SHA-256 of (prompt, context, model) under
~/.cache/lpsf/openai_llm/. Reports TokenUsage for cost accounting.

OpenAI SDK is imported ONLY in this file. The safety test allows it here and
forbids it everywhere else under src/lpsf/experiments/.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import openai

from .cost import TokenUsage
from .prompts import DEFAULT_SYSTEM_PROMPT


class OpenAILLM:
    """OpenAI ChatCompletion wrapper with file caching + token accounting."""

    DEFAULT_CACHE_DIR = os.path.expanduser("~/.cache/lpsf/openai_llm")

    def __init__(
        self,
        *,
        model: str = "gpt-4o",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        cache_dir: Optional[str] = None,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        max_tokens: int = 512,
        temperature: float = 0.0,
        timeout: float = 60.0,
    ) -> None:
        client_kwargs: Dict[str, Any] = {"timeout": timeout}
        resolved_key = api_key or os.environ.get("OPENAI_API_KEY")
        if resolved_key:
            client_kwargs["api_key"] = resolved_key
        resolved_base = base_url or os.environ.get("OPENAI_BASE_URL")
        if resolved_base:
            client_kwargs["base_url"] = resolved_base
        self._client = openai.OpenAI(**client_kwargs)
        self._model = model
        self._system_prompt = system_prompt
        self._max_tokens = max_tokens
        self._temperature = temperature

        self._cache_dir = Path(cache_dir or self.DEFAULT_CACHE_DIR)
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            self._cache_dir = Path(tempfile.gettempdir()) / "lpsf_openai_cache"
            self._cache_dir.mkdir(parents=True, exist_ok=True)

        self.usage = TokenUsage(model=model)

    # ---------- Protocol surface -----------------------------------------

    def version(self) -> str:
        return self._model

    def complete(
        self,
        prompt: str,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        key = self._cache_key(prompt, context)
        cached = self._load_cache(key)
        if cached is not None:
            self.usage.cache_hits += 1
            return cached

        chat = self._client.chat.completions.create(
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            messages=[
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": prompt},
            ],
        )

        choice = chat.choices[0]
        response_text = (choice.message.content or "").strip()

        usage_in = getattr(chat.usage, "prompt_tokens", 0) or 0
        usage_out = getattr(chat.usage, "completion_tokens", 0) or 0
        # OpenAI prompt_tokens_details.cached_tokens for cache hits
        cached_in = 0
        details = getattr(chat.usage, "prompt_tokens_details", None)
        if details is not None:
            cached_in = getattr(details, "cached_tokens", 0) or 0
        self.usage.add(
            input_tokens=usage_in,
            output_tokens=usage_out,
            cached_input_tokens=cached_in,
        )

        result: Dict[str, Any] = {
            "response": response_text,
            "confidence": 0.85,
            "evidence_refs": [],
            "model": self._model,
            "tokens": {"input": usage_in, "output": usage_out, "cached_input": cached_in},
        }
        self._save_cache(key, result)
        return result

    # ---------- Diagnostics ----------------------------------------------

    @classmethod
    def is_available(cls) -> bool:
        return bool(os.environ.get("OPENAI_API_KEY"))

    def stats(self) -> Dict[str, Any]:
        return self.usage.to_dict()

    # ---------- Cache internals (mirror CodexLLM) ------------------------

    def _cache_key(self, prompt: str, context: Optional[Dict[str, Any]]) -> str:
        payload = json.dumps(
            {
                "prompt": prompt,
                "context": context,
                "model": self._model,
                "system": self._system_prompt,
                "temperature": self._temperature,
            },
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
