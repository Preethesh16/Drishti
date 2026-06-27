# CONTEXT — Drishti — read this file alone to continue with zero prior chat

## What we're building (one paragraph)
**Drishti** ("Setu" = bridge) for the **Claude Impact Lab, Mumbai 2026** hackathon.
Theme: reunite missing persons at the **Nashik Kumbh Mela 2027** while protecting PII.
Real-world failure: ~10 lost-and-found centers are disconnected silos with no cross-search —
a person *found* at Center B is invisible to a family *searching* at Center A. We build **one
shared, live, de-identified registry** that **matches two reports about the same person** (a
family's "missing" + a volunteer's "found") on **weak signals** (age, gender, language,
location, physical description), because strong identifiers (name, phone) are usually missing
and the lost person often cannot identify themselves. **Claude is the reasoning brain**;
everything else is plumbing. **No facial recognition, no GPS tracking.** Privacy is structural:
match on hashed/de-identified data, reveal real identity only at a human-confirmed reunion,
with an audit log.

**Positioning line:** *"We don't track people or scan faces. We connect the two halves of every
search — the family looking and the person found — across centers that today can't see each
other, in any language, on weak data, without ever surveilling anyone."*

## Non-negotiable principles (do not drift)
1. Claude is the brain; voice = I/O; geometry = math; everything else is plumbing.
2. Match on weak signals, not identifiers (name/mobile stay hashed).
3. No tracking, no facial recognition. Predict where to look; match reports; human confirms.
4. Privacy is structural — blind matching, hash-at-ingest, reveal-on-confirm + audit.
5. Offline-first — capture never blocks; tiered matching; mesh is a sim + a slide.
6. Human-in-the-loop — surface top-3; never auto-reunite.
7. Prove it with a real number from the 202 duplicates.
8. Scope discipline — protect the spine + the number; everything else is additive.

## The data (design to these numbers; files go in `data/`)
`Synthetic_Missing_Persons_2500.csv` — 2,500 rows, 16 cols:
`case_id, reported_at, missing_person_name, gender, age_band, state, district, language,
last_seen_location, reporting_center, reporter_mobile, physical_description, status,
resolution_hours, is_duplicate_report, remarks`.
- status: Reunited 2150 / Pending 210 / Transferred to hospital 73 / Unresolved 67.
- name blank ~15%, mobile blank ~20%. **`is_duplicate_report==True` ≈ 202 → ground truth.**
- age skews elderly (61-70 largest). language across 8+ Indian langs (strong discriminator).
- last_seen_location: 20 distinct. reporting_center: 10 silos. mobiles ALL unique; names collide.
- Other CSVs: `CCTV_Locations.csv` (1,280), `Zone_Boundaries.csv` (32), `Police_Stations.csv`
  (14), `Chokepoints_Parking.csv` (85). 4 KMLs hold the real polygons/corridors.
- **All synthetic/fake PII.** Parse with a real CSV reader (quoted commas in descriptions).

## Architecture
INTAKE (voice-first, operator-mediated, landmark-based) → THE REGISTRY (shared, live,
retroactive, time-windowed, de-identified) → INTELLIGENCE [(A) Tier-1 offline rules + Tier-2
Claude cross-lingual match; (B) drift predictor from KML zone graph; (C) blind-spot map] →
ACTION (targeted alert → nearest help → human confirms → reunite). PRIVACY CORE cross-cuts.

## Scoring config (`drishti/config.py`, all tunable)
`lang=30, age=15 (adjacent=7), gender=10 (Unknown=5), geo_same=25 / geo_diff=4,
desc=35×similarity, state=10, district=5`. `MAX_RAW=130` (raw→0..100). Gate: not-same-record,
age within ±1 band, gender equal-or-Unknown. `DUP_THRESHOLD=55` (tune vs the 202).
Age order: `['0-12','13-17','18-40','41-60','61-70','71-80','80+']`.

## Repo layout (current)
```
Drishti/
├── data/ (README; stand-in CSV present; DROP official 5 CSVs + 4 KMLs here)
├── drishti/ __init__ · config · privacy · ingest · matcher_tier1 · matcher_tier2 · validate
│            · registry · llm · voice
├── app/dashboard.py (Streamlit, 6 tabs) · scripts/make_demo_data.py
├── docs/ PERSON_A_CORE.md · PERSON_B_BACKEND.md · PERSON_C_DESIGN.md
├── PROGRESS.md · PHASE_LOG.md · CONTEXT.md · README.md · requirements.txt
└── (todo) drishti/geo · drift · blindspot · mesh · scripts/build_geo
```

