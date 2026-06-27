"""Structural privacy: hash at ingest, mask in UI, reveal-on-confirm + audit.

The matching engine NEVER sees raw name/mobile — only HMAC hashes. Raw values
live in an access-controlled vault and surface only when a human confirms a
reunion, leaving an audit line behind.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import hmac

from drishti.config import PII_SALT, AUDIT_LOG, UNKNOWN_TOKENS


def _norm(value: str | None) -> str:
    return (value or "").strip()


def is_blank(value: str | None) -> bool:
    return _norm(value).lower() in UNKNOWN_TOKENS


def hash_pii(value: str | None) -> str | None:
    """HMAC-SHA256 of a normalised PII string. Returns None for blanks so we
    never pretend an absent identifier is a meaningful hash."""
    v = _norm(value).lower()
    if v in UNKNOWN_TOKENS:
        return None
    return hmac.new(PII_SALT.encode(), v.encode(), hashlib.sha256).hexdigest()


def mask_name(name: str | None) -> str:
    n = _norm(name)
    if not n:
        return "—"
    if len(n) <= 2:
        return n[0] + "*"
    return f"{n[0]}{'*' * (len(n) - 2)}{n[-1]}"


def mask_mobile(mobile: str | None) -> str:
    digits = "".join(ch for ch in _norm(mobile) if ch.isdigit())
    if not digits:
        return "—"
    return "*" * max(0, len(digits) - 4) + digits[-4:]


def reveal(case_id: str, fields: dict, *, actor: str, reason: str) -> dict:
    """Reveal raw PII for a human-confirmed match. Writes an audit line.
    `fields` is the raw record dict pulled from the vault by the caller."""
    ts = _dt.datetime.now(_dt.timezone.utc).isoformat()
    line = (
        f"{ts}\tREVEAL\tcase={case_id}\tactor={actor}\treason={reason}\t"
        f"fields={sorted(fields.keys())}\n"
    )
    with open(AUDIT_LOG, "a", encoding="utf-8") as fh:
        fh.write(line)
    return fields


def audit(event: str, **kv) -> None:
    """Generic audit line for non-reveal privacy events (purge, consent, etc.)."""
    ts = _dt.datetime.now(_dt.timezone.utc).isoformat()
    extra = "\t".join(f"{k}={v}" for k, v in kv.items())
    with open(AUDIT_LOG, "a", encoding="utf-8") as fh:
        fh.write(f"{ts}\t{event}\t{extra}\n")
