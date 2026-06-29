"""
model_registry.py
=================
Maps model names to their provider and implements a unified chat() interface
for all supported free-tier LLM providers:
  - Groq  (OpenAI-compatible REST API)
  - Google Gemini (google-generativeai SDK)
  - Mistral (OpenAI-compatible REST API)

All calls are temperature-locked at 0.0 for reproducibility.
API failures are caught and returned as ChatResponse(success=False).
"""

from __future__ import annotations

import os
import json
import time
import logging
import requests
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional SDK imports — fall back to raw REST if SDKs are not installed
# ---------------------------------------------------------------------------
try:
    from groq import Groq as GroqClient  # type: ignore
    _GROQ_SDK = True
except ImportError:
    _GROQ_SDK = False

# Prefer new google-genai SDK; fall back to deprecated google-generativeai
_GEMINI_SDK = False
_GEMINI_SDK_NEW = False
try:
    from google import genai as _google_genai  # type: ignore  (google-genai >= 0.8)
    from google.genai import types as _genai_types  # type: ignore
    _GEMINI_SDK = True
    _GEMINI_SDK_NEW = True
except (ImportError, AttributeError):
    try:
        import google.generativeai as _google_genai  # type: ignore  (deprecated)
        _GEMINI_SDK = True
        _GEMINI_SDK_NEW = False
    except ImportError:
        pass

try:
    from mistralai import Mistral as MistralClient  # type: ignore
    _MISTRAL_SDK = True
except ImportError:
    _MISTRAL_SDK = False


# ---------------------------------------------------------------------------
# Response dataclass
# ---------------------------------------------------------------------------
@dataclass
class ChatResponse:
    """Unified response object from any LLM provider."""
    content: str
    model: str
    provider: str
    latency_seconds: float
    token_count: int          # completion tokens (estimated if unavailable)
    success: bool
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------
# fmt: off
MODELS: Dict[str, Dict[str, str]] = {
    # ── Groq ──────────────────────────────────────────────────────────────
    "groq/llama-3.3-70b-versatile":         {"provider": "groq",    "model_id": "llama-3.3-70b-versatile"},
    "groq/llama-4-scout-17b":               {"provider": "groq",    "model_id": "meta-llama/llama-4-scout-17b-16e-instruct"},
    # ── Google Gemini ──────────────────────────────────────────────────────
    "gemini/gemini-2.0-flash":              {"provider": "gemini",  "model_id": "gemini-2.0-flash"},
    # ── Mistral ────────────────────────────────────────────────────────────
    "mistral/mistral-small-latest":         {"provider": "mistral", "model_id": "mistral-small-latest"},
}
# fmt: on

ALL_MODEL_NAMES: List[str] = list(MODELS.keys())

# Canonical 4-model benchmark set (default for --models all in run_eval.py)
FOUR_MODEL_NAMES: List[str] = [
    "groq/llama-3.3-70b-versatile",
    "groq/llama-4-scout-17b",
    "gemini/gemini-2.0-flash",
    "mistral/mistral-small-latest",
]

# Provider groupings (used for judge rotation)
PROVIDER_GROUPS: Dict[str, List[str]] = {
    "groq":    [m for m, v in MODELS.items() if v["provider"] == "groq"],
    "gemini":  [m for m, v in MODELS.items() if v["provider"] == "gemini"],
    "mistral": [m for m, v in MODELS.items() if v["provider"] == "mistral"],
}


# ---------------------------------------------------------------------------
# Internal provider implementations
# ---------------------------------------------------------------------------

def _chat_groq(
    model_id: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.0,
    max_tokens: int = 2048,
) -> ChatResponse:
    """Call Groq API — prefers the groq SDK; falls back to raw REST."""
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return ChatResponse(
            content="", model=model_id, provider="groq",
            latency_seconds=0.0, token_count=0, success=False,
            error="GROQ_API_KEY not set",
        )
    t0 = time.perf_counter()
    try:
        if _GROQ_SDK:
            client = GroqClient(api_key=api_key)
            completion = client.chat.completions.create(
                model=model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = completion.choices[0].message.content or ""
            tokens = (
                completion.usage.completion_tokens
                if completion.usage
                else _estimate_tokens(content)
            )
        else:
            # Raw REST fallback
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_id,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=90,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            tokens = data.get("usage", {}).get(
                "completion_tokens", _estimate_tokens(content)
            )
        return ChatResponse(
            content=content,
            model=model_id,
            provider="groq",
            latency_seconds=time.perf_counter() - t0,
            token_count=tokens,
            success=True,
        )
    except Exception as exc:
        logger.warning("Groq %s failed: %s", model_id, exc)
        return ChatResponse(
            content="", model=model_id, provider="groq",
            latency_seconds=time.perf_counter() - t0,
            token_count=0, success=False, error=str(exc),
        )


def _chat_gemini(
    model_id: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.0,
    max_tokens: int = 2048,
) -> ChatResponse:
    """Call Google Gemini API — prefers the SDK; falls back to REST."""
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        return ChatResponse(
            content="", model=model_id, provider="gemini",
            latency_seconds=0.0, token_count=0, success=False,
            error="GOOGLE_API_KEY not set",
        )
    t0 = time.perf_counter()
    try:
        # Flatten multi-turn messages into a single prompt
        prompt = _flatten_messages(messages)

        if _GEMINI_SDK and _GEMINI_SDK_NEW:
            # New google-genai SDK (google.genai >= 0.8)
            client = _google_genai.Client(api_key=api_key)  # type: ignore
            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=_genai_types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )
            content = response.text or ""
            tokens = _estimate_tokens(content)
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                tokens = getattr(response.usage_metadata, "candidates_token_count", tokens) or tokens
        elif _GEMINI_SDK and not _GEMINI_SDK_NEW:
            # Old deprecated google-generativeai SDK
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                _google_genai.configure(api_key=api_key)  # type: ignore
                model_obj = _google_genai.GenerativeModel(  # type: ignore
                    model_name=model_id,
                    generation_config={
                        "temperature": temperature,
                        "max_output_tokens": max_tokens,
                    },
                )
                response = model_obj.generate_content(prompt)
            content = response.text or ""
            tokens = _estimate_tokens(content)
        else:
            # REST fallback via v1beta endpoint
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model_id}:generateContent?key={api_key}"
            )
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                },
            }
            resp = requests.post(url, json=payload, timeout=90)
            resp.raise_for_status()
            data = resp.json()
            content = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
            tokens = _estimate_tokens(content)

        return ChatResponse(
            content=content,
            model=model_id,
            provider="gemini",
            latency_seconds=time.perf_counter() - t0,
            token_count=tokens,
            success=True,
        )
    except Exception as exc:
        logger.warning("Gemini %s failed: %s", model_id, exc)
        return ChatResponse(
            content="", model=model_id, provider="gemini",
            latency_seconds=time.perf_counter() - t0,
            token_count=0, success=False, error=str(exc),
        )


