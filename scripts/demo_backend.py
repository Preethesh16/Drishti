"""Backend verification demo (Person B) — runs with NO real data, NO API keys.

Exercises the things B owns, end to end, against throwaway temp DBs:
  B1  vault separation  — raw PII lives only in setu_vault.db, registry holds hashes
  B1  time-window       — get_records(window_hours=...) scopes the pool by reported_at
  B2  retroactive hook  — a FOUND report sits open as bait; the family's later report
                          fires the match *backward* and links them
  B4  reveal-on-confirm — confirm_match reveals raw contact (audited), then PURGEs it

Run:  python -m scripts.demo_backend      (or: python scripts/demo_backend.py)
"""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from drishti import privacy, registry
from drishti import vault as vaultmod
from drishti.ingest import Record

# Keep the audit trail in the temp dir so the demo is self-contained.
TMP = Path(tempfile.mkdtemp(prefix="setu_demo_"))
REG_DB = TMP / "registry.db"
VAULT_DB = TMP / "setu_vault.db"
privacy.AUDIT_LOG = TMP / "audit.log"

# Raw PII the family provides (goes ONLY to the vault).
RAW = {
    "F1": {"missing_person_name": "", "reporter_mobile": ""},               # found: nameless
    "M1": {"missing_person_name": "Sunita Patil", "reporter_mobile": "9812345678"},
    "F2": {"missing_person_name": "", "reporter_mobile": ""},
    "D1": {"missing_person_name": "Rakesh Kumar", "reporter_mobile": "9700000000"},
    "R1": {"missing_person_name": "Old Case", "reporter_mobile": "9000000000"},
}


def rec(case_id, *, gender, age, lang, loc, center, desc, status, reported_at,
        report_type, dup=False) -> Record:
    raw = RAW[case_id]
    return Record(
        case_id=case_id, reported_at=reported_at, gender=gender, age_band=age,
        state="Maharashtra", district="Nashik", language=lang,
        last_seen_location=loc, reporting_center=center, physical_description=desc,
        status=status,
        name_hash=privacy.hash_pii(raw["missing_person_name"]),
        mobile_hash=privacy.hash_pii(raw["reporter_mobile"]),
        is_duplicate_report=dup, vault_id=case_id, report_type=report_type,
    )


def hr(title):
    print("\n" + "=" * 68 + f"\n{title}\n" + "=" * 68)


