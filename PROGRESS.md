# PROGRESS — Drishti

**Current phase:** Phase 2 — workflow build (renamed to Drishti; Tier-2 + bands done).
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
- [ ] B1 vault separation + time-window query
- [ ] B2 retroactive re-match hook
- [ ] B3 offline queue + sync/merge (UUID dedup, terminal-wins, LWW)
- [ ] B4 reveal-on-confirm + audit + purge
- [ ] B5 `mesh.py` simulated DTN demo (sim only)
- [ ] (stretch) thin API / MCP server

## Person C — Design / Frontend / Maps (`design`)
- [x] `app/dashboard.py` skeleton — 6 tabs wired to live data
- [ ] C1 intake forks + branding
- [ ] C2 Registry + Matches tabs (top-3 + reasons + reveal-on-confirm)
- [ ] C3 `geo.py` / `blindspot.py` / `drift.py` + Maps tab (folium)
- [ ] C4 Validation tab polish + demo script

## Git / GitHub
- [x] committed scaffold → `origin/main` (`d4e1ebc`)
- [x] created + pushed branches `core`, `backend`, `design`

## Tracking (every turn)
- [x] PROGRESS.md · PHASE_LOG.md · CONTEXT.md · README.md · per-person docs

## Cut-line order if time runs short
mesh → drift → Tier-2 → maps. **Never** cut the spine or the number.
