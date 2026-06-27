"""Generate a realistic STAND-IN dataset matching the official spec, so the
pipeline + demo run before the official file lands. Synthetic, no real PII.

Writes data/Synthetic_Missing_Persons_2500.csv (won't clobber an existing file
unless --force). Replace with the official hackathon file when you have it.

Run:  python scripts/make_demo_data.py [--force]
"""
from __future__ import annotations

import csv
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "Synthetic_Missing_Persons_2500.csv"

rng = random.Random(2027)

COLUMNS = ["case_id", "reported_at", "missing_person_name", "gender", "age_band",
           "state", "district", "language", "last_seen_location", "reporting_center",
           "reporter_mobile", "physical_description", "status", "resolution_hours",
           "is_duplicate_report", "remarks"]

# distributions roughly per spec §3
LANGUAGES = (["Hindi"] * 271 + ["Bengali"] * 261 + ["Kannada"] * 261 + ["Maithili"] * 256 +
             ["Gujarati"] * 250 + ["Telugu"] * 248 + ["Bhojpuri"] * 245 + ["Awadhi"] * 241)
AGE_BANDS = (["61-70"] * 697 + ["71-80"] * 532 + ["41-60"] * 506 + ["18-40"] * 252 +
             ["80+"] * 225 + ["0-12"] * 201 + ["13-17"] * 87)
AGE_ORDER = ["0-12", "13-17", "18-40", "41-60", "61-70", "71-80", "80+"]

LOCATIONS = ["Madsangvi Transit", "Sadhugram Gate 2", "Ramkund Ghat", "Nashik Road Station",
             "Trimbak Road", "Gauri Patangan", "Dasak Ghat", "Adgaon Parking",
             "Tapovan", "Kapaleshwar Mandir", "Panchavati", "Saptashrungi Base",
             "Kalaram Mandir", "Someshwar", "Gangapur Road", "CBS Stand",
             "Trimbakeshwar Gate", "Sadhugram Gate 5", "Mukti Dham", "Nandur Naka"]
CENTERS = ["Adgaon Kho-Ya-Paya", "Bharat Bharati Control Room", "Central Control Room",
           "Nashik Road Center", "Panchavati Center", "Police Main Control Room",
           "Rajur Bahula Center", "Ramkund Kho-Ya-Paya Kendra", "Sadhugram Lost Found",
           "Trimbakeshwar Kho-Ya-Paya Kendra"]
HOME = [("Uttar Pradesh", "Varanasi"), ("Bihar", "Madhubani"), ("West Bengal", "Murshidabad"),
        ("Karnataka", "Belagavi"), ("Gujarat", "Surat"), ("Telangana", "Warangal"),
        ("Maharashtra", "Nashik"), ("Madhya Pradesh", "Rewa"), ("Rajasthan", "Kota"),
        ("Jharkhand", "Dhanbad")]
STATUSES = ["Reunited"] * 2150 + ["Pending"] * 210 + ["Transferred to hospital"] * 73 + ["Unresolved"] * 67

GARMENT = ["white kurta", "saffron robe", "blue saree", "green sari", "brown dhoti",
           "checked shirt", "grey sweater", "yellow blouse", "maroon shawl"]
ACCESSORY = ["rudraksha mala", "gold bangles", "wooden walking stick", "thick spectacles",
             "a cloth bag", "silver anklets", "a saffron tilak", "a steel kada"]
TRAIT = ["hard of hearing", "limps on the right leg", "cannot remember name",
         "speaks very little", "a mole on the cheek", "white beard", "partially blind",
         "confused and disoriented"]
# synonym swaps a *second* reporter might use (forces real cross-wording matching)
SYN = {"saffron robe": "orange clothes", "rudraksha mala": "prayer beads",
       "thick spectacles": "glasses", "wooden walking stick": "wooden stick",
       "hard of hearing": "cannot hear well", "white kurta": "white shirt-kurta"}
NAMES = ["Ramesh Kumar", "Sita Devi", "Lakshmi Bai", "Govind Singh", "Anita Sharma",
         "Mohan Lal", "Radha Yadav", "Suresh Patil", "Kamala Das", "Vijay Mehta"]