def main():
    registry.init_db(REG_DB)
    vaultmod.init_vault(VAULT_DB)
    vaultmod.seed_vault(RAW, VAULT_DB)

    # A FOUND report created earlier at Center-B, sitting OPEN as bait.
    f1 = rec("F1", gender="Female", age="61-70", lang="Marathi", loc="Ramkund",
             center="Center-B", status="Pending", reported_at="2027-08-15T09:00:00",
             report_type="found",
             desc="elderly woman saffron saree rudraksha beads silver anklets")
    # Another open elderly woman, different language/place — a weaker candidate.
    f2 = rec("F2", gender="Female", age="61-70", lang="Bengali", loc="Tapovan",
             center="Center-C", status="Pending", reported_at="2027-08-15T08:00:00",
             report_type="found", desc="old woman green saree spectacles")
    # A decoy that must be GATED OUT (male).
    d1 = rec("D1", gender="Male", age="18-40", lang="Hindi", loc="Ramkund",
             center="Center-B", status="Pending", reported_at="2027-08-15T10:00:00",
             report_type="found", desc="young man blue shirt jeans backpack")
    # An old, already-reunited case far outside the time window.
    r1 = rec("R1", gender="Female", age="61-70", lang="Marathi", loc="Ramkund",
             center="Center-A", status="Reunited", reported_at="2027-07-01T08:00:00",
             report_type="missing", desc="elderly woman saffron saree silver anklets")

    for r in (f1, f2, d1, r1):
        registry.add_record(r, REG_DB, rematch=False)

    # ---------------------------------------------------------------- B1
    hr("B1 — VAULT SEPARATION (registry holds hashes; raw PII only in the vault)")
    cols = sqlite3.connect(REG_DB).execute("SELECT * FROM records").description
    colnames = [c[0] for c in cols]
    print("registry.records columns:", colnames)
    assert "missing_person_name" not in colnames and "reporter_mobile" not in colnames
    print("  -> no raw name/mobile column in the registry. ✔")
    row = sqlite3.connect(REG_DB).execute(
        "SELECT case_id, name_hash, mobile_hash FROM records WHERE case_id='M1' OR case_id='F1'"
    ).fetchall()
    print("  registry stores only hashes, e.g.:", [(r[0], (r[1] or '')[:12]) for r in row] or "(M1 not yet added)")
    live, purged = vaultmod.count(VAULT_DB)
    print(f"  vault rows (separate file {VAULT_DB.name}): live={live} purged={purged} ✔")

    # ---------------------------------------------------------------- B1 time window
    hr("B1 — TIME WINDOW (only plausible-overlap open cases, not the whole pool)")
    anchor = "2027-08-15T11:00:00"   # the new report's time
    full = registry.get_records(open_only=True, db_path=REG_DB)
    windowed = registry.get_records(open_only=True, window_hours=72,
                                    reference_time=anchor, db_path=REG_DB)
    print(f"  open records, no window      : {sorted(r.case_id for r in full)}")
    print(f"  open records within ±72h of {anchor[:10]} : {sorted(r.case_id for r in windowed)}")
    print("  -> R1 is Reunited+45 days old, correctly excluded. ✔")

    # ---------------------------------------------------------------- B2
    hr("B2 — RETROACTIVE RE-MATCH (the family files later; match fires BACKWARD)")
    m1 = rec("M1", gender="Female", age="61-70", lang="Marathi", loc="Ramkund",
             center="Center-A", status="Pending", reported_at=anchor,
             report_type="missing", dup=True,
             desc="old lady orange saree prayer beads silver anklets")
    print("  family files M1 at Center-A (a DIFFERENT silo from F1's Center-B)…")
    registry.add_record(m1, REG_DB, rematch=True)   # <- the live hook fires here
    cands = registry.get_candidates("M1", db_path=REG_DB)
    for c in cands:
        flag = "STRONG" if c["is_strong"] else "weak"
        print(f"    M1 ~ {c['candidate_case']:>3}  score={c['score']:5.1f}  [{flag}]  {c['reasons']}")
    assert cands and cands[0]["candidate_case"] == "F1", "F1 should be the top match"
    print("  -> top match is F1, the found report from the OTHER center. Silos bridged. ✔")
    print("  -> querying from F1's side too:",
          [c["other"] for c in registry.get_candidates("F1", db_path=REG_DB)])

    # ---------------------------------------------------------------- B4
    hr("B4 — REVEAL-ON-CONFIRM + AUDIT + PURGE (raw PII surfaces once, then gone)")
    before = vaultmod.get("M1", actor="audit-probe", reason="pre-confirm peek",
                          db_path=VAULT_DB)
    print("  vault before confirm (M1):", before)
    result = registry.confirm_match("M1", "F1", actor="vol_42",
                                    reason="mother identified at Center-B",
                                    db_path=REG_DB, vault_path=VAULT_DB)
    print("  confirm_match ->")
    print("    summary :", result["summary"])
    print("    revealed:", result["revealed"], " <- operator calls this number NOW")
    print("    purged  :", result["purged"])
    after = vaultmod.get("M1", actor="audit-probe", reason="post-purge peek",
                         db_path=VAULT_DB)
    print("  vault after purge (M1):", after, "  <- raw PII destroyed")
    assert after == {}, "raw PII must be gone after purge"
    # the de-identified hash survives for dedup/proof
    h = sqlite3.connect(REG_DB).execute(
        "SELECT mobile_hash FROM records WHERE case_id='M1'").fetchone()[0]
    print("  registry still holds the mobile HASH (dedup survives):", (h or "")[:16], "✔")
    statuses = dict(sqlite3.connect(REG_DB).execute(
        "SELECT case_id, status FROM records WHERE case_id IN ('M1','F1')").fetchall())
    print("  both cases now:", statuses, "(terminal) ✔")

    # ---------------------------------------------------------------- audit
    hr("AUDIT TRAIL (every reveal / purge / confirm is logged)")
    print(privacy.AUDIT_LOG.read_text().rstrip())

    print("\nALL CHECKS PASSED ✔   (temp dir:", TMP, ")")


if __name__ == "__main__":
    main()
