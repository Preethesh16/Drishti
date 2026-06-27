"""THIN API — the one door the dashboard (and Claude/MCP later) knock on. [PERSON B]

Decouples C's UI from B's internals: nothing outside `setu/` reaches into SQLite.
Every call is served by the live `registry.db` + the access-controlled `setu_vault.db`
— the same stores `seed_from_csv` fills. The registry never exposes raw PII; contact
surfaces only through `confirm()` (reveal-on-confirm), exactly as the privacy core
demands.

    ensure_seeded()                 -> str    # seed from real CSV if present, else a demo set
    stats()                         -> dict
    list_records(open_only, limit)  -> list[Record]
    get_record(case_id)             -> Record | None
    find_matches(case_id, top_k)    -> list[dict]   # live Tier-1 vs the open, windowed pool
    candidates(case_id)             -> list[dict]   # stored retroactive matches (B2)
    file_report(record)             -> str          # add_record(rematch=True) — fires B2
    confirm(case_a, case_b, ...)    -> dict          # reveal-on-confirm + purge (B4)
"""
from __future__ import annotations

import os
from collections import Counter

from drishti import config as C
from drishti import registry
from drishti import vault as vaultmod
from drishti.ingest import Record
from drishti.matcher_tier1 import find_candidates


# ----------------------------------------------------------------------------
# Reads
# ----------------------------------------------------------------------------
def stats(db_path=C.REGISTRY_DB, vault_path=C.VAULT_DB) -> dict:
    recs = registry.get_records(db_path=db_path)
    by_status = Counter((r.status or "—") for r in recs)
    live, purged = vaultmod.count(vault_path) if os.path.exists(vault_path) else (0, 0)
    return {
        "total": len(recs),
        "open": sum(1 for r in recs if r.is_open),
        "reunited": by_status.get("Reunited", 0),
        "by_status": dict(by_status),
        "centers": len({r.reporting_center for r in recs if r.reporting_center}),
        "languages": len({r.language for r in recs if r.language}),
        "vault_live": live,
        "vault_purged": purged,
    }


def list_records(open_only=False, limit=None, db_path=C.REGISTRY_DB) -> list[Record]:
    recs = registry.get_records(open_only=open_only, db_path=db_path)
    recs.sort(key=lambda r: r.reported_at or "", reverse=True)
    return recs[:limit] if limit else recs


def get_record(case_id, db_path=C.REGISTRY_DB) -> Record | None:
    for r in registry.get_records(db_path=db_path):
        if r.case_id == case_id:
            return r
    return None


def _to_view(rec: Record, r) -> dict:
    """Shape one Tier-1 ScoreResult + its record into a display dict (no raw PII)."""
    return {
        "case_id": r.case_id,
        "score": r.score,
        "is_strong": r.score >= C.DUP_THRESHOLD,
        "reasons": r.reasons,
        "report_type": rec.report_type,
        "gender": rec.gender, "age_band": rec.age_band, "language": rec.language,
        "last_seen_location": rec.last_seen_location,
        "reporting_center": rec.reporting_center,
        "physical_description": rec.physical_description,
        "status": rec.status,
    }


def find_matches(case_id, top_k=3, window_hours=C.TIME_WINDOW_HOURS,
                 db_path=C.REGISTRY_DB) -> list[dict]:
    """Live Tier-1 search: rank the open, time-windowed pool against `case_id`.
    Returns display dicts (score + per-signal reasons), best first."""
    target = get_record(case_id, db_path)
    if target is None:
        return []
    pool = registry.get_records(open_only=True, window_hours=window_hours,
                                reference_time=target.reported_at, db_path=db_path)
    by_id = {r.case_id: r for r in pool}
    results = find_candidates(target, pool, top_k=top_k, require_open=True)
    return [_to_view(by_id[r.case_id], r) for r in results if r.case_id in by_id]


def candidates(case_id, db_path=C.REGISTRY_DB) -> list[dict]:
    return registry.get_candidates(case_id, db_path=db_path)


# ----------------------------------------------------------------------------
# Writes
# ----------------------------------------------------------------------------
def file_report(record: Record, db_path=C.REGISTRY_DB, vault_path=C.VAULT_DB,
                *, name: str | None = None, mobile: str | None = None,
                consent: bool = True) -> str:
    """File a new report: persist its raw PII to the vault, the de-identified
    record to the registry, and fire the retroactive re-match hook (B2)."""
    vaultmod.put(record.vault_id or record.case_id, name, mobile,
                 consent=consent, db_path=vault_path)
    return registry.add_record(record, db_path, rematch=True)


def confirm(case_a, case_b, actor="operator", reason="human-confirmed reunion",
            db_path=C.REGISTRY_DB, vault_path=C.VAULT_DB) -> dict:
    """Reveal-on-confirm: mark Reunited, reveal raw contact (audited), purge PII."""
    return registry.confirm_match(case_a, case_b, actor=actor, reason=reason,
                                  db_path=db_path, vault_path=vault_path)