def make_desc(rng):
    parts = [f"wearing {rng.choice(GARMENT)}",
             f"carries {rng.choice(ACCESSORY)}",
             rng.choice(TRAIT)]
    rng.shuffle(parts)
    return ", ".join(parts)


def paraphrase(desc, rng):
    """How a *different* reporter would describe the same person: swap synonyms,
    drop a clause, reorder. This is what makes matching non-trivial."""
    clauses = desc.split(", ")
    out = []
    for c in clauses:
        for k, v in SYN.items():
            if k in c:
                c = c.replace(k, v)
        out.append(c)
    if len(out) > 2 and rng.random() < 0.6:
        out.pop(rng.randrange(len(out)))
    rng.shuffle(out)
    return ", ".join(out)


def adj_band(band, rng):
    i = AGE_ORDER.index(band)
    opts = [j for j in (i - 1, i + 1) if 0 <= j < len(AGE_ORDER)]
    return AGE_ORDER[rng.choice(opts)] if opts else band


def main(force=False):
    if OUT.exists() and not force:
        print(f"!! {OUT.name} already exists — not clobbering. Use --force to regenerate.")
        return
    OUT.parent.mkdir(exist_ok=True)

    N_BASE = 2298           # base people; + ~202 duplicates ≈ 2500
    N_DUP = 202
    mobile = 9000000000
    rows = []
    base_people = []

    for i in range(N_BASE):
        gender = rng.choice(["Male", "Female"])
        state, district = rng.choice(HOME)
        mobile += rng.randint(1, 7777)
        status = rng.choice(STATUSES)
        name = "" if rng.random() < 0.15 else rng.choice(NAMES)
        p = {
            "case_id": f"KS{i:05d}",
            "reported_at": f"2027-08-{rng.randint(10, 30):02d} {rng.randint(6,21):02d}:{rng.randint(0,59):02d}",
            "missing_person_name": name,
            "gender": gender,
            "age_band": rng.choice(AGE_BANDS),
            "state": state, "district": district,
            "language": rng.choice(LANGUAGES),
            "last_seen_location": rng.choice(LOCATIONS),
            "reporting_center": rng.choice(CENTERS),
            "reporter_mobile": "" if rng.random() < 0.20 else str(mobile),
            "physical_description": make_desc(rng),
            "status": status,
            "resolution_hours": f"{rng.uniform(0.5, 60):.1f}" if status == "Reunited" else "",
            "is_duplicate_report": "False",
            "remarks": rng.choice(["", "", "family searching", "elderly, needs care",
                                   "child, scared", "lost husband", "came with group"]),
        }
        rows.append(p)
        base_people.append(p)

    # inject realistic duplicates: SAME person, different center, dropped name,
    # paraphrased description, sometimes adjacent age/location, new unique mobile.
    dup_sources = rng.sample(base_people, N_DUP)
    for k, src in enumerate(dup_sources):
        mobile += rng.randint(1, 7777)
        center = rng.choice([c for c in CENTERS if c != src["reporting_center"]])
        age = src["age_band"] if rng.random() < 0.8 else adj_band(src["age_band"], rng)
        loc = src["last_seen_location"] if rng.random() < 0.6 else rng.choice(LOCATIONS)
        rows.append({
            "case_id": f"KS9{k:04d}",
            "reported_at": f"2027-08-{rng.randint(10, 30):02d} {rng.randint(6,21):02d}:{rng.randint(0,59):02d}",
            "missing_person_name": "",                      # second reporter rarely has the name
            "gender": src["gender"],
            "age_band": age,
            "state": src["state"], "district": src["district"],
            "language": src["language"],
            "last_seen_location": loc,
            "reporting_center": center,
            "reporter_mobile": "" if rng.random() < 0.20 else str(mobile),
            "physical_description": paraphrase(src["physical_description"], rng),
            "status": rng.choice(["Pending", "Reunited", "Transferred to hospital"]),
            "resolution_hours": "",
            "is_duplicate_report": "True",                  # ground-truth label
            "remarks": "possible duplicate of an earlier report",
        })

    rng.shuffle(rows)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows ({N_DUP} hidden duplicates) -> {OUT}")
    print("   ⚠️ STAND-IN demo data. Replace with the official file when available.")


if __name__ == "__main__":
    main(force="--force" in sys.argv)
