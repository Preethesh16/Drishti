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
