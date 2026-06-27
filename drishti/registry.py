"""THE REGISTRY — the spine that breaks the silos.  [PERSON B owns this file]

One shared, live, time-windowed, retroactive, DE-IDENTIFIED pool backed by
SQLite with offline/sync fields. The `records` table holds ONLY hashes +
de-identified attributes; raw name/mobile live in the separate access-controlled
`drishti.vault` (see vault.py). A (matcher) and C (dashboard) call these functions.

Contract used by the rest of the system (keep these signatures stable):
    init_db()
    add_record(record: Record, *, rematch=True) -> str        # returns case_id
    get_records(open_only=False, window_hours=None, reference_time=None) -> list[Record]
    set_status(case_id, status)
    get_candidates(case_id) -> list[dict]                      # retroactive matches
    confirm_match(case_a, case_b, actor, reason) -> dict       # reveal-on-confirm + purge
    seed_from_csv() -> int
"""
from __future__ import annotations

import datetime as _dt
import json
import sqlite3

from drishti import config as C
from drishti.ingest import Record, OPEN_STATUSES

SCHEMA = """
CREATE TABLE IF NOT EXISTS records (
    case_id           TEXT PRIMARY KEY,
    reported_at       TEXT,
    gender            TEXT,
    age_band          TEXT,
    state             TEXT,
    district          TEXT,
    language          TEXT,
    last_seen_location TEXT,
    reporting_center  TEXT,
    physical_description TEXT,
    status            TEXT,
    name_hash         TEXT,
    mobile_hash       TEXT,
    is_duplicate_report INTEGER DEFAULT 0,
    report_type       TEXT DEFAULT 'missing',
    vault_id          TEXT,
    -- offline / sync fields (Person B: conflict resolution lives here)
    origin_node       TEXT DEFAULT 'local',
    updated_at        TEXT,
    synced            INTEGER DEFAULT 0
);

-- Retroactive re-match results: when a new report lands we score it against the
-- open pool and persist the top-k so the link survives and the UI can show it.
CREATE TABLE IF NOT EXISTS candidates (
    target_case    TEXT,
    candidate_case TEXT,
    score          REAL,
    is_strong      INTEGER DEFAULT 0,
    reasons        TEXT,          -- JSON
    created_at     TEXT,
    PRIMARY KEY (target_case, candidate_case)
);
"""


def _conn(db_path=C.REGISTRY_DB) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=C.REGISTRY_DB) -> None:
    with _conn(db_path) as conn:
        conn.executescript(SCHEMA)


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


