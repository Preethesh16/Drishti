"""THE NUMBER — runs OFFLINE in seconds, no API key.

Method A — duplicate detection on the real `is_duplicate_report` flag (202 rows):
  for each record, best candidate score; predict "duplicate" if >= DUP_THRESHOLD.
  Report RECALL over the 202 flagged + the discrimination GAP (mean best-score of
  flagged vs non-flagged). Naive precision is misleading (names collide by chance),
  so we lead with recall + gap and say so.

Method B — synthetic pair recovery (clean ground truth):
  clone N resolved records into realistic "second reports" (new id, different
  center, DROP the name, paraphrase the description, shift to an adjacent zone),
  inject, then measure recall@1/@3/@5 — does the matcher rank the true source in
  top-k using ONLY de-identified weak signals.

Run:  python -m drishti.validate
"""
from __future__ import annotations

import random
import statistics
from dataclasses import replace

from drishti import config as C
from drishti.ingest import Record, load_records
from drishti.matcher_tier1 import find_candidates, score, gate


# ----------------------------------------------------------------------------
# Method A
# ----------------------------------------------------------------------------
def method_a(records: list[Record]) -> dict:
    flagged_best, nonflagged_best = [], []
    recovered = 0
    flagged_total = 0

    # precompute best score per record (gate-aware)
    for target in records:
        best = 0.0
        for b in records:
            if not gate(target, b):
                continue
            s = score(target, b).score
            if s > best:
                best = s
        if target.is_duplicate_report:
            flagged_total += 1
            flagged_best.append(best)
            if best >= C.DUP_THRESHOLD:
                recovered += 1
        else:
            nonflagged_best.append(best)

    recall = recovered / flagged_total if flagged_total else 0.0
    mean_flagged = statistics.mean(flagged_best) if flagged_best else 0.0
    mean_non = statistics.mean(nonflagged_best) if nonflagged_best else 0.0
    return {
        "flagged_total": flagged_total,
        "recovered": recovered,
        "recall": recall,
        "mean_flagged": mean_flagged,
        "mean_nonflagged": mean_non,
        "gap": mean_flagged - mean_non,
        "threshold": C.DUP_THRESHOLD,
    }


# ----------------------------------------------------------------------------
# Method B
# ----------------------------------------------------------------------------
def _adjacent_location(loc: str, all_locs: list[str], rng: random.Random) -> str:
    others = [l for l in all_locs if l and l != loc]
    return rng.choice(others) if others else loc


def _paraphrase(desc: str, rng: random.Random) -> str:
    """Light, deterministic-ish paraphrase: drop ~1 token + shuffle. Keeps the
    test honest (some overlap survives, mimicking a second reporter's wording)."""
    toks = [t for t in desc.split() if t]
    if len(toks) > 3:
        toks.pop(rng.randrange(len(toks)))
    rng.shuffle(toks)
    return " ".join(toks)


def make_synthetic_pairs(records: list[Record], n: int, seed: int = 42) -> list[tuple[Record, str]]:
    """Return list of (synthetic_second_report, true_source_case_id)."""
    rng = random.Random(seed)
    resolved = [r for r in records if (r.status or "").lower() == "reunited" and r.physical_description]
    rng.shuffle(resolved)
    all_locs = list({r.last_seen_location for r in records if r.last_seen_location})
    pairs = []
    for src in resolved[:n]:
        twin = replace(
            src,
            case_id=f"SYN-{src.case_id}",
            reporting_center=_adjacent_location(src.reporting_center,
                                                [r.reporting_center for r in records], rng),
            last_seen_location=_adjacent_location(src.last_seen_location, all_locs, rng),
            physical_description=_paraphrase(src.physical_description, rng),
            name_hash=None,          # the lost person can't give their name
            mobile_hash=None,        # different relative, different phone
            status="Pending",
            is_duplicate_report=False,
            vault_id=f"SYN-{src.case_id}",
            report_type="found",
        )
        pairs.append((twin, src.case_id))
    return pairs


def method_b(records: list[Record], n: int = 200, seed: int = 42) -> dict:
    pairs = make_synthetic_pairs(records, n=n, seed=seed)
    hits = {1: 0, 3: 0, 5: 0}
    for twin, true_id in pairs:
        ranked = find_candidates(twin, records, top_k=5)
        ranked_ids = [r.case_id for r in ranked]
        for k in (1, 3, 5):
            if true_id in ranked_ids[:k]:
                hits[k] += 1
    total = len(pairs) or 1
    return {
        "n": len(pairs),
        "recall@1": hits[1] / total,
        "recall@3": hits[3] / total,
        "recall@5": hits[5] / total,
    }


# ----------------------------------------------------------------------------
# Report
# ----------------------------------------------------------------------------
def run(n_synthetic: int = 200) -> dict:
    records, _ = load_records()
    a = method_a(records)
    b = method_b(records, n=n_synthetic)

    print("=" * 64)
    print("KUMBH SETU — VALIDATION (offline, no API key)")
    print("=" * 64)
    print(f"records loaded: {len(records)}")
    print()
    print("METHOD A — duplicate detection on real is_duplicate_report flag")
    print(f"  flagged duplicates (ground truth) : {a['flagged_total']}")
    print(f"  recovered at threshold {a['threshold']:>3}        : {a['recovered']}")
    print(f"  RECALL                            : {a['recall']*100:5.1f}%")
    print(f"  mean best-score  flagged          : {a['mean_flagged']:5.1f}")
    print(f"  mean best-score  non-flagged      : {a['mean_nonflagged']:5.1f}")
    print(f"  discrimination GAP                : {a['gap']:5.1f}")
    print("  (recall + gap lead; naive precision misleads — names collide by chance)")
    print()
    print("METHOD B — synthetic pair recovery (clean ground truth, de-identified)")
    print(f"  synthetic second-reports          : {b['n']}")
    print(f"  RECALL@1                          : {b['recall@1']*100:5.1f}%")
    print(f"  RECALL@3                          : {b['recall@3']*100:5.1f}%")
    print(f"  RECALL@5                          : {b['recall@5']*100:5.1f}%")
    print("=" * 64)
    return {"method_a": a, "method_b": b, "n_records": len(records)}


if __name__ == "__main__":
    run()