# ----------------------------------------------------------------------------
# Seeding — make the connected DB usable with OR without the real data drop
# ----------------------------------------------------------------------------
def ensure_seeded(db_path=C.REGISTRY_DB, vault_path=C.VAULT_DB) -> str:
    """Idempotent: if the registry is empty, seed it. Prefer the real 2,500-row
    CSV; if it isn't there yet, fall back to a small built-in demo set so the UI
    (and the DB connection) work the instant you launch — no data drop required."""
    registry.init_db(db_path)
    if stats(db_path, vault_path)["total"] > 0:
        return "already-seeded"
    if C.MISSING_CSV.exists():
        n = registry.seed_from_csv(db_path, vault_path)
        return f"seeded {n} from real CSV"
    n = seed_demo(db_path, vault_path)
    return f"seeded {n} demo records (data/ empty — drop the real CSV to replace)"


def reset(db_path=C.REGISTRY_DB, vault_path=C.VAULT_DB) -> str:
    """Wipe both stores and reseed. Demo convenience (DB files are gitignored)."""
    for p in (db_path, vault_path):
        try:
            os.remove(p)
        except FileNotFoundError:
            pass
    return ensure_seeded(db_path, vault_path)


# (rec_id, type, gender, age, lang, loc, center, status, reported_at, desc, name, mobile)
_DEMO = [
    ("R6", "missing", "Female", "41-60", "Bengali", "Tapovan", "Center-A",
     "Reunited", "2027-08-12T07:00:00", "woman blue saree spectacles gold earrings",
     "Anita Das", "9811111111"),
    ("R7", "found", "Male", "18-40", "Marathi", "Ramkund", "Center-B",
     "Reunited", "2027-08-13T07:00:00", "man checked shirt jeans", "", ""),
    ("M5", "missing", "Male", "71-80", "Gujarati", "Kalaram Temple", "Center-C",
     "Pending", "2027-08-15T08:30:00", "old man white kurta walking stick hard of hearing",
     "Harilal Shah", "9722220000"),
    ("F1", "found", "Female", "61-70", "Marathi", "Ramkund", "Center-B",
     "Pending", "2027-08-15T09:00:00",
     "elderly woman saffron saree rudraksha beads silver anklets", "", ""),
    ("F4", "found", "Female", "18-40", "Tamil", "Trimbakeshwar", "Center-F",
     "Pending", "2027-08-15T10:15:00", "young woman green salwar gold bangles", "", ""),
    ("M1", "missing", "Female", "61-70", "Marathi", "Ramkund", "Center-A",
     "Pending", "2027-08-15T11:00:00",
     "old lady orange saree prayer beads silver anklets", "Sunita Patil", "9812345678"),
    ("F3", "found", "Male", "0-12", "Hindi", "Panchavati", "Center-D",
     "Pending", "2027-08-15T12:00:00", "small boy red tshirt blue shorts crying", "", ""),
    ("M3", "missing", "Male", "0-12", "Hindi", "Panchavati", "Center-E",
     "Pending", "2027-08-15T13:30:00", "little boy red shirt dark shorts scared",
     "Imran Shaikh", "9890011111"),
    ("M8", "missing", "Female", "61-70", "Marathi", "Gangapur", "Center-G",
     "Pending", "2027-08-15T14:00:00", "elderly woman white saree thin frame",
     "Kamala Bai", "9733330000"),
]


def seed_demo(db_path=C.REGISTRY_DB, vault_path=C.VAULT_DB) -> int:
    """Insert a small, realistic synthetic set (cross-center match pairs, singletons,
    reunited cases, 5 languages) IN chronological order with the B2 hook live, so
    the registry, retroactive candidates, and reveal-on-confirm all have something
    to show. NOT the real number — that needs the hackathon CSV."""
    from drishti import privacy
    registry.init_db(db_path)
    vaultmod.init_vault(vault_path)
    n = 0
    for (cid, rtype, gender, age, lang, loc, center, status, ts, desc, name, mob) in _DEMO:
        vaultmod.put(cid, name, mob, consent=True, db_path=vault_path)
        rec = Record(
            case_id=cid, reported_at=ts, gender=gender, age_band=age,
            state="Maharashtra", district="Nashik", language=lang,
            last_seen_location=loc, reporting_center=center,
            physical_description=desc, status=status,
            name_hash=privacy.hash_pii(name), mobile_hash=privacy.hash_pii(mob),
            is_duplicate_report=cid in {"M1", "M3"}, vault_id=cid, report_type=rtype,
        )
        # rematch only for open reports (closed ones aren't bait)
        registry.add_record(rec, db_path, rematch=rec.is_open)
        n += 1
    return n


if __name__ == "__main__":
    print("ensure_seeded:", ensure_seeded())
    s = stats()
    print(f"records={s['total']} open={s['open']} reunited={s['reunited']} "
          f"centers={s['centers']} langs={s['languages']} "
          f"vault(live/purged)={s['vault_live']}/{s['vault_purged']}")
    print("status breakdown:", s["by_status"])
    print("\nlive matches for M1 (the family's report):")
    for m in find_matches("M1"):
        tag = "STRONG" if m["is_strong"] else "weak"
        print(f"  {m['case_id']} [{m['report_type']}] score={m['score']:5.1f} "
              f"[{tag}] @ {m['reporting_center']}  reasons={m['reasons']}")
