"""Generate 50 Nashik Kumbh help-booth pin-points on a ~500m grid (real coords),
plus a CCTV layout (dense core, sparse edges) for the blind-spot map.

Booths are the only pins — every reporter is within ~500m of one, and each has a
readable name so people can report "near West Hall". No hardcoded landmarks.

Writes data/nashik_landmarks.csv (name, lat, lng, type='booth') and
data/nashik_cctv.csv (camera_id, lat, lng).  Run: python scripts/make_nashik_geo.py [--force]
"""
from __future__ import annotations

import csv
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "nashik_landmarks.csv"
CCTV_OUT = ROOT / "data" / "nashik_cctv.csv"
_rng = random.Random(73)

# ~500m grid over the Panchavati/Ramkund core (real Nashik coordinates).
LAT0, DLAT, NROWS = 19.9850, 0.0045, 7      # ~500m steps
LNG0, DLNG, NCOLS = 73.7790, 0.0039, 8
N_BOOTHS = 50

# 50 readable booth names so reporters can say "near <name>".
BOOTH_NAMES = [
    "North Gate", "North Hall", "North Sangam", "North Transit", "North Watch",
    "North Camp", "North Food Court", "North Parking",
    "West Gate", "West Hall", "West Ghat Walk", "West Seva Booth", "Riverside West",
    "West Akhara", "West Medical Post", "West Help Hall",
    "Central Plaza", "Central Bhajan Hall", "Central Annakshetra", "Central Help Hall",
    "Central Watch Tower", "Banana Point", "Loudspeaker Post", "Volunteer Tent",
    "East Gate", "East Hall", "East Ghat Walk", "East Akhara Camp", "Riverside East",
    "East Help Post", "East Food Court", "East Transit",
    "South Gate", "South Hall", "South Transit", "South Parking Cross", "South Watch",
    "South Camp", "South Belt", "South Medical Post",
    "Snan Ghat 1", "Snan Ghat 2", "Snan Ghat 3", "Sangam Gate", "Outer Camp",
    "Transit Point", "Parking Belt", "Dharamshala Block", "Mukti Naka", "Saptashrungi Stand",
]


def grid():
    pts = []
    for r in range(NROWS):
        for c in range(NCOLS):
            pts.append((round(LAT0 + r * DLAT, 5), round(LNG0 + c * DLNG, 5)))
    return pts[:N_BOOTHS]


def write_booths(force=False):
    if OUT.exists() and not force:
        print(f"!! {OUT.name} exists — not clobbering. Use --force.")
        return None
    OUT.parent.mkdir(exist_ok=True)
    pts = grid()
    rows = []
    for i, (la, lo) in enumerate(pts):
        name = BOOTH_NAMES[i] if i < len(BOOTH_NAMES) else f"Booth {i + 1:02d}"
        rows.append({"name": name, "lat": la, "lng": lo, "type": "booth"})
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["name", "lat", "lng", "type"])
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} booth pin-points (~500m grid) -> {OUT}")
    return rows


def write_cctv(booths, force=False):
    """Cameras: DENSE around the central booths, SPARSE at the edges → blind spots emerge."""
    if CCTV_OUT.exists() and not force:
        return
    # central booths = the dense-camera core; edges stay thin
    clat = sum(b["lat"] for b in booths) / len(booths)
    clng = sum(b["lng"] for b in booths) / len(booths)
    core = sorted(booths, key=lambda b: (b["lat"] - clat) ** 2 + (b["lng"] - clng) ** 2)[:6]
    cams, cid = [], 0
    for b in core:
        for _ in range(_rng.randint(7, 11)):
            cid += 1
            cams.append((f"CAM{cid:04d}", round(b["lat"] + _rng.uniform(-0.0014, 0.0014), 6),
                         round(b["lng"] + _rng.uniform(-0.0014, 0.0014), 6)))
    for _ in range(16):                     # a few sparse outer cameras
        cid += 1
        cams.append((f"CAM{cid:04d}", round(_rng.uniform(LAT0, LAT0 + NROWS * DLAT), 6),
                     round(_rng.uniform(LNG0, LNG0 + NCOLS * DLNG), 6)))
    with open(CCTV_OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["camera_id", "lat", "lng"])
        w.writerows(cams)
    print(f"wrote {len(cams)} CCTV cameras (dense core, sparse edges) -> {CCTV_OUT}")


def main(force=False):
    booths = write_booths(force)
    if booths:
        write_cctv(booths, force)


if __name__ == "__main__":
    main(force="--force" in sys.argv)
