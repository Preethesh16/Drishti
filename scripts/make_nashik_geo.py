"""Generate Nashik Kumbh landmarks + a ~500m booth grid on REAL coordinates.

Writes data/nashik_landmarks.csv (name, lat, lng, type). 'landmark' = a real,
recognisable spot people report against ("near Ramkund"); 'booth' = a staffed
help-booth on a ~500m grid so every reporter is within ~500m of one. Stand-in
until official zone/KML geometry lands; coordinates are real Nashik locations.

Run:  python scripts/make_nashik_geo.py [--force]
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "nashik_landmarks.csv"

# Real, recognisable Nashik Kumbh landmarks (people report "near <these>").
LANDMARKS = [
    ("Ramkund Ghat", 19.9975, 73.7898),
    ("Kalaram Mandir", 19.9986, 73.7889),
    ("Kapaleshwar Mandir", 19.9969, 73.7905),
    ("Sundarnarayan Temple", 19.9958, 73.7878),
    ("Tapovan Sangam", 20.0086, 73.8047),
    ("Sadhugram Camp", 20.0050, 73.8005),
    ("CBS Bus Stand", 19.9975, 73.7860),
    ("Panchavati Karyalay", 19.9990, 73.7892),
    ("Someshwar", 20.0123, 73.7456),
    ("Trimbak Naka", 19.9905, 73.7660),
    ("Nashik Road Station", 19.9457, 73.8377),
    ("Dwarka Circle", 19.9846, 73.7945),
    ("Gadge Maharaj Bridge", 19.9963, 73.7882),
    ("Mukti Dham", 19.9447, 73.8312),
]

# Friendly, directional booth names so reporters can say "near West Hall".
BOOTH_NAMES = [
    "North Gate", "North Hall", "North Sangam", "North Transit", "North Watch",
    "West Hall", "West Gate", "West Ghat Walk", "West Seva Booth", "West Food Court",
    "East Hall", "East Gate", "East Ghat Walk", "East Akhara Camp", "East Help Post",
    "South Gate", "South Hall", "South Transit", "South Parking Cross", "South Watch",
    "Central Plaza", "Central Bhajan Hall", "Central Annakshetra", "Central Help Hall",
    "Banana Point", "River Walk", "Dharamshala Block", "Loudspeaker Post",
    "Snan Ghat 1", "Snan Ghat 2", "Snan Ghat 3", "Sangam Gate", "Akhara Camp 2",
    "Transit Point", "Parking Belt", "Outer Camp", "Volunteer Tent", "Medical Post",
]

# ~500m booth grid over the Panchavati/Ramkund core.
# 500m ≈ 0.0045° lat, ≈ 0.0048° lng at this latitude.
LAT0, LAT1, DLAT = 19.9880, 20.0125, 0.0045
LNG0, LNG1, DLNG = 73.7800, 73.8060, 0.0048


def grid_points():
    pts = []
    lat = LAT0
    while lat <= LAT1 + 1e-9:
        lng = LNG0
        while lng <= LNG1 + 1e-9:
            pts.append((round(lat, 5), round(lng, 5)))
            lng += DLNG
        lat += DLAT
    return pts


def main(force=False):
    if OUT.exists() and not force:
        print(f"!! {OUT.name} exists — not clobbering. Use --force.")
        return
    OUT.parent.mkdir(exist_ok=True)
    rows = [{"name": n, "lat": la, "lng": lo, "type": "landmark"} for n, la, lo in LANDMARKS]

    pts = grid_points()
    for i, (la, lo) in enumerate(pts):
        if i < len(BOOTH_NAMES):
            name = BOOTH_NAMES[i]
        else:
            name = f"Sector {chr(65 + i // 6)}{i % 6 + 1} Booth"
        rows.append({"name": name, "lat": la, "lng": lo, "type": "booth"})

    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["name", "lat", "lng", "type"])
        w.writeheader()
        w.writerows(rows)
    n_booth = sum(1 for r in rows if r["type"] == "booth")
    print(f"wrote {len(rows)} points ({len(LANDMARKS)} landmarks + {n_booth} booths "
          f"on ~500m grid) -> {OUT}")


if __name__ == "__main__":
    main(force="--force" in sys.argv)
