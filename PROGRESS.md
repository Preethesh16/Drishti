# PROGRESS — Kumbh Setu (Drishti)

**Current phase:** Phase 1 — Spine scaffolded & proven on fixture.
**Next checkpoint:** drop real `data/Synthetic_Missing_Persons_2500.csv` → run
`python -m setu.validate` → tune `DUP_THRESHOLD` → tag `v0.1-number`.

> ⚠️ **BLOCKER:** `data/` is empty. The real number needs the 5 CSVs + 4 KMLs.
> See `data/README.md`.

---

## Spine (steps 1–4) — NEVER cut
- [x] Scaffold: dirs, `.gitignore`, `.env.example`, `requirements.txt`, `setu/__init__.py`
- [x] `setu/config.py` — weights, thresholds, age order, model ids, columns
- [x] `setu/privacy.py` — hash_pii / mask / reveal+audit
- [x] `setu/ingest.py` — real CSV parse, de-identify, `Record` dataclass
- [x] `setu/matcher_tier1.py` — gate + weighted weak-signal score + top-k funnel
- [x] `setu/validate.py` — Method A (real flag) + Method B (synthetic pairs)
- [x] Spine smoke-tested on synthetic fixture (A recall 100%, B@1 90%)
- [ ] **Run on real 2,500-row file** → real recall + gap
- [ ] Tune `DUP_THRESHOLD` vs the 202 → tag `v0.1-number`

## Person A — Core / AI (`core`)
- [x] A1 spine (above)
- [ ] A2 lock the number (tune threshold on real data)
- [ ] A3 `matcher_tier2.py` — Claude cross-lingual + reasons (degrade w/o key)
- [ ] A4 `voice.py` — Sarvam/Vosk → Claude structure → fields + containment TTS

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
