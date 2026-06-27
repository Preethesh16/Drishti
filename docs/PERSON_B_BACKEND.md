# Person B — Backend / Database / Sync 🗄️

**You are:** the registry that breaks the silos, the privacy vault, the offline
sync, and the mesh simulation. You make the data *live, shared, and safe*.

**Branch:** `backend`  →  merge to `main` at every green checkpoint.
**You own:** `drishti/registry.py`, `drishti/mesh.py`, the vault, the audit/reveal storage,
and the thin API the dashboard calls.

> Principle: the registry is **one shared, live, retroactive, time-windowed,
> de-identified** pool. Capture **never blocks on the network**. The system that
> finds people never needs to know who they are until the moment of reunion.

A working minimal `registry.py` is already scaffolded (SQLite, `init_db`,
`add_record`, `get_records`, `set_status`, `confirm_match`, `seed_from_csv`).
Your job is to harden it into the real spine, in phases.

---

## Setup
```bash
git checkout -b backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # set SETU_SALT (must match A's salt for hashes to line up)
# drop data/Synthetic_Missing_Persons_2500.csv (see data/README.md)
python -m drishti.registry     # -> "registry seeded: 2500 records"
```

## Phases (each ends with a runnable checkpoint + commit)

### B1 — Registry hardening 🎯 (NEXT)
- Confirm `seed_from_csv()` loads all 2,500 into `registry.db`.
- **Separate the vault**: raw `missing_person_name` / `reporter_mobile` go into a
  distinct access-controlled `setu_vault.db` (gitignored), keyed by `vault_id`.
  The `records` table holds ONLY hashes + de-identified attributes. (`ingest.py`
  already returns `(records, vault)` — persist the vault separately.)
- Implement the **time-window** filter in `get_records(window_hours=...)` using
  `reported_at` (never scan the whole pool — only plausible open cases).

### B2 — Retroactive re-match hook
- When a **new report lands**, automatically run
  `drishti.matcher_tier1.find_candidates(new, get_records(open_only=True))` and store
  surfaced candidates. A FOUND report stays open as "bait"; the moment the family
  files anywhere, the match fires **backward** and links them. This is the live +
  retroactive behaviour that is the actual product.

### B3 — Offline queue + sync/merge (the offline-first core)
- On-device UUIDs so two offline booths never collide.
- Append-mostly local SQLite per node; `synced` flag + `origin_node` + `updated_at`
  already in the schema.
- **Conflict resolution**: terminal status (`Reunited`) wins; else last-writer-wins.
- Demo: two offline DBs diverge, then converge on sync with no central coordinator.

### B4 — Reveal-on-confirm + audit + purge
- `confirm_match` already marks both Reunited + writes a `CONFIRM_MATCH` audit line.
- Wire `privacy.reveal(case_id, vault_fields, actor, reason)` so raw contact surfaces
  ONLY here, with an audit line (who revealed what, when).
- **Purge** raw PII from the vault post-reunion, keep the hash. Consent flag at intake.

### B5 — Mesh simulation (`drishti/mesh.py`) — SLIDE + SIM ONLY, do NOT build real BLE/DTN
- A small `MeshNode` demo: a FOUND report created offline on Node A hops
  A→B→C→online→Claude match→ack relays back. Show UUID dedup/merge between two
  offline nodes. **Resist writing real networking code — it's a time sink.**
- Pitch line: *"epidemic routing needs device density — Kumbh is the densest crowd
  on Earth; the crowd that causes the separations becomes the network that carries
  the reports."*

### Stretch — thin API / MCP
- A function-level or FastAPI API the dashboard calls (decouple C from your internals).
- MCP server exposing the registry as a tool Claude queries (aligns with the govt
  "Agentic Kumbh / Kumbh Doot" blueprint). Build only if everything else is green.

## The contract you expose (keep stable — A and C depend on these)
```python
from drishti.registry import (
    init_db, add_record, get_records, set_status, confirm_match, seed_from_csv,
)
# get_records(open_only=False, window_hours=None) -> list[Record]
# add_record(Record) -> case_id
# confirm_match(case_a, case_b, actor="operator") -> audit line
```
Consume A's `Record` (from `drishti.ingest`) and `privacy` helpers; do not invent a
parallel record shape.

## Cut-lines
mesh (B5) is the first thing cut. Never cut B1 (the shared registry) — it IS the
"break the silos" story. B4 (privacy reveal) is demo gold.

## Definition of done per turn
Run it, read output, fix, commit. Update `PROGRESS.md`, `PHASE_LOG.md`, `CONTEXT.md`.
