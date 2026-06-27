# CONTEXT — Kumbh Setu (Drishti) — read this file alone to continue with zero prior chat

## What we're building (one paragraph)
**Kumbh Setu** ("Setu" = bridge) for the **Claude Impact Lab, Mumbai 2026** hackathon.
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

## Scoring config (`setu/config.py`, all tunable)
`lang=30, age=15 (adjacent=7), gender=10 (Unknown=5), geo_same=25 / geo_diff=4,
desc=35×similarity, state=10, district=5`. `MAX_RAW=130` (raw→0..100). Gate: not-same-record,
age within ±1 band, gender equal-or-Unknown. `DUP_THRESHOLD=55` (tune vs the 202).
Age order: `['0-12','13-17','18-40','41-60','61-70','71-80','80+']`.

## Repo layout (current)
```
Drishti/
├── data/ (README; DROP the 5 CSVs + 4 KMLs here — currently EMPTY)
├── setu/ __init__ · config · privacy · ingest · matcher_tier1 · validate · registry ·
│        vault (B1) · api (B facade) · llm · voice
├── app/dashboard.py (Streamlit, 6 tabs — now wired to the live DB via setu.api)
├── scripts/demo_backend.py (B1/B2/B4 verification — runs with no data, no keys)
├── docs/ PERSON_A_CORE.md · PERSON_B_BACKEND.md · PERSON_C_DESIGN.md
├── PROGRESS.md · PHASE_LOG.md · CONTEXT.md · README.md · requirements.txt
└── (todo) setu/matcher_tier2 · mesh (B5) · geo · drift · blindspot · scripts/build_geo
```

## Team split (parallel branches → merge to main at green checkpoints)
- **A = Core/AI** (`core`): config, privacy, ingest, matcher_tier1, validate, matcher_tier2, voice.
- **B = Backend/DB/Sync** (`backend`): registry, vault, sync/merge, reveal+audit, mesh sim, API.
- **C = Design/Frontend/Maps** (`design`): dashboard, geo, drift, blindspot, branding, demo.
See `docs/PERSON_*.md`. Stable contracts:
```python
setu.ingest:        Record, load_records()  -> (records, vault)
setu.matcher_tier1: find_candidates(target, pool, top_k=3, require_open=False) -> [ScoreResult]
                    ScoreResult(.case_id, .score 0..100, .raw, .reasons dict)
setu.registry:      init_db, add_record(rec, rematch=True), set_status, seed_from_csv,
                    get_records(open_only=False, window_hours=None, reference_time=None),
                    get_candidates(case_id) -> [dict],     # B2 retroactive matches
                    confirm_match(a, b, actor, reason) -> {summary, revealed, purged, actor}
                    # ^ B4: now returns a dict (was a string); raw contact + purge happen here
setu.vault:         init_vault, put, seed_vault(vault), get(vid, actor=, reason=) -> {} | raw,
                    purge(vid, actor=), count() -> (live, purged)   # access-controlled raw PII
setu.api:           ensure_seeded(), stats(), list_records(open_only, limit), get_record(id),
                    find_matches(id, top_k) -> [dict], candidates(id), file_report(rec),
                    confirm(a, b, actor, reason)   # THE door the dashboard calls (B's facade)
setu.privacy:       hash_pii, mask_name, mask_mobile, reveal(case_id, fields, actor, reason), audit
setu.validate:      run() -> {method_a, method_b}
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
- **Date:** 2026-06-27. Branches on `Preethesh16/Drishti`: `main` (integration),
  `core` (A), `backend` (B), `design` (C). Voice work merged core → main.
- Spine built and proven on a synthetic fixture: Method A recall 100% / gap 15.6;
  Method B recall@1 90% / @3 100%. **Real number pending real data drop.**
- Voice done (A4): `setu/voice.py` (Sarvam ASR/TTS/translate) + `setu/llm.py`
  (shared Claude helper). Both degrade cleanly with no keys (verified, no crash).
- **Backend B1+B2+B4 done on `backend`** (not yet merged): `setu/vault.py` separates raw
  PII into an access-controlled `setu_vault.db`; `get_records` has a time-window filter;
  `add_record` fires a retroactive re-match (new `candidates` table + `get_candidates`);
  `confirm_match` does reveal-on-confirm → audit → purge and returns a dict. Proven by
  `scripts/demo_backend.py` (no data, no keys → ALL CHECKS PASSED).
- **DB connected to the app** via `setu/api.py` (B's thin facade): the dashboard now
  reads/writes registry.db + setu_vault.db through the API (no CSV, no direct SQLite).
  `api.ensure_seeded()` seeds from the real CSV if present, else a 9-record demo set, so
  the connection works with no data drop. registry.db is 0644; setu_vault.db is 0600.
- Python 3.10.12 / pandas 2.3.3 in this env (rapidfuzz optional, stdlib Jaccard fallback).
- **BLOCKER:** `data/` is empty — user must drop the 5 CSVs + 4 KMLs. Optional keys:
  `SARVAM_API_KEY` (voice), `ANTHROPIC_API_KEY` (Tier-2 + structuring) in `.env`.
  (Backend logic is data-independent; only the real seed counts + the number wait on data.)
- **Next:** real `validate` run + threshold tune → tag v0.1-number, then A3 Tier-2
  (A); B3 sync/merge + B5 mesh, then merge `backend`→`main` (B); intake UI + branding C1 (C).