# ----------------------------------------------------------------------------
# Write path
# ----------------------------------------------------------------------------
def add_record(record: Record, db_path=C.REGISTRY_DB, *,
               rematch: bool = True, origin_node: str = "local") -> str:
    """Insert/replace a de-identified record. If `rematch` and the record is
    open, immediately score it against the open pool and persist the top-k
    candidates (B2 — the live + retroactive behaviour). Bulk seeding passes
    rematch=False."""
    with _conn(db_path) as conn:
        conn.execute(
            """INSERT OR REPLACE INTO records
               (case_id, reported_at, gender, age_band, state, district, language,
                last_seen_location, reporting_center, physical_description, status,
                name_hash, mobile_hash, is_duplicate_report, report_type, vault_id,
                origin_node, updated_at, synced)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (record.case_id, record.reported_at, record.gender, record.age_band,
             record.state, record.district, record.language, record.last_seen_location,
             record.reporting_center, record.physical_description, record.status,
             record.name_hash, record.mobile_hash, int(record.is_duplicate_report),
             record.report_type, record.vault_id, origin_node, _now(), 0),
        )
    if rematch and record.is_open:
        rematch_record(record, db_path=db_path)
    return record.case_id


def rematch_record(record: Record, db_path=C.REGISTRY_DB, top_k: int = 3) -> list[dict]:
    """B2 — run the Tier-1 matcher for `record` against the open, time-windowed
    pool and persist the surfaced candidates. Fires *backward*: a FOUND report
    sitting open as bait gets linked the moment the family files anywhere.
    Returns the stored candidate dicts (also used by the dashboard)."""
    # local import: keeps seeding light and avoids any import-time matcher cost
    from drishti.matcher_tier1 import find_candidates

    pool = get_records(open_only=True, window_hours=C.TIME_WINDOW_HOURS,
                       reference_time=record.reported_at, db_path=db_path)
    results = find_candidates(record, pool, top_k=top_k, require_open=True)

    stored: list[dict] = []
    with _conn(db_path) as conn:
        for r in results:
            is_strong = int(r.score >= C.DUP_THRESHOLD)
            conn.execute(
                """INSERT OR REPLACE INTO candidates
                   (target_case, candidate_case, score, is_strong, reasons, created_at)
                   VALUES (?,?,?,?,?,?)""",
                (record.case_id, r.case_id, r.score, is_strong,
                 json.dumps(r.reasons), _now()),
            )
            stored.append({"target_case": record.case_id, "candidate_case": r.case_id,
                           "score": r.score, "is_strong": bool(is_strong),
                           "reasons": r.reasons})
    return stored


def set_status(case_id, status, db_path=C.REGISTRY_DB) -> None:
    with _conn(db_path) as conn:
        conn.execute("UPDATE records SET status=?, updated_at=? WHERE case_id=?",
                     (status, _now(), case_id))


# ----------------------------------------------------------------------------
# Read path
# ----------------------------------------------------------------------------
def _row_to_record(row: sqlite3.Row) -> Record:
    return Record(
        case_id=row["case_id"], reported_at=row["reported_at"], gender=row["gender"],
        age_band=row["age_band"], state=row["state"], district=row["district"],
        language=row["language"], last_seen_location=row["last_seen_location"],
        reporting_center=row["reporting_center"],
        physical_description=row["physical_description"], status=row["status"],
        name_hash=row["name_hash"], mobile_hash=row["mobile_hash"],
        is_duplicate_report=bool(row["is_duplicate_report"]),
        vault_id=row["vault_id"] or "", report_type=row["report_type"] or "missing",
    )


def _parse_dt(value: str | None) -> _dt.datetime | None:
    """Best-effort parse of a reported_at string. Returns None if unparseable
    (callers FAIL-OPEN on None so a format quirk never silently drops a case)."""
    s = (value or "").strip()
    if not s:
        return None
    s = s.replace("Z", "+00:00")
    try:
        return _dt.datetime.fromisoformat(s)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M",
                "%Y-%m-%d", "%d-%m-%Y %H:%M", "%d/%m/%Y %H:%M", "%d/%m/%Y"):
        try:
            return _dt.datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def get_records(open_only=False, window_hours=None, reference_time=None,
                db_path=C.REGISTRY_DB) -> list[Record]:
    """Return de-identified records.

    open_only      — keep only matchable (non-terminal) statuses.
    window_hours   — keep only reports within ±window_hours of the anchor time.
    reference_time — the anchor (a reported_at string or datetime). Defaults to
                     the most recent reported_at in the pool, so we only scan
                     plausible-overlap cases, never the whole historical pool.
    """
    with _conn(db_path) as conn:
        rows = conn.execute("SELECT * FROM records").fetchall()
    recs = [_row_to_record(r) for r in rows]
    if open_only:
        recs = [r for r in recs if r.status.strip().lower() in OPEN_STATUSES]

    if window_hours is not None:
        parsed = [(r, _parse_dt(r.reported_at)) for r in recs]
        if isinstance(reference_time, _dt.datetime):
            anchor = reference_time
        elif isinstance(reference_time, str):
            anchor = _parse_dt(reference_time)
        else:
            known = [dt for _, dt in parsed if dt is not None]
            anchor = max(known) if known else None
        if anchor is not None:
            span = _dt.timedelta(hours=window_hours)
            # FAIL-OPEN: keep records whose timestamp is unparseable.
            recs = [r for r, dt in parsed if dt is None or abs(dt - anchor) <= span]
    return recs


def get_candidates(case_id, db_path=C.REGISTRY_DB) -> list[dict]:
    """Retroactive matches touching `case_id`, in either direction, best first."""
    with _conn(db_path) as conn:
        rows = conn.execute(
            """SELECT target_case, candidate_case, score, is_strong, reasons, created_at
               FROM candidates WHERE target_case=? OR candidate_case=?
               ORDER BY score DESC""",
            (case_id, case_id)).fetchall()
    out = []
    for r in rows:
        out.append({
            "target_case": r["target_case"], "candidate_case": r["candidate_case"],
            "score": r["score"], "is_strong": bool(r["is_strong"]),
            "reasons": json.loads(r["reasons"]) if r["reasons"] else {},
            "created_at": r["created_at"],
            # the "other" case relative to the one asked about
            "other": r["candidate_case"] if r["target_case"] == case_id else r["target_case"],
        })
    return out


def _vault_id_for(case_id, db_path=C.REGISTRY_DB) -> str:
    with _conn(db_path) as conn:
        row = conn.execute("SELECT vault_id FROM records WHERE case_id=?",
                           (case_id,)).fetchone()
    return (row["vault_id"] if row and row["vault_id"] else case_id)


# ----------------------------------------------------------------------------
# Reveal-on-confirm (B4)
# ----------------------------------------------------------------------------
def confirm_match(case_a, case_b, actor="operator",
                  reason="human-confirmed reunion",
                  *, reveal=True, purge=True,
                  db_path=C.REGISTRY_DB, vault_path=C.VAULT_DB) -> dict:
    """Human-confirmed reunion. This is the ONLY place raw PII surfaces:

      1. mark both cases Reunited (terminal),
      2. REVEAL raw contact from the vault for the operator to act on (audited),
      3. PURGE raw PII from the vault, keeping the hash + a tombstone.

    Returns a dict with the revealed contact + audit line (the dashboard shows
    the contact at the moment of confirmation, then it's gone from storage).
    NOTE: return shape changed from a bare string to a dict (B4) — A/C consume
    the dict; see CONTEXT.md.
    """
    from drishti import vault as vaultmod
    from drishti.privacy import audit

    set_status(case_a, "Reunited", db_path)
    set_status(case_b, "Reunited", db_path)

    revealed: dict[str, dict] = {}
    purged: list[str] = []
    for case in (case_a, case_b):
        vid = _vault_id_for(case, db_path)
        if reveal:
            contact = vaultmod.get(vid, actor=actor, reason=reason, db_path=vault_path)
            if contact:
                revealed[case] = contact
        if purge:
            if vaultmod.purge(vid, actor=actor, db_path=vault_path):
                purged.append(case)

    audit("CONFIRM_MATCH", case_a=case_a, case_b=case_b, actor=actor)
    return {
        "summary": f"confirmed {case_a} <-> {case_b}",
        "revealed": revealed,     # {case_id: {missing_person_name, reporter_mobile}}
        "purged": purged,
        "actor": actor,
    }


# ----------------------------------------------------------------------------
# Seeding
# ----------------------------------------------------------------------------
def seed_from_csv(db_path=C.REGISTRY_DB, vault_path=C.VAULT_DB) -> int:
    """Load the de-identified records into the registry AND the raw PII into the
    separate access-controlled vault (B1 — the two stores never co-mingle)."""
    from drishti.ingest import load_records
    from drishti import vault as vaultmod

    init_db(db_path)
    recs, vault = load_records()
    for r in recs:
        add_record(r, db_path, rematch=False)   # bulk: defer matching to validate/UI
    vaultmod.seed_vault(vault, vault_path)
    return len(recs)


if __name__ == "__main__":
    from drishti import vault as vaultmod
    n = seed_from_csv()
    live, purged = vaultmod.count()
    print(f"registry seeded: {n} records into {C.REGISTRY_DB.name}")
    print(f"vault seeded:    {live} raw-PII rows into {C.VAULT_DB.name} "
          f"(separate, gitignored) | purged={purged}")
