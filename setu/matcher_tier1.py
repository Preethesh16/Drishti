"""Tier-1 matcher — OFFLINE, no API, no GPU. A funnel: thousands -> top-3.

1. Hard gate (cheap excludes): not same record, age within ±1 band,
   gender equal-or-Unknown, (optional) open status + time window.
2. Weighted score on weak signals: language, age, gender, geo, description,
   state, district -> normalise to 0..100 with explainable reasons.

Description similarity uses rapidfuzz if available, else a stdlib token-Jaccard
fallback so the spine runs with pandas + stdlib only.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from setu import config as C
from setu.ingest import Record

try:
    from rapidfuzz import fuzz as _fuzz
    _HAVE_RAPIDFUZZ = True
except Exception:  # pragma: no cover - fallback path
    _HAVE_RAPIDFUZZ = False


_TOKEN_RE = re.compile(r"[a-z0-9ऀ-ॿ]+")


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall((text or "").lower()))


def desc_similarity(a: str, b: str) -> float:
    """Return similarity in [0,1]. rapidfuzz token_set_ratio if available,
    else Jaccard over tokens. (Tier-2/Claude handles cross-lingual cases.)"""
    a, b = (a or "").strip(), (b or "").strip()
    if not a or not b:
        return 0.0
    if _HAVE_RAPIDFUZZ:
        return _fuzz.token_set_ratio(a, b) / 100.0
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _is_unknown(v: str) -> bool:
    return (v or "").strip().lower() in C.UNKNOWN_TOKENS or (v or "").strip().lower() == "unknown"


def gate(a: Record, b: Record, *, require_open: bool = False) -> bool:
    """Cheap hard excludes. True = b is a plausible candidate for a."""
    if a.case_id == b.case_id:
        return False
    # age within ±AGE_BAND_GATE
    ia, ib = C.AGE_INDEX.get(a.age_band), C.AGE_INDEX.get(b.age_band)
    if ia is not None and ib is not None and abs(ia - ib) > C.AGE_BAND_GATE:
        return False
    # gender equal or one Unknown
    ga, gb = a.gender.strip().lower(), b.gender.strip().lower()
    if not _is_unknown(ga) and not _is_unknown(gb) and ga != gb:
        return False
    if require_open and not b.is_open:
        return False
    return True


@dataclass
class ScoreResult:
    case_id: str
    score: float          # normalised 0..100
    raw: float
    reasons: dict         # signal -> points (explainable)


def score(a: Record, b: Record) -> ScoreResult:
    """Weighted weak-signal score with per-signal reasons."""
    reasons: dict[str, float] = {}
    raw = 0.0

    # language (strong discriminator)
    if a.language and a.language == b.language:
        raw += C.W_LANG
        reasons["language"] = C.W_LANG

    # age band
    ia, ib = C.AGE_INDEX.get(a.age_band), C.AGE_INDEX.get(b.age_band)
    if ia is not None and ib is not None:
        if ia == ib:
            raw += C.W_AGE_SAME
            reasons["age"] = C.W_AGE_SAME
        elif abs(ia - ib) == 1:
            raw += C.W_AGE_ADJ
            reasons["age"] = C.W_AGE_ADJ

    # gender
    ga, gb = a.gender.strip().lower(), b.gender.strip().lower()
    if not _is_unknown(ga) and ga == gb:
        raw += C.W_GENDER
        reasons["gender"] = C.W_GENDER
    elif _is_unknown(ga) or _is_unknown(gb):
        raw += C.W_GENDER_UNK
        reasons["gender"] = C.W_GENDER_UNK

    # geography (coarse same-location; geo.py refines with zone graph later)
    if a.last_seen_location and a.last_seen_location == b.last_seen_location:
        raw += C.W_GEO_SAME
        reasons["geo"] = C.W_GEO_SAME
    else:
        raw += C.W_GEO_DIFF
        reasons["geo"] = C.W_GEO_DIFF

    # description similarity
    sim = desc_similarity(a.physical_description, b.physical_description)
    if sim > 0:
        pts = round(C.W_DESC * sim, 2)
        raw += pts
        reasons["description"] = pts

    # state / district
    if a.state and a.state == b.state:
        raw += C.W_STATE
        reasons["state"] = C.W_STATE
    if a.district and a.district == b.district:
        raw += C.W_DISTRICT
        reasons["district"] = C.W_DISTRICT

    norm = round(100.0 * raw / C.MAX_RAW, 1)
    return ScoreResult(case_id=b.case_id, score=norm, raw=round(raw, 2), reasons=reasons)


def find_candidates(
    target: Record,
    pool: list[Record],
    *,
    top_k: int = 3,
    require_open: bool = False,
    min_score: float = 0.0,
) -> list[ScoreResult]:
    """Rank `pool` against `target`, return top-k passing the gate."""
    results = [
        score(target, b)
        for b in pool
        if gate(target, b, require_open=require_open)
    ]
    results = [r for r in results if r.score >= min_score]
    results.sort(key=lambda r: r.score, reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    from setu.ingest import load_records

    recs, _ = load_records()
    # demo: pick the first record flagged as a duplicate and show its top-3
    target = next((r for r in recs if r.is_duplicate_report), recs[0])
    print(f"TARGET {target.case_id} | {target.gender} {target.age_band} "
          f"{target.language} @ {target.last_seen_location}")
    print(f"  desc: {target.physical_description[:80]}")
    print("TOP-3 candidates:")
    for r in find_candidates(target, recs, top_k=3):
        print(f"  {r.case_id}  score={r.score:5.1f}  reasons={r.reasons}")
