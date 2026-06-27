# PHASE LOG — Kumbh Setu (Drishti)

Append-only. Newest entries at the bottom.

---

## 2026-06-27 — Turn 1 — Scaffold + spine + team split

**Asked:** Read the master prompt. Divide the build into phases for the backend,
tell me how to set up so 3 people (A = me+Claude / B = backend+DB / C = designer)
can work simultaneously, create per-person markdown docs, and push to GitHub.

**Did:**
- Inspected repo: `/home/infinity/Projects/Drishti` is an empty git repo (no commits),
  SSH remote already set → `git@github.com:Preethesh16/Drishti.git`. **No `data/` dir
  and no datasets present** — flagged as a blocker for the real number.
- Corrected §3 assumption: there were **no** data files in the repo. Code is written to
  the documented 16-column schema and will run the instant the files are dropped in.
- Wrote `.claude/settings.local.json` to allowlist tools (no more permission prompts).
- Scaffolded: `data/ setu/ app/ scripts/ docs/ tests/`, `.gitignore`, `.env.example`,
  `requirements.txt`, `setu/__init__.py`.
- Built the **spine**: `config.py`, `privacy.py`, `ingest.py`, `matcher_tier1.py`,
  `validate.py` (Method A + Method B).
- Built working bases for teammates: `setu/registry.py` (Person B) and
  `app/dashboard.py` (Person C, 6 tabs wired to live data).
- Wrote docs: `README.md`, `data/README.md`, `docs/PERSON_A_CORE.md`,
  `docs/PERSON_B_BACKEND.md`, `docs/PERSON_C_DESIGN.md`, and the three tracking files.

**Ran:**
- `python3` env check: Python 3.14.5, pandas 3.0.2 present, rapidfuzz absent
  (matcher falls back to stdlib token-Jaccard — spine stays pandas+stdlib only).
- Generated a 324-row schema-correct fixture (24 planted duplicates) and ran the
  full spine on it.

**Result (fixture, NOT the real data):**
- ingest: 324 records de-identified, vault=324.
- Method A: recall **100%** (24/24), gap **15.6** (flagged 89.2 vs non 73.6).
- Method B: recall@1 **90%**, @3 **100%**, @5 **100%**.
- Proves the pipeline is correct. The meaningful number comes from the real 2,500 file.

**Pushed:** commit `d4e1ebc` → `origin/main`; created + pushed `core`, `backend`,
`design` branches. All four branches live on `github.com:Preethesh16/Drishti`.

**Next:**
1. (User) drop the 5 CSVs + 4 KMLs into `data/`.
2. (A) run `python -m setu.validate` on real data, tune `DUP_THRESHOLD`, tag `v0.1-number`.
3. (B) `git checkout backend`, harden registry (B1). (C) `git checkout design`, build intake (C1).

---

## 2026-06-27 — Turn 2 — Voice (Sarvam) confirmed + built

**Asked:** Confirmed Sarvam AI is best for voice. What should I do and what should
the other contributors do?

**Did:**
- Researched the current Sarvam API/SDK (web) to build against real signatures, not
  memory: `pip install sarvamai`; `SarvamAI(api_subscription_key=...)`;
  `speech_to_text.transcribe` (saarika), `speech_to_text.translate` (auto-detect →
  English), `text.translate` (mayura), `text_to_speech.convert` (bulbul).