## Team split (parallel branches → merge to main at green checkpoints)
- **A = Core/AI** (`core`): config, privacy, ingest, matcher_tier1, validate, matcher_tier2, voice.
- **B = Backend/DB/Sync** (`backend`): registry, vault, sync/merge, reveal+audit, mesh sim, API.
- **C = Design/Frontend/Maps** (`design`): dashboard, geo, drift, blindspot, branding, demo.
See `docs/PERSON_*.md`. Stable contracts:
```python
drishti.ingest:        Record, load_records()  -> (records, vault)
drishti.matcher_tier1: find_candidates(target, pool, top_k=3, require_open=False) -> [ScoreResult]
                    ScoreResult(.case_id, .score 0..100, .raw, .reasons dict)
drishti.matcher_tier2: match(target, pool, top_k=3, tier2_k=5, require_open=False) -> [EnrichedResult]
                    EnrichedResult(.case_id, .score, .band 'auto'|'review'|'none', .reason, .tier2_used)
                    band thresholds: MATCH_AUTO=70 (alert human, not auto-reunite), MATCH_REVIEW=40
drishti.registry:      init_db, add_record, get_records(open_only, window_hours), set_status,
                    confirm_match(a, b, actor), seed_from_csv
drishti.privacy:       hash_pii, mask_name, mask_mobile, reveal(case_id, fields, actor, reason), audit
drishti.validate:      run() -> {method_a, method_b}
```

## Tech (all free, offline-capable core)
Claude (`claude-sonnet-4-6` default, `claude-opus-4-8` hard cases) · Sarvam/Vosk voice ·
shapely+lxml geometry · SQLite · rapidfuzz/Jaccard text sim · Streamlit + folium UI.
Spine (steps 1–4) needs pandas + stdlib ONLY. NO facial recognition, NO GPS, NO GPU.

## Build order (each ends with a runnable checkpoint + commit)
1✅ scaffold+config+privacy → 2✅ ingest → 3✅ matcher_tier1 → 4✅ validate (spine done,
fixture-proven) → **(real data → tag v0.1-number)** → 5 dashboard → 6 tier2 → 7 geo/maps →
8 voice → 9 mesh. Cut-lines if short: mesh → drift → tier2 → maps. Never cut spine/number.

## CURRENT STATE (update every turn)
- **Date:** 2026-06-27. Name = **Drishti** (was codename "Kumbh Setu"). Branches on
  `Preethesh16/Drishti`: `main` (integration), `core` (A), `backend` (B), `design` (C).
- **Done so far:** spine (config/privacy/ingest/matcher_tier1/validate); `llm.py`;
  `voice.py` (Sarvam ASR/translate/TTS + **free edge-tts + Claude fallbacks**;
  any-language → English structured details); `matcher_tier2.py` (Claude cross-lingual
  + bands); `geo.py` (**Nashik named landmarks + ~500m booth grid + emergency
  broadcast + folium map**); registry base; dashboard (Maps + File tabs LIVE);
  data + nashik-geo generators. All fallback-safe.
- **Env:** dev uses `.venv --system-site-packages` (folium/streamlit-folium/edge-tts
  added; system has pandas/streamlit). Run app: `.venv/bin/python -m streamlit run app/dashboard.py`.
- **Connectivity model (decided):** LAN→central (normal) → booth↔booth P2P (only on
  LAN loss) → local queue → SMS. Booth is STAFFED (operator-mediated). [B to build]
- **Match bands:** auto≥70 (alert a human, never auto-reunite), review≥40, else none.
- **Pipeline green on STAND-IN data** (`python scripts/make_demo_data.py`): Method A
  recall 100% / gap 12.3; Method B recall@1 ~97%. (100% expected on self-made dupes —
  proves the pipeline; real number awaits official 202; not yet tagged v0.1-number.)
- Python 3.14.5, pandas 3.0.2 (rapidfuzz optional; stdlib fallback).
- **Still need:** OFFICIAL 5 CSVs + 4 KMLs (real number + maps). Optional keys:
  `SARVAM_API_KEY` (voice), `ANTHROPIC_API_KEY` (Tier-2 + structuring) in `.env`.
- **Next:** A — lock the number when data lands. B — B1 registry + connectivity
  ladder/SMS-sim. C — C1 intake + Matches tab via `matcher_tier2.match()` + maps (geo-data-gated).
  (A); registry hardening B1 (B); intake UI + branding C1 (C).
