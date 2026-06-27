"""Tier-2 matcher — Claude as the cross-lingual brain on top of Tier-1.

Tier-1 is a cheap offline funnel. Tier-2 takes ONLY its top-K survivors and asks
Claude to compare the free-text physical descriptions ACROSS LANGUAGES — the one
thing a SQL/Jaccard matcher cannot do ("saffron saree, rudraksha" ↔ "orange
clothes, prayer beads" → same person). It re-scores just the description signal,
re-ranks, assigns a decision band, and writes a human-readable reason.

Degrades cleanly: with no ANTHROPIC_API_KEY it returns Tier-1 scores + a templated
reason. The demo never crashes on a missing key.

Decision bands (config): score >= MATCH_AUTO -> auto-ALERT a human (never auto-
reunite); >= MATCH_REVIEW -> queue for review; below -> no match yet.

Run:  python -m drishti.matcher_tier2
"""
from __future__ import annotations

from dataclasses import dataclass

from drishti import config as C
from drishti import llm
from drishti.ingest import Record
from drishti.matcher_tier1 import find_candidates, ScoreResult


def band(score: float) -> str:
    if score >= C.MATCH_AUTO:
        return "auto"
    if score >= C.MATCH_REVIEW:
        return "review"
    return "none"


@dataclass
class EnrichedResult:
    case_id: str
    score: float            # normalised 0..100 (description upgraded by Claude if available)
    tier1_score: float
    band: str               # auto | review | none
    reason: str             # human-readable
    tier2_used: bool        # did Claude actually run?
    reasons: dict           # per-signal points (from Tier-1)


# ---------------------------------------------------------------------------
# Human-readable reason (works with or without Claude)
# ---------------------------------------------------------------------------
_SIGNAL_PHRASE = {
    "language": "same language",
    "age": "similar age",
    "gender": "gender consistent",
    "geo": "same area",
    "description": "matching description",
    "state": "same home state",
    "district": "same home district",
}


def _template_reason(reasons: dict) -> str:
    parts = [phrase for key, phrase in _SIGNAL_PHRASE.items()
             if key in reasons and reasons[key]]
    return ", ".join(parts) if parts else "weak signal overlap only"


# ---------------------------------------------------------------------------
# Claude cross-lingual description comparison
# ---------------------------------------------------------------------------
_DESC_SYS = (
    "You compare two physical descriptions of a possibly-missing person, written "
    "by DIFFERENT people, often in different Indian languages or transliterations. "
    "Judge how likely they describe the SAME person. Focus on stable attributes: "
    "clothing colour/type, build, age cues, distinguishing marks, mobility aids "
    "(stick, glasses), sensory issues. Treat cross-language synonyms as matches "
    "(e.g. 'saffron'='orange', 'rudraksha mala'='prayer beads'). Ignore wording."
)


def claude_desc_similarity(a: Record, b: Record) -> tuple[float | None, str | None]:
    """Return (likelihood 0..1, short reason) from Claude, or (None, None)."""
    da, db = (a.physical_description or "").strip(), (b.physical_description or "").strip()
    if not da or not db or not llm.have_claude():
        return None, None
    user = (
        f"Description A ({a.language}): \"{da}\"\n"
        f"Description B ({b.language}): \"{db}\"\n"
        f"Context: both reportedly {a.gender}/{b.gender}, age {a.age_band}/{b.age_band}.\n"
        'Return JSON: {"likelihood": 0.0-1.0, "reason": "<=12 words, plain English"}.'
    )
    out = llm.complete_json(user, system=_DESC_SYS, max_tokens=200)
    if not out:
        return None, None
    try:
        lk = float(out.get("likelihood"))
        lk = max(0.0, min(1.0, lk))
        return lk, str(out.get("reason", "")).strip() or None
    except (TypeError, ValueError):
        return None, None


def _rescore_with_desc(result: ScoreResult, new_desc_sim: float) -> float:
    """Swap Tier-1's offline description points for Claude's cross-lingual ones."""
    old_desc_pts = result.reasons.get("description", 0.0)
    new_desc_pts = C.W_DESC * new_desc_sim
    new_raw = result.raw - old_desc_pts + new_desc_pts
    return round(100.0 * new_raw / C.MAX_RAW, 1)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def enrich(target: Record, pool_by_id: dict[str, Record],
           candidates: list[ScoreResult]) -> list[EnrichedResult]:
    out: list[EnrichedResult] = []
    for cand in candidates:
        b = pool_by_id.get(cand.case_id)
        score = cand.score
        tier2_used = False
        reason = _template_reason(cand.reasons)
        if b is not None:
            lk, claude_reason = claude_desc_similarity(target, b)
            if lk is not None:
                score = _rescore_with_desc(cand, lk)
                tier2_used = True
                base = _template_reason({k: v for k, v in cand.reasons.items()
                                         if k != "description"})
                reason = (f"{base}; description: {claude_reason}" if claude_reason
                          else f"{base}; cross-lingual description match {lk:.0%}")
        out.append(EnrichedResult(
            case_id=cand.case_id, score=score, tier1_score=cand.score,
            band=band(score), reason=reason, tier2_used=tier2_used,
            reasons=cand.reasons,
        ))
    out.sort(key=lambda r: r.score, reverse=True)
    return out


def match(target: Record, pool: list[Record], *, top_k: int = 3,
          tier2_k: int = 5, require_open: bool = False) -> list[EnrichedResult]:
    """Full Step-5 pipeline: Tier-1 funnel -> Claude enrich top tier2_k -> band -> top_k."""
    cands = find_candidates(target, pool, top_k=tier2_k, require_open=require_open)
    pool_by_id = {r.case_id: r for r in pool}
    enriched = enrich(target, pool_by_id, cands)
    return enriched[:top_k]


if __name__ == "__main__":
    from drishti.ingest import load_records

    recs, _ = load_records()
    print(f"Claude available: {llm.have_claude()}  "
          f"(bands: auto>={C.MATCH_AUTO}, review>={C.MATCH_REVIEW})")
    target = next((r for r in recs if r.is_duplicate_report), recs[0])
    print(f"\nTARGET {target.case_id} | {target.gender} {target.age_band} "
          f"{target.language} @ {target.last_seen_location}")
    print(f"  desc: {target.physical_description[:80]}")
    print("TOP-3 (Tier-2 enriched):")
    for r in match(target, recs, top_k=3):
        flag = "🤖Claude" if r.tier2_used else "offline"
        print(f"  {r.case_id}  score={r.score:5.1f} [{r.band:6}] ({flag})  {r.reason}")
