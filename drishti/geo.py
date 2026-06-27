"""Nashik geography — named landmarks, the ~500m booth grid, proximity broadcast,
and the folium map for the website.  [Person C's domain; built to unblock the demo]

Core idea (Step 3 of the workflow): a new report at booth/landmark X must alert
ALL booths within a radius, because the lost person may have drifted to a
neighbouring booth. `nearby_booths()` computes that set; `build_map()` renders it.

Pure-stdlib for the logic (haversine); folium is lazy-imported only for the map,
so this module imports fine even where folium isn't installed.
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass

from drishti import config as C

LANDMARKS_CSV = C.DATA_DIR / "nashik_landmarks.csv"

# Default emergency-broadcast radius: a person can walk ~1km in ~30-60 min in a
# dense crowd, so alert booths within ~1km of where they were last seen.
DEFAULT_RADIUS_M = 1000


@dataclass
class Point:
    name: str
    lat: float
    lng: float
    type: str  # 'landmark' | 'booth'


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in metres."""
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def load_points(path=LANDMARKS_CSV) -> list[Point]:
    pts: list[Point] = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            pts.append(Point(row["name"], float(row["lat"]), float(row["lng"]),
                             row.get("type", "booth")))
    return pts


def landmarks(path=LANDMARKS_CSV) -> list[Point]:
    return [p for p in load_points(path) if p.type == "landmark"]


def booths(path=LANDMARKS_CSV) -> list[Point]:
    return [p for p in load_points(path) if p.type == "booth"]


def point_by_name(name: str, path=LANDMARKS_CSV) -> Point | None:
    name = (name or "").strip().lower()
    for p in load_points(path):
        if p.name.strip().lower() == name:
            return p
    return None


def nearest(lat: float, lng: float, kind: str | None = None,
            path=LANDMARKS_CSV) -> tuple[Point, float] | None:
    pts = [p for p in load_points(path) if kind is None or p.type == kind]
    if not pts:
        return None
    best = min(pts, key=lambda p: haversine_m(lat, lng, p.lat, p.lng))
    return best, haversine_m(lat, lng, best.lat, best.lng)


def nearby_booths(origin: str | tuple[float, float], radius_m: float = DEFAULT_RADIUS_M,
                  path=LANDMARKS_CSV) -> list[tuple[Point, float]]:
    """Booths within radius_m of `origin` (a landmark/booth name OR (lat,lng)).
    This is the EMERGENCY-BROADCAST set: every booth here gets the alert."""
    if isinstance(origin, str):
        p = point_by_name(origin, path)
        if p is None:
            return []
        lat, lng = p.lat, p.lng
    else:
        lat, lng = origin
    out = []
    for b in booths(path):
        d = haversine_m(lat, lng, b.lat, b.lng)
        if d <= radius_m:
            out.append((b, round(d)))
    out.sort(key=lambda x: x[1])
    return out


def broadcast_alert(origin: str, radius_m: float = DEFAULT_RADIUS_M,
                    path=LANDMARKS_CSV) -> dict:
    """Return the emergency-signal payload: which booths to alert and how far."""
    targets = nearby_booths(origin, radius_m, path)
    return {
        "origin": origin,
        "radius_m": radius_m,
        "alerted_booths": [{"name": b.name, "distance_m": d} for b, d in targets],
        "count": len(targets),
    }


# ---------------------------------------------------------------------------
# Folium map for the website (lazy import — needs folium in the venv)
# ---------------------------------------------------------------------------
def build_map(highlight: str | None = None, radius_m: float = DEFAULT_RADIUS_M,
              path=LANDMARKS_CSV):
    """Folium map of Nashik with named landmarks + booths. If `highlight` is a
    landmark/booth name, draw the alert radius and colour alerted booths red."""
    import folium

    pts = load_points(path)
    clat = sum(p.lat for p in pts) / len(pts)
    clng = sum(p.lng for p in pts) / len(pts)
    fmap = folium.Map(location=[clat, clng], zoom_start=14, tiles="OpenStreetMap")

    alerted = set()
    if highlight:
        origin = point_by_name(highlight, path)
        if origin:
            folium.Circle([origin.lat, origin.lng], radius=radius_m,
                          color="#e8590c", fill=True, fill_opacity=0.08,
                          popup=f"Alert radius {radius_m:.0f}m around {highlight}").add_to(fmap)
            alerted = {b.name for b, _ in nearby_booths(highlight, radius_m, path)}

    for p in pts:
        if p.type == "landmark":
            folium.Marker([p.lat, p.lng], tooltip=f"📍 {p.name}",
                          icon=folium.Icon(color="blue", icon="star")).add_to(fmap)
        else:
            is_alert = p.name in alerted
            folium.CircleMarker(
                [p.lat, p.lng], radius=6,
                color="#c92a2a" if is_alert else "#e8590c",
                fill=True, fill_opacity=0.9,
                tooltip=("🚨 ALERTED · " if is_alert else "🏠 Booth · ") + p.name,
            ).add_to(fmap)
    return fmap


if __name__ == "__main__":
    pts = load_points()
    print(f"loaded {len(pts)} points ({len(landmarks())} landmarks, {len(booths())} booths)")
    demo = "Central Plaza"
    payload = broadcast_alert(demo, radius_m=1000)
    print(f"\nEMERGENCY BROADCAST — report near '{demo}', radius 1000m:")
    print(f"  alerts {payload['count']} nearby booths:")
    for b in payload["alerted_booths"][:8]:
        print(f"    {b['distance_m']:>4}m  {b['name']}")
