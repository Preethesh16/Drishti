# PROGRESS — Drishti

**Current phase:** Phase 3 — integrated build (A core + B backend + C maps merged on `main`).
**Next checkpoint:** drop real `data/Synthetic_Missing_Persons_2500.csv` → run
`python -m drishti.validate` → tune `DUP_THRESHOLD` → tag `v0.1-number`.

- [x] Phase 0 — renamed Kumbh Setu → **Drishti** (package `setu/`→`drishti/`); all branches synced

> ✅ **Pipeline runs on STAND-IN data** (`python scripts/make_demo_data.py`).
> ⚠️ Still need the **OFFICIAL** 5 CSVs + 4 KMLs for the real number + the maps.
> See `data/README.md`.

---

## Spine (steps 1–4) — NEVER cut
- [x] Scaffold: dirs, `.gitignore`, `.env.example`, `requirements.txt`, `drishti/__init__.py`
- [x] `drishti/config.py` — weights, thresholds, age order, model ids, columns
- [x] `drishti/privacy.py` — hash_pii / mask / reveal+audit
- [x] `drishti/ingest.py` — real CSV parse, de-identify, `Record` dataclass
- [x] `drishti/matcher_tier1.py` — gate + weighted weak-signal score + top-k funnel
- [x] `drishti/validate.py` — Method A (real flag) + Method B (synthetic pairs)
- [x] Spine smoke-tested on synthetic fixture (A recall 100%, B@1 90%)
- [x] Full pipeline run on 2,500-row STAND-IN data (`scripts/make_demo_data.py`):
      Method A recall 100% / gap 12.3 · Method B recall@1 96.5% / @3 100%
- [ ] **Re-run on OFFICIAL file** → real recall + gap → tag `v0.1-number`
- [ ] Tune `DUP_THRESHOLD` vs the official 202

## Person A — Core / AI (`core`)
- [x] A1 spine (above)
- [x] `drishti/llm.py` — shared Claude helper (have_claude/complete/complete_json)
- [x] A4 `voice.py` — Sarvam ASR/TTS/translate + Claude structuring + containment
      TTS; runs in fallback with no keys (merged to main). _Needs a SARVAM key +
      real audio to fully exercise._
- [x] A3 `matcher_tier2.py` — Claude cross-lingual desc match + decision bands
      (auto≥70 / review≥40 / none) + human reason; `match()` Step-5 pipeline.
      Verified offline; lights up with `ANTHROPIC_API_KEY`.
- [ ] A2 lock the number (tune threshold on real data) ← **gated on data drop**

## Person B — Backend / DB / Sync (`backend`)
- [x] `registry.py` working minimal base (SQLite, CRUD, confirm_match, seed_from_csv)
- [x] B1 vault separation (`drishti/vault.py`, gitignored 0600 store) + time-window query
- [x] B2 retroactive re-match hook (`candidates` table, `get_candidates`) — fires backward
- [x] B4 reveal-on-confirm + audit + purge (confirm_match → dict {revealed, purged})
- [x] verified end-to-end via `scripts/demo_backend.py` (no data/keys needed) — ALL PASS
- [x] thin API `drishti/api.py` — the one door the dashboard calls (stats/list/find_matches/
      confirm/ensure_seeded); decouples C from the registry/vault internals
- [x] **connected the DB to the app** — `app/dashboard.py` now reads/writes the live
      registry.db + vault via `drishti.api` (no CSV, no direct SQLite). Auto-seeds (real CSV
      if present, else a built-in demo set) so the DB works with no data drop.
- [x] **merged `backend` → `main`** (`d12f8f6`) — integrated unified dashboard
- [ ] B3 offline queue + sync/merge (UUID dedup, terminal-wins, LWW) — supports LAN→P2P fallback
- [ ] B5 `mesh.py` booth↔booth P2P-fallback sim (activates on LAN loss)
- [ ] SMS-parse intake + SMS-out (simulated); zone/proximity-targeted broadcast wired to registry
- [ ] (stretch) MCP server exposing the registry as a Claude tool

## Person C — Design / Frontend / Maps (`design`)
- [x] `app/dashboard.py` skeleton — 6 tabs wired to live data
- [x] `drishti/geo.py` — Nashik named landmarks + ~500m booth grid + haversine
      proximity + **emergency broadcast** (nearby booths in radius) + folium map
- [x] `scripts/make_nashik_geo.py` → `data/nashik_landmarks.csv` (14 landmarks + 36 booths)
- [x] Maps tab — live Nashik map: pick where a report lands → alert radius + booths lit red
- [x] File tab — staffed-booth intake: language picker, landmark dropdown, file →
      shows booths alerted; Found-flow plays containment TTS (edge-tts)
- [~] C2 Matches tab — LIVE (B wired it: top-3 via `api.find_matches` + per-signal
      reasons + ✅ reveal-on-confirm). Remaining: swap to `matcher_tier2.match()` for the
      auto/review/none **bands** + Claude cross-lingual reason.
- [ ] C3 `blindspot.py` / `drift.py` overlays (need official geo data for full version)
- [ ] C4 branding polish + demo script
- [ ] File-tab live retroactive match: align demo dates (stand-in is 2027 vs filed "now")

## Git / GitHub
- [x] committed scaffold → `origin/main` (`d4e1ebc`)
- [x] created + pushed branches `core`, `backend`, `design`

## Tracking (every turn)
- [x] PROGRESS.md · PHASE_LOG.md · CONTEXT.md · README.md · per-person docs

## Cut-line order if time runs short
mesh → drift → Tier-2 → maps. **Never** cut the spine or the number.