def _chat_mistral(
    model_id: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.0,
    max_tokens: int = 2048,
) -> ChatResponse:
    """Call Mistral La Plateforme API — prefers SDK; falls back to REST."""
    api_key = os.getenv("MISTRAL_API_KEY", "")
    if not api_key:
        return ChatResponse(
            content="", model=model_id, provider="mistral",
            latency_seconds=0.0, token_count=0, success=False,
            error="MISTRAL_API_KEY not set",
        )
    t0 = time.perf_counter()
    try:
        if _MISTRAL_SDK:
            client = MistralClient(api_key=api_key)
            # SDK v2 uses client.chat.complete(); v1 used client.chat()
            try:
                response = client.chat.complete(
                    model=model_id,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except AttributeError:
                # Fallback for older mistralai SDK v1
                response = client.chat(
                    model=model_id,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            content = response.choices[0].message.content or ""
            tokens = (
                response.usage.completion_tokens
                if response.usage
                else _estimate_tokens(content)
            )
        else:
            # Raw REST fallback
            resp = requests.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_id,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=90,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            tokens = data.get("usage", {}).get(
                "completion_tokens", _estimate_tokens(content)
            )
        return ChatResponse(
            content=content,
            model=model_id,
            provider="mistral",
            latency_seconds=time.perf_counter() - t0,
            token_count=tokens,
            success=True,
        )
    except Exception as exc:
        logger.warning("Mistral %s failed: %s", model_id, exc)
        return ChatResponse(
            content="", model=model_id, provider="mistral",
            latency_seconds=time.perf_counter() - t0,
            token_count=0, success=False, error=str(exc),
        )


# ---------------------------------------------------------------------------
# Public unified interface
# ---------------------------------------------------------------------------

def chat(
    model_name: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.0,
    max_tokens: int = 2048,
) -> ChatResponse:
    """
    Unified chat call dispatched to the correct provider.

    Args:
        model_name:  Registry key, e.g. "groq/llama-3.3-70b-versatile"
        messages:    OpenAI-style list of {"role": "user"|"assistant"|"system", "content": "..."}
        temperature: Sampling temperature (fixed at 0.0 for reproducibility)
        max_tokens:  Maximum completion tokens

    Returns:
        ChatResponse (success=False if the provider is unreachable)
    """
    if model_name not in MODELS:
        raise ValueError(
            f"Unknown model '{model_name}'. Available: {ALL_MODEL_NAMES}"
        )
    info = MODELS[model_name]
    provider = info["provider"]
    model_id = info["model_id"]

    if provider == "groq":
        return _chat_groq(model_id, messages, temperature, max_tokens)
    elif provider == "gemini":
        return _chat_gemini(model_id, messages, temperature, max_tokens)
    elif provider == "mistral":
        return _chat_mistral(model_id, messages, temperature, max_tokens)
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def get_provider(model_name: str) -> str:
    """Return the provider name for a given model registry key."""
    return MODELS[model_name]["provider"]


def get_judge_candidates(backbone_model: str) -> List[str]:
    """
    Return a list of candidate judge models, excluding the backbone model's
    own provider (to ensure independent evaluation).  Falls back to all models
    if only one provider is available.
    """
    backbone_provider = get_provider(backbone_model)
    candidates = [
        m for m in ALL_MODEL_NAMES
        if get_provider(m) != backbone_provider
    ]
    if not candidates:
        # Last resort: allow same provider but exclude exact model
        candidates = [m for m in ALL_MODEL_NAMES if m != backbone_model]
    return candidates


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~0.75 words per token (GPT-family heuristic)."""
    return max(1, int(len(text.split()) / 0.75))


def _flatten_messages(messages: List[Dict[str, str]]) -> str:
    """Collapse a multi-turn message list into a single string for Gemini."""
    parts = []
    for m in messages:
        role = m.get("role", "user").capitalize()
        content = m.get("content", "")
        if role.lower() == "system":
            parts.append(f"[System Instructions]\n{content}")
        elif role.lower() == "assistant":
            parts.append(f"[Assistant]\n{content}")
        else:
            parts.append(content)
    return "\n\n".join(parts)


def check_api_keys() -> Dict[str, bool]:
    """Return which API keys are configured (non-empty)."""
    return {
        "GROQ_API_KEY":   bool(os.getenv("GROQ_API_KEY")),
        "GOOGLE_API_KEY": bool(os.getenv("GOOGLE_API_KEY")),
        "MISTRAL_API_KEY": bool(os.getenv("MISTRAL_API_KEY")),
    }
