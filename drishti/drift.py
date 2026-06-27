"""Drift predictor — WHERE to search (additive intelligence, Step 4).

Given where someone was last seen, how long ago, and their profile, rank the
zones/booths they most likely drifted to — bounded by walking speed (~1–2 km/h
in a dense crowd) and behavioural priors:
  • confused elderly  → low mobility, ANCHOR-seeking (drift toward big landmarks)
  • child             → erratic, SHORT range (stays close)
  • adult             → heads for EXITS / transit / parking

Output: ranked booths with a probability → alert ONLY those booths' volunteers,
not all 50. Pure math on the Nashik geo points (no surveillance).

Run:  python -m drishti.drift
"""
from __future__ import annotations

import math

from drishti import geo

# walking speed (km/h) by profile in a dense crowd
SPEED = {"elderly": 1.0, "child": 1.4, "adult": 1.8}
# how spread-out the search cone is (× reach). elderly/child tight, adults wide.
SPREAD = {"elderly": 0.7, "child": 0.5, "adult": 1.1}
# words that hint a point is an EXIT/transit (adults head here)
EXIT_WORDS = ("gate", "transit", "parking", "cross", "belt", "outer", "station", "naka", "stand")
# words that hint a calm gathering anchor (confused elderly drift toward these)
ANCHOR_WORDS = ("ghat", "sangam", "plaza", "hall", "bhajan", "annakshetra", "ghat walk", "watch")


def _is_exit(name: str) -> bool:
    n = name.lower()
    return any(w in n for w in EXIT_WORDS)


def _is_anchor(name: str) -> bool:
    n = name.lower()
    return any(w in n for w in ANCHOR_WORDS)


def predict(last_seen: str, elapsed_hours: float, profile: str = "elderly",
            top_k: int = 6, path=geo.LANDMARKS_CSV) -> list[dict]:
    """Rank likely locations. `last_seen` is a landmark/booth name. Returns
    [{name, type, probability, distance_m}] sorted by probability."""
    origin = geo.point_by_name(last_seen, path)
    if origin is None:
        return []
    profile = profile if profile in SPEED else "elderly"
    reach_m = max(150.0, SPEED[profile] * max(elapsed_hours, 0.1) * 1000.0)
    sigma = reach_m * SPREAD[profile]

    scored = []
    for p in geo.load_points(path):
        if p.name == origin.name:
            d = 0.0
        else:
            d = geo.haversine_m(origin.lat, origin.lng, p.lat, p.lng)
        if d > reach_m * 2.2:                      # unreachable in the elapsed time
            continue
        base = math.exp(-((d / sigma) ** 2))       # gaussian falloff with distance
        boost = 1.0
        if profile == "elderly" and _is_anchor(p.name):
            boost = 1.8                            # anchor-seeking toward calm gathering points
        elif profile == "adult" and _is_exit(p.name):
            boost = 1.7                            # heading for an exit
        elif profile == "child":
            boost = 1.3 if d < reach_m * 0.5 else 0.6  # stays close, erratic short range
        scored.append((p, base * boost, d))

    total = sum(s for _, s, _ in scored) or 1.0
    ranked = sorted(scored, key=lambda x: x[1], reverse=True)[:top_k]
    return [{"name": p.name, "type": p.type,
             "probability": round(s / total, 3), "distance_m": round(d)}
            for p, s, d in ranked]


if __name__ == "__main__":
    for prof in ("elderly", "child", "adult"):
        print(f"\n{prof.upper()} last seen 'Central Plaza', missing 2h → search:")
        for z in predict("Central Plaza", 2.0, prof, top_k=5):
            print(f"  {z['probability']*100:4.0f}%  {z['name']:<22} ({z['distance_m']}m, {z['type']})")
