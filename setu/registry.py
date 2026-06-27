"""THE REGISTRY — the spine that breaks the silos.  [PERSON B owns this file]

One shared, live, time-windowed, retroactive, DE-IDENTIFIED pool backed by
SQLite with offline/sync fields. This is a WORKING MINIMAL base + a contract:
A (matcher) and C (dashboard) call these functions; B fleshes out the TODOs.

Contract used by the rest of the system (keep these signatures stable):
    init_db()
    add_record(record: Record) -> str            # returns case_id
    get_records(open_only=False, window_hours=None) -> list[Record]
    set_status(case_id, status)
    confirm_match(case_a, case_b, actor) -> audit line   # reveal-on-confirm
"""
from __future__ import annotations

import sqlite3
import datetime as _dt

from setu import config as C
from setu.ingest import Record, OPEN_STATUSES

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


def add_record(record: Record, db_path=C.REGISTRY_DB) -> str:
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
             record.report_type, record.vault_id, "local", _now(), 0),
        )
    return record.case_id


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


def get_records(open_only=False, window_hours=None, db_path=C.REGISTRY_DB) -> list[Record]:
    with _conn(db_path) as conn:
        rows = conn.execute("SELECT * FROM records").fetchall()
    recs = [_row_to_record(r) for r in rows]
    if open_only:
        recs = [r for r in recs if r.status.strip().lower() in OPEN_STATUSES]
    # TODO(B): time-window filter using reported_at + window_hours
    return recs


def set_status(case_id, status, db_path=C.REGISTRY_DB) -> None:
    with _conn(db_path) as conn:
        conn.execute("UPDATE records SET status=?, updated_at=? WHERE case_id=?",
                     (status, _now(), case_id))


def confirm_match(case_a, case_b, actor="operator", db_path=C.REGISTRY_DB) -> str:
    """Human-confirmed reunion: mark both Reunited (terminal) + audit line.
    Reveal-on-confirm of raw PII is done by the caller via privacy.reveal()."""
    set_status(case_a, "Reunited", db_path)
    set_status(case_b, "Reunited", db_path)
    from setu.privacy import audit
    audit("CONFIRM_MATCH", case_a=case_a, case_b=case_b, actor=actor)
    return f"confirmed {case_a} <-> {case_b}"


def seed_from_csv(db_path=C.REGISTRY_DB) -> int:
    """Load the 2,500 de-identified records into the registry."""
    from setu.ingest import load_records
    init_db(db_path)
    recs, _ = load_records()
    for r in recs:
        add_record(r, db_path)
    return len(recs)


# TODO(B) — phased work, see docs/PERSON_B_BACKEND.md:
#   * separate access-controlled VAULT_DB for raw name/mobile (not in records table)
#   * time-window query; retroactive re-match hook when a new report lands
#   * offline queue + sync/merge (UUID dedup, terminal-status-wins, LWW)
#   * purge raw PII post-reunion, keep the hash
#   * thin API (functions or FastAPI) the dashboard calls

if __name__ == "__main__":
    n = seed_from_csv()
    print(f"registry seeded: {n} records into {C.REGISTRY_DB.name}")
