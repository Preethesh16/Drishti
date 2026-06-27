# Person A — Core / AI Brain 🧠

**You are:** the matching engine + the validation number + the Claude integration + voice.
This is the spine and the moat. If everything else dies, A still demos a real number.

**Branch:** `core`  →  merge to `main` at every green checkpoint.
**You own:** `setu/config.py`, `setu/privacy.py`, `setu/ingest.py`, `setu/matcher_tier1.py`,
`setu/validate.py`, `setu/matcher_tier2.py`, `setu/voice.py`.

> Principle: **match on weak signals, not identifiers** (name/mobile stay hashed).
> Claude is the brain; everything else is plumbing. The core MUST run offline.

---

## Setup
```bash
git checkout -b core
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # set SETU_SALT now; ANTHROPIC_API_KEY later
# drop data/Synthetic_Missing_Persons_2500.csv (see data/README.md)
python -m setu.validate     # this is your heartbeat
```

## Phases

### A1 — Spine ✅ (DONE, scaffolded)
`config → privacy → ingest → matcher_tier1 → validate`. Proven on a synthetic
fixture: Method A recall 100%, Method B recall@1 90%. **Now run it on the REAL
2,500-row file** and read the actual number.

### A2 — Lock the number 🎯 (NEXT — do this the moment data lands)
- Run `python -m setu.validate` on the real file.
- **Tune `DUP_THRESHOLD` in `config.py`** against the 202 flagged rows: maximise
  recall while keeping the discrimination gap wide. Sweep 45→70, pick the knee.
- Lead with **recall + gap** (naive precision misleads — names collide by chance).
- Commit + tag `v0.1-number`. This is the milestone that wins the room.

### A3 — Tier-2 Claude (`matcher_tier2.py`)
- Only the top-K Tier-1 candidates go to Claude (cheap funnel — never the full pool).
- Claude does **cross-lingual description matching** + a **human-readable reason**
  ("saffron saree, rudraksha" ↔ "orange clothes, prayer beads" → same person, 0.86).
- Default `claude-sonnet-4-6`; escalate to `claude-opus-4-8` only on ambiguous ties.
- **Degrade cleanly with no `ANTHROPIC_API_KEY`** — fall back to Tier-1 score + a
  templated reason. The demo must never crash on a missing key.
- Use the Anthropic Python SDK (`anthropic` in requirements). Pivot-translate at
  ingest if Sarvam available so even the OFFLINE matcher is cross-lingual.

### A4 — Voice (`setu/voice.py`)
- Sarvam AI (if `SARVAM_API_KEY`) → ASR + translate + TTS for Indian languages.
- Operator speaks the family's report → transcribe → **Claude structures into the
  16 fields** → preview for the operator. Never force a form on a non-literate user.
- **Containment TTS**: on a FOUND log, speak to the person in their language
  *"Stay here, your family is being contacted."* Stopping drift is half the solve.
- Fallback with no key: typed structured fields (graceful degradation).

## The contract you expose (keep these stable — B and C depend on them)
```python
from setu.ingest import Record, load_records          # de-identified record + loader
from setu.matcher_tier1 import find_candidates, score # find_candidates(target, pool,
                                                       #   top_k=3, require_open=False)
                                                       #   -> list[ScoreResult]
# ScoreResult: .case_id  .score (0..100)  .raw  .reasons (dict signal->points)
from setu.privacy import hash_pii, mask_name, mask_mobile, reveal, audit
```

## Cut-lines (cut in THIS order, never the spine/number)
mesh → drift → **Tier-2** → maps. A2 (the number) and A1 (spine) are NEVER cut.
Voice + the reveal-on-confirm flow are demo gold — protect them after the spine.

## Definition of done per turn
Run the module, read the output, fix, commit. Update `PROGRESS.md`, `PHASE_LOG.md`,
`CONTEXT.md` every turn (hard rule).
