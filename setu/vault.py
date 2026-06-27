"""THE VAULT — access-controlled store for raw PII.  [PERSON B owns this file]

Structural privacy means the registry that *finds* people never holds the data
that *identifies* them. Raw `missing_person_name` / `reporter_mobile` live ONLY
here, in a separate SQLite file (gitignored, mode 0600), keyed by `vault_id`.
The `records` table in the registry holds only hashes + de-identified attributes.

Raw values surface exactly once — at a human-confirmed reunion — via `get()`,
which writes an audit line. After reunion the row is `purge()`d: raw PII is
deleted, a tombstone (the hash + timestamps) is kept so we can prove it existed
and was destroyed. A `consent` flag captured at intake gates the reveal.

    init_vault()
    put(vault_id, name, mobile, *, consent=True)
    get(vault_id, *, actor, reason)        -> {"missing_person_name", "reporter_mobile"} | {}
    purge(vault_id, *, actor)              -> bool   (raw deleted, tombstone kept)
    seed_vault(vault: dict[str, dict])     -> int    (bulk-load ingest's vault)
"""
from __future__ import annotations

import datetime as _dt
import os
import sqlite3

from setu import config as C
from setu import privacy

SCHEMA = """
CREATE TABLE IF NOT EXISTS vault (
    vault_id   TEXT PRIMARY KEY,
    name       TEXT,
    mobile     TEXT,
    consent    INTEGER DEFAULT 1,
    purged     INTEGER DEFAULT 0,
    created_at TEXT,
    purged_at  TEXT
);
"""


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _conn(db_path=C.VAULT_DB) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_vault(db_path=C.VAULT_DB) -> None:
    """Create the vault DB and lock it to owner-only (0600) where supported."""
    with _conn(db_path) as conn:
        conn.executescript(SCHEMA)
    try:  # best-effort access control; symbolic on filesystems without POSIX modes
        os.chmod(db_path, 0o600)
    except OSError:  # pragma: no cover
        pass


def put(vault_id: str, name: str | None, mobile: str | None,
        *, consent: bool = True, db_path=C.VAULT_DB) -> str:
    """Store raw PII for one case. Blank values are kept as '' (still keyed)."""
    init_vault(db_path)
    with _conn(db_path) as conn:
        conn.execute(
            """INSERT OR REPLACE INTO vault
               (vault_id, name, mobile, consent, purged, created_at, purged_at)
               VALUES (?,?,?,?,0,?,NULL)""",
            (vault_id, (name or "").strip(), (mobile or "").strip(),
             int(consent), _now()),
        )
    return vault_id


def seed_vault(vault: dict[str, dict], db_path=C.VAULT_DB) -> int:
    """Bulk-load the vault dict that `setu.ingest.load_records()` returns."""
    init_vault(db_path)
    n = 0
    with _conn(db_path) as conn:
        for vid, raw in vault.items():
            conn.execute(
                """INSERT OR REPLACE INTO vault
                   (vault_id, name, mobile, consent, purged, created_at, purged_at)
                   VALUES (?,?,?,1,0,?,NULL)""",
                (vid, (raw.get("missing_person_name") or "").strip(),
                 (raw.get("reporter_mobile") or "").strip(), _now()),
            )
            n += 1
    return n


def has_consent(vault_id: str, db_path=C.VAULT_DB) -> bool:
    with _conn(db_path) as conn:
        row = conn.execute("SELECT consent FROM vault WHERE vault_id=?",
                           (vault_id,)).fetchone()
    return bool(row and row["consent"])


def is_purged(vault_id: str, db_path=C.VAULT_DB) -> bool:
    with _conn(db_path) as conn:
        row = conn.execute("SELECT purged FROM vault WHERE vault_id=?",
                           (vault_id,)).fetchone()
    return bool(row and row["purged"])


def get(vault_id: str, *, actor: str, reason: str, db_path=C.VAULT_DB) -> dict:
    """Reveal raw PII for `vault_id`. THE access-controlled read: every call
    writes a REVEAL audit line. Returns {} if missing, purged, or no consent."""
    with _conn(db_path) as conn:
        row = conn.execute(
            "SELECT name, mobile, consent, purged FROM vault WHERE vault_id=?",
            (vault_id,)).fetchone()
    if row is None or row["purged"] or not row["consent"]:
        privacy.audit("REVEAL_DENIED", vault_id=vault_id, actor=actor,
                      reason=reason,
                      cause=("missing" if row is None else
                             "purged" if row["purged"] else "no_consent"))
        return {}
    fields = {"missing_person_name": row["name"], "reporter_mobile": row["mobile"]}
    # privacy.reveal writes the audit line (who revealed what, when, why)
    return privacy.reveal(vault_id, fields, actor=actor, reason=reason)


def purge(vault_id: str, *, actor: str, db_path=C.VAULT_DB) -> bool:
    """Destroy raw PII post-reunion; keep a tombstone (purged=1) + audit line.
    Idempotent: returns False if there was nothing to purge."""
    with _conn(db_path) as conn:
        row = conn.execute("SELECT purged FROM vault WHERE vault_id=?",
                           (vault_id,)).fetchone()
        if row is None or row["purged"]:
            return False
        conn.execute(
            "UPDATE vault SET name='', mobile='', purged=1, purged_at=? WHERE vault_id=?",
            (_now(), vault_id))
    privacy.audit("PURGE", vault_id=vault_id, actor=actor)
    return True


def count(db_path=C.VAULT_DB) -> tuple[int, int]:
    """Return (live_rows, purged_rows)."""
    with _conn(db_path) as conn:
        live = conn.execute("SELECT COUNT(*) c FROM vault WHERE purged=0").fetchone()["c"]
        purged = conn.execute("SELECT COUNT(*) c FROM vault WHERE purged=1").fetchone()["c"]
    return live, purged


if __name__ == "__main__":
    # Tiny self-check (no real data needed).
    import tempfile
    from pathlib import Path

    tmp = Path(tempfile.mkdtemp()) / "vault_demo.db"
    put("C1", "Asha Devi", "9876543210", db_path=tmp)
    put("C2", "Ramu", "", consent=False, db_path=tmp)
    print("seeded:", count(tmp))
    print("reveal C1:", get("C1", actor="operator", reason="reunion", db_path=tmp))
    print("reveal C2 (no consent):", get("C2", actor="operator", reason="x", db_path=tmp))
    print("purge C1:", purge("C1", actor="operator", db_path=tmp))
    print("reveal C1 after purge:", get("C1", actor="operator", reason="x", db_path=tmp))
    print("counts (live, purged):", count(tmp))
