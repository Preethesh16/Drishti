"""Load the 2,500 missing-person rows with a REAL CSV parser, de-identify them
(hash name + mobile), and emit canonical `Record` objects the matcher consumes.

Run directly:  python -m setu.ingest
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from setu import privacy
from setu.config import MISSING_CSV, MISSING_COLUMNS


# Open statuses still in play for matching (closed = Reunited, terminal).
OPEN_STATUSES = {"pending", "transferred to hospital", "unresolved"}


@dataclass
class Record:
    """A de-identified missing/found report. The matcher only ever sees this —
    never the raw name/mobile (those are hashed; raw stays in the vault)."""
    case_id: str
    reported_at: str
    gender: str
    age_band: str
    state: str
    district: str
    language: str
    last_seen_location: str
    reporting_center: str
    physical_description: str
    status: str
    # de-identified identifiers
    name_hash: str | None
    mobile_hash: str | None
    # ground-truth label for validation (NOT used by the matcher)
    is_duplicate_report: bool = False
    resolution_hours: float | None = None
    remarks: str = ""
    # vault key — raw PII fetched only on reveal-on-confirm
    vault_id: str = ""
    report_type: str = "missing"  # "missing" | "found"

    @property
    def is_open(self) -> bool:
        return (self.status or "").strip().lower() in OPEN_STATUSES


def _clean(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()


def _to_bool(v) -> bool:
    return _clean(v).lower() in {"true", "1", "yes", "y"}


def load_raw(path=MISSING_CSV) -> pd.DataFrame:
    """Real CSV parse (handles quoted commas in physical_description)."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing_cols = [c for c in MISSING_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"CSV at {path} is missing expected columns: {missing_cols}\n"
            f"Found: {list(df.columns)}"
        )
    return df


def build_records(df: pd.DataFrame) -> tuple[list[Record], dict[str, dict]]:
    """Return (de-identified records, vault) where vault[vault_id] holds raw PII.
    The vault is what Person B persists to an access-controlled store."""
    records: list[Record] = []
    vault: dict[str, dict] = {}
    for _, row in df.iterrows():
        case_id = _clean(row["case_id"])
        raw_name = _clean(row["missing_person_name"])
        raw_mobile = _clean(row["reporter_mobile"])

        vault[case_id] = {"missing_person_name": raw_name, "reporter_mobile": raw_mobile}

        rec = Record(
            case_id=case_id,
            reported_at=_clean(row["reported_at"]),
            gender=_clean(row["gender"]) or "Unknown",
            age_band=_clean(row["age_band"]),
            state=_clean(row["state"]),
            district=_clean(row["district"]),
            language=_clean(row["language"]),
            last_seen_location=_clean(row["last_seen_location"]),
            reporting_center=_clean(row["reporting_center"]),
            physical_description=_clean(row["physical_description"]),
            status=_clean(row["status"]),
            name_hash=privacy.hash_pii(raw_name),
            mobile_hash=privacy.hash_pii(raw_mobile),
            is_duplicate_report=_to_bool(row["is_duplicate_report"]),
            resolution_hours=float(row["resolution_hours"]) if _clean(row["resolution_hours"]) else None,
            remarks=_clean(row["remarks"]),
            vault_id=case_id,
        )
        records.append(rec)
    return records, vault


def load_records(path=MISSING_CSV) -> tuple[list[Record], dict[str, dict]]:
    return build_records(load_raw(path))


if __name__ == "__main__":
    recs, vault = load_records()
    dupes = sum(1 for r in recs if r.is_duplicate_report)
    no_name = sum(1 for r in recs if r.name_hash is None)
    no_mobile = sum(1 for r in recs if r.mobile_hash is None)
    open_n = sum(1 for r in recs if r.is_open)
    print(f"seeded {len(recs)} records (de-identified)")
    print(f"  duplicates (ground truth): {dupes}")
    print(f"  blank name (hashed->None): {no_name}")
    print(f"  blank mobile (hashed->None): {no_mobile}")
    print(f"  open cases (matchable): {open_n}")
    print(f"  vault entries (raw PII, access-controlled): {len(vault)}")
