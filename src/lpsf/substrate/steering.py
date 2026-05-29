"""Activation steering — the founding-doc mechanism (epigenetic node modulation).

The state-space-landscape-plasticity hypothesis (2026-05-07) specifies, in
section 6, the actual mechanism: freeze the weights, attach a persistent
state to nodes/channels, and let that state change the node's *response*
during the forward pass. Line 200 literally defines sensitivity modulation as
"activation gain, threshold, gate sensitivity".

This module realizes that on a real frozen transformer (Qwen2.5-0.5B via MLX):
inject a persistent steering vector into a chosen residual-stream layer so the
same input follows a different internal trajectory — without touching weights
(unlike LoRA) and without re-feeding text into the prompt (unlike RAG).

The LPSF operators map onto steering naturally:
    deepen_attractor   -> add +alpha * v        (alpha large)
    weaken_attractor   -> reduce alpha
    inhibit_path       -> add -alpha * v
    tilt_value_field   -> v is a value-axis direction
    modulate_sensitivity -> scale alpha (gain)
    decay              -> alpha *= 0.5^(elapsed/half_life)

Steering vectors are derived by the standard contrastive mean-difference
recipe (ActAdd / CAA): mean residual activation on positive prompts minus
mean on negative prompts, at the target layer.

This file imports mlx only inside methods so the package still imports without
mlx present (CI has no model). It is NOT part of pytest.
"""

from __future__ import annotations

import math
from typing import Any, List, Optional


DEFAULT_MODEL = "mlx-community/Qwen2.5-0.5B-Instruct-4bit"


class SteeringModel:
    """A frozen MLX LLM with a persistent, inspectable activation-steering state.

    One steering vector is injected at `layer_idx` (residual stream). The vector
    and its scale ARE the landscape state — inspectable (a 896-dim vector),
    reversible (set scale 0), decayable (shrink scale), signable (negate).
    """

    def __init__(self, *, model_name: str = DEFAULT_MODEL, layer_idx: int = 12) -> None:
        from mlx_lm import load

        self.model_name = model_name
        self.layer_idx = layer_idx
        self.model, self.tok = load(model_name)
        self._inner = getattr(self.model, "model", self.model)
        self._layers = self._inner.layers
        self.hidden = self._layers[layer_idx].hidden_size

        # Steering state (the persistent landscape).
        self._steer = None      # mx.array (hidden,) or None
        self._scale = 0.0
        # Capture state.
        self._capture = False
        self._captured = None   # accumulates mean activation

        self._install_hook()

    # ---- hook -----------------------------------------------------------

    def _install_hook(self) -> None:
        # Python invokes `layer(...)` via `type(layer).__call__`, so assigning
        # an instance attribute does NOT intercept the call. Instead we replace
        # the layer object in the list with a wrapper whose CLASS defines
        # __call__. The wrapper delegates to the original layer (weights intact)
        # then applies capture / steering.
        original = self._layers[self.layer_idx]
        controller = self

        class _SteerWrapper:
            def __init__(self, inner):
                object.__setattr__(self, "inner", inner)

            def __call__(self, x, mask=None, cache=None):
                out = self.inner(x, mask=mask, cache=cache)
                if controller._capture:
                    v = out.mean(axis=1)[0]  # mean over sequence -> (hidden,)
                    controller._captured = (
                        v if controller._captured is None
                        else controller._captured + v
                    )
                if controller._steer is not None and controller._scale != 0.0:
                    out = out + (controller._scale * controller._steer)
                return out

            def __getattr__(self, name):
                # Delegate params/attrs to the wrapped layer.
                return getattr(object.__getattribute__(self, "inner"), name)

        self._orig_layer = original
        self._layers[self.layer_idx] = _SteerWrapper(original)

    # ---- steering state (LPSF landscape) --------------------------------

    def set_steer(self, vec, scale: float) -> None:
        self._steer = vec
        self._scale = float(scale)

    def clear_steer(self) -> None:
        self._steer = None
        self._scale = 0.0

    def decay(self, half_life: float, elapsed: float) -> float:
        """Operator: decay. Shrink the steering scale by 0.5^(elapsed/half_life)."""
        factor = math.pow(0.5, elapsed / max(half_life, 1e-8))
        self._scale *= factor
        return factor

    @property
    def scale(self) -> float:
        return self._scale

    # ---- vector derivation (contrastive mean-difference) ----------------

    def _mean_activation(self, prompts: List[str]) -> Any:
        import mlx.core as mx

        self._captured = None
        n = 0
        for p in prompts:
            msgs = [{"role": "user", "content": p}]
            ids = self.tok.apply_chat_template(msgs, add_generation_prompt=True)
            arr = mx.array(ids)[None]
            self._capture = True
            try:
                _ = self.model(arr)  # forward pass; hook captures
            finally:
                self._capture = False
            n += 1
        mx.eval(self._captured)
        return self._captured / max(n, 1)

    def derive_vector(self, positive: List[str], negative: List[str]) -> Any:
        """Steering vector = mean_act(positive) - mean_act(negative), unit-normed."""
        import mlx.core as mx

        pos = self._mean_activation(positive)
        neg = self._mean_activation(negative)
        v = pos - neg
        norm = mx.sqrt((v * v).sum())
        return v / (norm + 1e-8)

    def random_vector(self, seed: int = 0) -> Any:
        """A norm-1 random vector — the NEGATIVE CONTROL. If a random vector
        produces the same 'effect' as a derived one, the effect is degradation,
        not steering."""
        import mlx.core as mx

        key = mx.random.key(seed)
        v = mx.random.normal((self.hidden,), key=key)
        norm = mx.sqrt((v * v).sum())
        return v / (norm + 1e-8)

    # ---- generation -----------------------------------------------------

    def generate(self, prompt: str, *, max_tokens: int = 60) -> str:
        from mlx_lm import generate

        msgs = [{"role": "user", "content": prompt}]
        text = self.tok.apply_chat_template(msgs, add_generation_prompt=True)
        return generate(self.model, self.tok, prompt=text,
                        max_tokens=max_tokens, verbose=False).strip()
