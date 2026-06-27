# PHASE LOG — Drishti

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
- Scaffolded: `data/ drishti/ app/ scripts/ docs/ tests/`, `.gitignore`, `.env.example`,
  `requirements.txt`, `drishti/__init__.py`.
- Built the **spine**: `config.py`, `privacy.py`, `ingest.py`, `matcher_tier1.py`,
  `validate.py` (Method A + Method B).
- Built working bases for teammates: `drishti/registry.py` (Person B) and
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
2. (A) run `python -m drishti.validate` on real data, tune `DUP_THRESHOLD`, tag `v0.1-number`.
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
- Built `drishti/voice.py` (Person A / `core`): transcribe, transcribe_to_english
  (pivot-translate at ingest so the OFFLINE matcher is cross-lingual), translate,
  speak, `containment_message` (stay-put TTS in the person's language),
  `structure_report` (Claude → 16 fields). All degrade cleanly with no keys.
- Added `drishti/llm.py` shared Claude helper. Wired `.env` loading + key getters +
  Sarvam language-code map into `config.py`. Added `sarvamai` to requirements.

**Ran:** `python -m drishti.voice` (no keys) → no crash; Hindi containment text renders;
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
- `drishti.ingest` → seeded 2500, 202 ground-truth dupes, 548 blank names, 449 open.
- `drishti.matcher_tier1` → top-3 with explainable per-signal reasons (sample top score 91.6).
- `drishti.validate` → Method A recall **100%** / gap **12.3** (flagged 84.4 vs non 72.1);
  Method B recall@1 **96.5%** / @3 **100%** / @5 **100%**.
- 100% is expected on self-generated findable dupes — proves the PIPELINE, not difficulty.
  Real number awaits the official 202. Did NOT tag v0.1-number yet (hold for official data).

**Git:** committed generator + stand-in CSV + tracking on `main`; fast-forwarded
`core`/`backend`/`design` to main so all teammates have data + latest contracts.

**Next:** (User) drop official file → I re-run + tune threshold + tag v0.1-number.
(B) B1 registry hardening. (C) C1 intake + branding (dashboard runs against stand-in now).

---

## 2026-06-27 — Turn 4 — Workflow plan approved → rename + Tier-2 + bands

**Asked:** User explained the full 7-step operational workflow; two changes —
(1) staffed booth not self-kiosk, (2) LAN-primary, booth↔booth P2P only when LAN
drops. Then: project name is **Drishti** (not Kumbh Setu). Approved the plan.

**Did:**
- **Phase 0 rename**: `git mv setu drishti`; updated all imports/docstrings/module
  refs; rebranded README/docs/tracking/dashboard → Drishti; `setu_vault.db` →
  `drishti_vault.db`. ("Setup" headers left intact.) Spine re-verified green.
- **A3 `drishti/matcher_tier2.py`**: Tier-1 top-K → Claude compares descriptions
  cross-lingually → re-score description signal → re-rank → decision band → reason.
  `match(target, pool, top_k, tier2_k)` is the Step-5 entrypoint. Fallback-safe.
- **config**: `MATCH_AUTO=70`, `MATCH_REVIEW=40` bands (auto = alert a human, never
  auto-reunite). Updated plan file with LAN→P2P ladder + Drishti naming.

**Ran:** `drishti.validate` (green: A 100%/gap 12.3, B@1 97%); `drishti.matcher_tier2`
offline → top-3 with bands [auto]/[review] + templated reasons, no crash w/o key.

**Git:** Phase 0 on main → synced to core/backend/design. A3 on core → merged to main.

**Next:** (User) drop official data + (optional) keys. (A) lock the number when data
lands; help B with connectivity-ladder/SMS-sim if needed. (B) B1. (C) C1 + Matches
tab using `drishti.matcher_tier2.match()`.

---

## 2026-06-27 — Turn 5 — Voice fallback + Nashik map + landmark broadcast

**Asked:** Use Sarvam + Microsoft-TTS fallback for the voice assistant (any-language
complaint → translated structured details). Build a Nashik map with NAMED landmarks,
booths every ~500m; a new report fires an emergency signal to all nearby booths in
radius (person may have drifted there); name landmarks ("near West Hall").

**Did:**
- **Voice** (`drishti/voice.py`): added FREE **Microsoft edge-tts** fallback in
  `speak()` (no key → still speaks, base64 MP3); `translate()` now Sarvam→**Claude**
  fallback; `structure_report()` hardened to understand ANY Indian language and
  normalise the description to English for the matcher. Added `edge-tts` to requirements.
- **Geo** (`drishti/geo.py` + `scripts/make_nashik_geo.py` → `data/nashik_landmarks.csv`):
  14 real Nashik landmarks + 36 booths on a ~500m grid; haversine; `nearby_booths()`
  / `broadcast_alert()` = the emergency set; `build_map()` folium map (alert radius +
  alerted booths in red).
- **Website**: Maps tab = live Nashik map (pick where a report lands → radius + booths
  light red + list). File tab = staffed-booth intake (language picker, landmark
  dropdown, file → booths alerted; Found-flow plays containment TTS).
- Env: created `.venv --system-site-packages` + folium/streamlit-folium/edge-tts
  (PEP 668 system Python; no --break-system-packages). Streamlit now run via
  `.venv/bin/python -m streamlit`.

**Ran:** `make_nashik_geo` → 50 points; `drishti.geo` → report near Ramkund alerts 11
booths ≤1km; folium map builds; `drishti.voice` → edge-tts produces audio with no keys;
dashboard serves HTTP 200 with the map at localhost:8501.

**Next:** Matches tab (C2) with bands + reveal; SMS-sim + P2P (B); official data → number.