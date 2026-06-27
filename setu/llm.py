"""Shared Claude helper — the reasoning brain, used by matcher_tier2 and voice.

Everything degrades cleanly: with no ANTHROPIC_API_KEY (or no `anthropic`
package), `have_claude()` is False and callers fall back to offline behaviour.
The demo must NEVER crash because a key is missing.
"""
from __future__ import annotations

import json

from setu import config as C

_client = None


def have_claude() -> bool:
    return bool(C.ANTHROPIC_API_KEY) and _get_client() is not None


def _get_client():
    global _client
    if _client is not None:
        return _client
    if not C.ANTHROPIC_API_KEY:
        return None
    try:
        from anthropic import Anthropic
        _client = Anthropic(api_key=C.ANTHROPIC_API_KEY)
    except Exception:
        _client = None
    return _client


def complete(user: str, *, system: str = "", model: str | None = None,
             max_tokens: int = 1024) -> str | None:
    """Single-turn completion. Returns text, or None if Claude is unavailable."""
    client = _get_client()
    if client is None:
        return None
    try:
        resp = client.messages.create(
            model=model or C.MODEL_DEFAULT,
            max_tokens=max_tokens,
            system=system or "You are a careful assistant.",
            messages=[{"role": "user", "content": user}],
        )
        return resp.content[0].text
    except Exception:
        return None


def complete_json(user: str, *, system: str = "", model: str | None = None,
                  max_tokens: int = 1024) -> dict | None:
    """Completion that should return JSON. Returns parsed dict or None.
    We nudge with a system instruction and tolerate code-fenced output."""
    sys = (system + "\nRespond with ONLY valid JSON, no prose, no code fences.").strip()
    text = complete(user, system=sys, model=model, max_tokens=max_tokens)
    if not text:
        return None
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):text.rfind("}") + 1]
    try:
        return json.loads(text)
    except Exception:
        return None
