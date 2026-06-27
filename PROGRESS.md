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
- [x] `setu/llm.py` — shared Claude helper (have_claude/complete/complete_json)
- [x] A4 `voice.py` — Sarvam ASR/TTS/translate + Claude structuring + containment
      TTS; runs in fallback with no keys (merged to main). _Needs a SARVAM key +
      real audio to fully exercise._
- [ ] A2 lock the number (tune threshold on real data) ← **gated on data drop**
- [ ] A3 `matcher_tier2.py` — Claude cross-lingual + reasons (degrade w/o key)

## Person B — Backend / DB / Sync (`backend`)
- [x] `registry.py` working minimal base (SQLite, CRUD, confirm_match, seed_from_csv)
- [x] B1 vault separation (`setu/vault.py`, gitignored 0600 store) + time-window query
- [x] B2 retroactive re-match hook (`candidates` table, `get_candidates`) — fires backward
- [x] B4 reveal-on-confirm + audit + purge (confirm_match → dict {revealed, purged})
- [x] verified end-to-end via `scripts/demo_backend.py` (no data/keys needed) — ALL PASS
- [x] thin API `setu/api.py` — the one door the dashboard calls (stats/list/find_matches/
      confirm/ensure_seeded); decouples C from the registry/vault internals
- [x] **connected the DB to the app** — `app/dashboard.py` now reads/writes the live
      registry.db + vault via `setu.api` (no CSV, no direct SQLite). Auto-seeds (real CSV
      if present, else a built-in demo set) so the DB works with no data drop.
- [ ] B3 offline queue + sync/merge (UUID dedup, terminal-wins, LWW)
- [ ] B5 `mesh.py` simulated DTN demo (sim only)
- [ ] (stretch) MCP server exposing the registry as a Claude tool
- [ ] merge `backend` → `main` at the next green checkpoint

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
