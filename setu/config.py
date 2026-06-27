"""Central config: weights, thresholds, age order, model ids, column names.
Everything tunable lives here so the team tunes against the 202 duplicates
without hunting through code.
"""
from __future__ import annotations

import os
from pathlib import Path

# ----------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MISSING_CSV = DATA_DIR / "Synthetic_Missing_Persons_2500.csv"
CCTV_CSV = DATA_DIR / "CCTV_Locations.csv"
ZONES_CSV = DATA_DIR / "Zone_Boundaries.csv"
POLICE_CSV = DATA_DIR / "Police_Stations.csv"
CHOKE_CSV = DATA_DIR / "Chokepoints_Parking.csv"

REGISTRY_DB = ROOT / "registry.db"          # Person B: de-identified registry
VAULT_DB = ROOT / "setu_vault.db"           # Person B: access-controlled raw PII (gitignored)
AUDIT_LOG = ROOT / "audit.log"              # reveal-on-confirm audit trail

# ----------------------------------------------------------------------------
# Privacy
# ----------------------------------------------------------------------------
# HMAC salt for hashing name + mobile. Override via env in prod.
PII_SALT = os.environ.get("SETU_SALT", "dev-only-insecure-salt-change-me")

# ----------------------------------------------------------------------------
# Models (Claude is the brain; default cheap, escalate only when ambiguous)
# ----------------------------------------------------------------------------
MODEL_DEFAULT = "claude-sonnet-4-6"   # structuring, cross-lingual desc match, explanations
MODEL_HARD = "claude-opus-4-8"        # only for hard/ambiguous/dedup-tie cases

# ----------------------------------------------------------------------------
# Canonical CSV columns (verified against §3 of the spec)
# ----------------------------------------------------------------------------
MISSING_COLUMNS = [
    "case_id", "reported_at", "missing_person_name", "gender", "age_band",
    "state", "district", "language", "last_seen_location", "reporting_center",
    "reporter_mobile", "physical_description", "status", "resolution_hours",
    "is_duplicate_report", "remarks",
]

# ----------------------------------------------------------------------------
# Matching: scoring weights (§8). Raw -> 0..100 via MAX_RAW.
# ----------------------------------------------------------------------------
W_LANG = 30          # language equal
W_AGE_SAME = 15      # same age band
W_AGE_ADJ = 7        # adjacent age band (±1)
W_GENDER = 10        # gender equal
W_GENDER_UNK = 5     # one side Unknown
W_GEO_SAME = 25      # same last_seen_location (coarse; geo.py refines later)
W_GEO_DIFF = 4       # different location, small baseline
W_DESC = 35          # × description similarity in [0,1]
W_STATE = 10         # state equal
W_DISTRICT = 5       # district equal

# Max achievable raw score, used to normalise to 0..100.
MAX_RAW = W_LANG + W_AGE_SAME + W_GENDER + W_GEO_SAME + W_DESC + W_STATE + W_DISTRICT  # 130

# Gate / threshold tuning
AGE_BAND_GATE = 1          # candidates must be within ±1 age band
DUP_THRESHOLD = 55         # normalised score >= this => "same person" (tune vs the 202)
TIME_WINDOW_HOURS = 72     # only match within a plausible time window (registry use)

# ----------------------------------------------------------------------------
# Age bands, ordered youngest -> oldest (adjacency = |index diff| == 1)
# ----------------------------------------------------------------------------
AGE_ORDER = ["0-12", "13-17", "18-40", "41-60", "61-70", "71-80", "80+"]
AGE_INDEX = {band: i for i, band in enumerate(AGE_ORDER)}

# Values that mean "not provided / unknown"
UNKNOWN_TOKENS = {"", "unknown", "n/a", "na", "none", "nan", "-"}

# Geographic extent of Nashik Kumbh data (from KMLs), for map bounds.
GEO_BOUNDS = {"lat_min": 19.93, "lat_max": 20.08, "lng_min": 73.71, "lng_max": 73.89}
