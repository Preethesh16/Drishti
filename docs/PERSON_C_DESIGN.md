# Person C — Design / Frontend / Maps 🎨

**You are:** everything the judges SEE. The operator dashboard, the intake flow,
the maps, the branding, and the demo polish. You turn the engine into a story.

**Branch:** `design`  →  merge to `main` at every green checkpoint.
**You own:** `app/dashboard.py`, `drishti/geo.py`, `drishti/drift.py`, `drishti/blindspot.py`,
`scripts/build_geo.py`, branding/assets, and the demo script.

> Design north star: a panicking, **non-literate** reporter is served by a
> **volunteer**. Calm, big type, voice-first, two big forks: **"Lost someone?"** /
> **"Found someone?"**. Judges must SEE three moments: (1) the silos merging into one
> registry, (2) a **cross-lingual match with a human-readable reason**, (3) the
> **reveal-on-confirm** privacy moment.

A working dashboard skeleton (`app/dashboard.py`) with all six tabs is already
scaffolded and wired to live data. Make it real and beautiful, in phases.

---

## Setup
```bash
git checkout -b design
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # set SETU_SALT
# drop the CSVs + KMLs into data/ (see data/README.md)
streamlit run app/dashboard.py
```

## Phases

### C1 — Intake + branding 🎯 (NEXT)
- The **File** tab: the two big forks. Lost-flow stays brain-dead simple; Found-flow
  lets the operator log details. Big buttons, minimal text, language picker.
- Brand it "Drishti" (Setu = bridge). Warm, calm, trustworthy. The one-liner from
  the README goes on the header. Add the "what we do NOT do" honesty line somewhere
  visible — it reads as senior.

### C2 — Registry + Matches tabs (the core demo)
- **Registry** tab: show the merged pool with center + status; visibly demonstrate
  that a record from Center B is now visible to Center A (the silo break).
- **Matches** tab: pick a record → call
  `drishti.matcher_tier1.find_candidates(target, pool, top_k=3)` → render each candidate
  with its **score (0–100)** and **per-signal reasons** (`r.reasons` dict). Mask PII
  with `drishti.privacy.mask_name / mask_mobile`. Add a **"Confirm reunion"** button that
  calls `registry.confirm_match` and triggers `privacy.reveal` — the privacy money shot.

### C3 — Maps (`geo.py` / `blindspot.py` / `drift.py`) + Maps tab
- `scripts/build_geo.py`: parse the KMLs with `lxml` → polygons/lines → GeoJSON.
  `drishti/geo.py`: `which_zone(lat,lng)` via `shapely` point-in-polygon; build the
  zone graph (nodes = zone polygons, edges = corridors/chokepoints).
- `drishti/blindspot.py`: overlay CCTV coverage vs separation hotspots (chokepoints +
  `last_seen_location` clusters). **High-separation × low-camera = where people vanish.**
- `drishti/drift.py`: `P(zone | last_seen, elapsed, profile)` bounded by walking speed
  (~1–2 km/h); behavioural priors (confused elderly = low-mobility/anchor-seeking;
  children = erratic short-range; adults = head for exits).
- **Maps** tab: `folium` + `streamlit-folium` heatmaps. Bounds:
  lat 19.93–20.08, lng 73.71–73.89.

### C4 — Validation tab + demo polish
- **Validation** tab already calls `drishti.validate.run()` — make the number BIG and
  proud (recall + gap, recall@1/@3/@5). This is the differentiator; give it the stage.
- Write/own the 3-minute demo script: silos → file a report by voice → instant
  cross-lingual match with reason → confirm → reveal → "and here's the number".

## The contract you consume (don't reach past these)
```python
from drishti.ingest import load_records, Record
from drishti.matcher_tier2 import match     # PREFERRED for the Matches tab:
#   match(target, pool, top_k=3) -> [EnrichedResult(.case_id, .score, .band, .reason, .tier2_used)]
#   .band is 'auto' (≥70, green) | 'review' (≥40, amber) | 'none' — colour the cards by band.
from drishti.matcher_tier1 import find_candidates          # raw Tier-1 if you need it
from drishti.registry import get_records, confirm_match
from drishti.privacy import mask_name, mask_mobile, reveal
from drishti.validate import run
```

## Cut-lines
maps (C3) is cut before the spine. **Never cut** the Matches tab (C2) or the
Validation tab (C4) — those carry the demo. Voice button + reveal-on-confirm are gold.

## Definition of done per turn
Run `streamlit run app/dashboard.py`, click through, fix, commit. Update
`PROGRESS.md`, `PHASE_LOG.md`, `CONTEXT.md` every turn.