- Built `setu/voice.py` (Person A / `core`): transcribe, transcribe_to_english
  (pivot-translate at ingest so the OFFLINE matcher is cross-lingual), translate,
  speak, `containment_message` (stay-put TTS in the person's language),
  `structure_report` (Claude → 16 fields). All degrade cleanly with no keys.
- Added `setu/llm.py` shared Claude helper. Wired `.env` loading + key getters +
  Sarvam language-code map into `config.py`. Added `sarvamai` to requirements.

**Ran:** `python -m setu.voice` (no keys) → no crash; Hindi containment text renders;
structuring/audio fall back to None as designed. All modules import OK.

**Git:** committed on `core` → pushed; merged `core` → `main` (--no-ff) → pushed.

**Next:** (A) wait for data → lock the number, then A3 Tier-2. (B) start B1 on
`backend`. (C) start C1 on `design`. (User) drop data + get SARVAM/ANTHROPIC keys.

---

## 2026-06-27 — Turn 3 — "run it" → full pipeline on stand-in data

**Asked:** Run it for me.

**Did:** Official data still absent, so wrote `scripts/make_demo_data.py` — a
realistic STAND-IN generator matching spec §3 distributions (2,500 rows, 202 hidden
duplicates, 8 langs, 10 centers, 20 locations, elderly-skewed ages, ~15% blank names,
~20% blank mobiles, paraphrased/synonym-swapped duplicate descriptions). Ran the full
spine on it.

**Ran & result (STAND-IN data, NOT official):**
- generate → 2,500 rows / 202 dupes.
- `setu.ingest` → seeded 2500, 202 ground-truth dupes, 548 blank names, 449 open.
- `setu.matcher_tier1` → top-3 with explainable per-signal reasons (sample top score 91.6).
- `setu.validate` → Method A recall **100%** / gap **12.3** (flagged 84.4 vs non 72.1);
  Method B recall@1 **96.5%** / @3 **100%** / @5 **100%**.
- 100% is expected on self-generated findable dupes — proves the PIPELINE, not difficulty.
  Real number awaits the official 202. Did NOT tag v0.1-number yet (hold for official data).

**Git:** committed generator + stand-in CSV + tracking on `main`; fast-forwarded
`core`/`backend`/`design` to main so all teammates have data + latest contracts.

**Next:** (User) drop official file → I re-run + tune threshold + tag v0.1-number.
(B) B1 registry hardening. (C) C1 intake + branding (dashboard runs against stand-in now).

---

## 2026-06-27 — Turn 4 — Person B: registry hardening (B1 + B2 + B4)

**Asked:** "I am Person B — go through the repo in depth and make the implementation."

**Did (on branch `backend`, forked from latest `main` so it has A's spine + voice):**
- **B1 — vault separation.** New `setu/vault.py`: an access-controlled raw-PII store
  in a SEPARATE SQLite file (`setu_vault.db`, gitignored, chmod 0600). `init_vault`,
  `put`, `seed_vault`, `get` (audited reveal, honours consent + purge), `purge`
  (destroys raw, keeps a tombstone), `count`. The `records` table now holds ONLY
  hashes + de-identified attributes — raw name/mobile never co-mingle with the
  matchable pool. `registry.seed_from_csv` now loads records → registry.db and raw
  → vault.db as two stores.
- **B1 — time window.** `get_records(window_hours=, reference_time=)` scopes the pool
  to reports within ±window of an anchor time (defaults to the newest `reported_at`),
  so we never scan the whole historical pool. Robust `_parse_dt` FAILS OPEN so a date
  format quirk never silently drops a real case.
- **B2 — retroactive re-match hook.** `add_record(..., rematch=True)` auto-runs
  `matcher_tier1.find_candidates` against the open, time-windowed pool and persists the
  top-k into a new `candidates` table. A FOUND report sits open as bait; when the family
  files anywhere, the match fires BACKWARD and links the two silos. `get_candidates()`
  reads them in either direction.
- **B4 — reveal-on-confirm + audit + purge.** `confirm_match` now: marks both Reunited →
  REVEALS raw contact from the vault (audited, for the operator to act on) → PURGEs raw
  PII (keeps the hash). **Contract change:** it now returns a dict
  `{summary, revealed, purged, actor}` instead of a bare string (A/C consume the dict).

**Ran:** `python -m setu.vault` (self-check ✔) and a new `scripts/demo_backend.py`
that builds Records in Python (NO real data, NO keys) and asserts the whole flow:
vault has no raw columns in registry; ±72h window excludes the 45-day-old reunited
case; M1 (family, Center-A) retroactively links to F1 (found, Center-B) at score 82.1
[STRONG] while the male decoy is gated out; confirm reveals "Sunita Patil / 9812345678"
then purges it (post-purge reveal denied) while the mobile HASH survives for dedup.
Audit log shows every REVEAL / PURGE / CONFIRM_MATCH / REVEAL_DENIED line.
`ALL CHECKS PASSED ✔`. All `setu.*` modules still import.

**Git:** committed on `backend` (not yet merged to main).

**Next (B):** B3 offline queue + sync/merge (UUID dedup, terminal-status-wins, LWW —
two offline DBs diverge then converge); B5 `mesh.py` simulated DTN demo (sim only,
first to cut). Then merge `backend` → `main`. The real `seed_from_csv`/vault counts
still wait on the data drop, but all B logic is data-independent and proven.

---

## 2026-06-27 — Turn 5 — Person B: connect the DB to the app (thin API)

**Asked:** "connect the db too please" — the dashboard was reading the CSV directly
and never touched the registry database B built.

**Did (branch `backend`):**
- **`setu/api.py`** — the thin facade (B's stretch goal): `stats`, `list_records`,
  `get_record`, `find_matches` (live Tier-1 vs the open, time-windowed pool),
  `candidates`, `file_report` (→ vault + registry + B2 hook), `confirm` (reveal-on-
  confirm), `ensure_seeded`, `reset`. Nothing outside `setu/` touches SQLite now.
- **`ensure_seeded()`** makes the connected DB usable with OR without the data drop:
  seeds from the real `Synthetic_Missing_Persons_2500.csv` if present, else a small
  built-in **demo set** (`seed_demo`: 9 records, cross-center match pairs, singletons,
  reunited cases, 5 languages) inserted chronologically with the B2 hook live.
- **Connected `app/dashboard.py`** to the live DB through `setu.api` (was reading the
  CSV via `ingest.load_records`). Registry tab = live de-identified pool from
  registry.db; Matches tab = pick an open case → `find_matches` → score + per-signal
  reasons → **✅ Confirm reunion** button → reveal-on-confirm shows the contact, then
  it's purged. Sidebar shows live DB stats + a "Reset demo data" button.

**Ran:** `python -m setu.api` → seeded 9 demo records into a persistent registry.db
(0644) + setu_vault.db (**0600**, locked); M1→F1 = 82.1 [STRONG], M8 = 59.0 weaker
(ranked). Headless flow of the exact dashboard calls: `confirm("M1","F1")` revealed
"Sunita Patil / 9812345678", purged both, both Reunited, post-purge vault read = {},
stats updated (open 7→5, reunited 2→4, vault live 9→7 / purged 0→2). `dashboard.py`
compiles; needs `pip install -r requirements.txt` (streamlit not in this env) to
launch the server.

**Git:** committed on `backend`.

**Next (B):** B3 sync/merge, B5 mesh, then merge `backend` → `main`.
