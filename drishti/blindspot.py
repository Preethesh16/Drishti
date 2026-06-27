"""Blind-spot map — WHERE to place help (additive intelligence, pre-event).

Overlay crowd-separation PRESSURE against CCTV COVERAGE. High pressure × low
camera coverage = where people vanish unseen → place kiosks/volunteers THERE
before the snan surge. Also answers the honest question "how does a wandering
person become a found record?" — by putting the catch-points where the data says
separations cluster.

Pressure here is a transparent heuristic from booth type/role (transit/parking/
gate/edge points funnel crowds → high pressure; temples/ghats medium). With the
official last_seen clusters + CCTV feed this swaps in real numbers.

Run:  python -m drishti.blindspot
"""
from __future__ import annotations

import csv

from drishti import geo

CCTV_CSV = geo.C.DATA_DIR / "nashik_cctv.csv"
COVERAGE_RADIUS_M = 250          # a camera "covers" points within this radius

# crowd-separation pressure by what a point is (funnels = high)
HIGH = ("gate", "transit", "parking", "cross", "belt", "outer", "station", "naka", "stand", "sangam")
MED = ("ghat", "mandir", "temple", "plaza", "hall", "ramkund", "tapovan")


def load_cameras(path=CCTV_CSV) -> list[tuple[float, float]]:
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            return [(float(r["lat"]), float(r["lng"])) for r in csv.DictReader(fh)]
    except FileNotFoundError:
        return []


def _pressure(name: str) -> float:
    n = name.lower()
    if any(w in n for w in HIGH):
        return 1.0
    if any(w in n for w in MED):
        return 0.6
    return 0.35


def coverage(lat: float, lng: float, cams, radius_m=COVERAGE_RADIUS_M) -> int:
    return sum(1 for clat, clng in cams if geo.haversine_m(lat, lng, clat, clng) <= radius_m)


def rank_blind_spots(top_k: int | None = None, path=geo.LANDMARKS_CSV,
                     cctv_path=CCTV_CSV) -> list[dict]:
    """Rank points by blind-spot score = pressure / (1 + camera coverage)."""
    cams = load_cameras(cctv_path)
    out = []
    for p in geo.load_points(path):
        cov = coverage(p.lat, p.lng, cams)
        pres = _pressure(p.name)
        score = pres / (1 + cov)
        out.append({"name": p.name, "type": p.type, "pressure": round(pres, 2),
                    "cameras": cov, "blind_score": round(score, 3),
                    "lat": p.lat, "lng": p.lng})
    out.sort(key=lambda d: d["blind_score"], reverse=True)
    return out[:top_k] if top_k else out


def build_map(top_k: int = 12, path=geo.LANDMARKS_CSV, cctv_path=CCTV_CSV):
    """Folium map: CCTV (blue dots) + booths/landmarks coloured by blind-spot risk;
    the top-k blind spots ringed red = put help here first."""
    import folium

    cams = load_cameras(cctv_path)
    ranked = rank_blind_spots(path=path, cctv_path=cctv_path)
    worst = {d["name"] for d in ranked[:top_k]}
    pts = geo.load_points(path)
    clat = sum(p.lat for p in pts) / len(pts)
    clng = sum(p.lng for p in pts) / len(pts)
    fmap = folium.Map(location=[clat, clng], zoom_start=14, tiles="OpenStreetMap")

    for clat, clng in cams:
        folium.CircleMarker([clat, clng], radius=3, color="#1c7ed6",
                            fill=True, fill_opacity=0.7, tooltip="CCTV").add_to(fmap)
    for d in ranked:
        is_blind = d["name"] in worst
        folium.CircleMarker(
            [d["lat"], d["lng"]], radius=9 if is_blind else 5,
            color="#c92a2a" if is_blind else "#2f9e44", fill=True,
            fill_opacity=0.85,
            tooltip=(("🚨 BLIND SPOT · " if is_blind else "") +
                     f"{d['name']} · pressure {d['pressure']} · {d['cameras']} cams"),
        ).add_to(fmap)
    return fmap


if __name__ == "__main__":
    spots = rank_blind_spots(top_k=10)
    cams = load_cameras()
    print(f"{len(cams)} cameras loaded. Top blind spots (place help here first):")
    for d in spots:
        print(f"  score {d['blind_score']:.2f}  {d['name']:<22} "
              f"pressure {d['pressure']}  cams {d['cameras']}")
