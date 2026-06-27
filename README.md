# 🪔 Drishti

**Reuniting missing persons at the Nashik Kumbh Mela 2027 — without surveilling anyone.**

> *"We don't track people or scan faces. We connect the two halves of every search —
> the family looking and the person found — across centers that today can't see each
> other, in any language, on weak data, without ever surveilling anyone."*

Built for the **Claude Impact Lab, Mumbai 2026** hackathon.

---

## The problem
~10 lost-and-found centers at the Kumbh are **disconnected silos**. A person *found* at
Center B is invisible to a family *searching* at Center A. The lost person is often
elderly or a child, non-literate, panicking, doesn't speak the local language, and
**usually cannot identify themselves**. Strong identifiers (name, phone) are missing or
useless (every relative calls from a different number).

## The fix
**One shared, live, de-identified registry** that **matches two reports about the same
person** on **weak signals** — age, gender, language, location, physical description —
**across languages**, and reveals real identity only at a **human-confirmed reunion**.

- **Claude is the brain** — structures voice intake, matches descriptions across languages
  ("saffron saree, rudraksha" ↔ "orange clothes, prayer beads"), explains every match.
- **Privacy is structural** — hash name + mobile at ingest, match blind, reveal-on-confirm
  with an audit log, purge raw PII after reunion.
- **Offline-first** — the core matcher and the validation number run with **pandas + stdlib
  only**, no network, no API key, no GPU. Capture never blocks on the network.
- **No facial recognition, no GPS tracking** — the CCTV data is coordinates only (no
  footage), and the lost person carries no device. We predict *where to look* and match
  *reports*; a human always confirms.

## What we do NOT do
We don't track the person and we don't scan faces. A human still brings them to a help
point — we make that fast by (a) instantly connecting the two reports and (b) a blind-spot
map that places help where separations cluster. Owning this boundary is the honest, senior
position; overclaiming gets dismantled in Q&A.

---

## The number that proves it
`validate.py` runs **offline in seconds** against the **202 real `is_duplicate_report`**
rows (Method A) and against **synthetic recovered pairs** (Method B), reporting recall and
the discrimination gap. Almost no team brings a real metric — this is the differentiator.

```bash
python -m drishti.validate
```

---

## Quick start
```bash
git clone git@github.com:Preethesh16/Drishti.git && cd Drishti
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # fill SETU_SALT (+ optional ANTHROPIC_API_KEY / SARVAM_API_KEY)

# Put the data files in data/  (see data/README — 5 CSVs + 4 KMLs)
python -m drishti.ingest          # -> "seeded 2500 records"
python -m drishti.validate        # -> THE NUMBER
streamlit run app/dashboard.py # operator UI
```

## Team & ownership
We build in parallel on three branches. See the per-person guides:
| Person | Role | Branch | Guide |
|---|---|---|---|
| **A** | Core / AI brain (matching, validation, Claude, voice) | `core` | [docs/PERSON_A_CORE.md](docs/PERSON_A_CORE.md) |
| **B** | Backend / database / sync | `backend` | [docs/PERSON_B_BACKEND.md](docs/PERSON_B_BACKEND.md) |
| **C** | Design / frontend / maps | `design` | [docs/PERSON_C_DESIGN.md](docs/PERSON_C_DESIGN.md) |

Live status: [PROGRESS.md](PROGRESS.md) · history: [PHASE_LOG.md](PHASE_LOG.md) ·
full context for any teammate/LLM: [CONTEXT.md](CONTEXT.md)

## Architecture (one screen)
```
INTAKE (voice-first, operator-mediated, landmark-based)
   │  "Lost someone?" / "Found someone?"
   ▼
THE REGISTRY  — one shared, live, retroactive, de-identified pool  (breaks the silos)
   ▼
INTELLIGENCE
   (A) MATCH ENGINE   — Tier-1 offline rules + Tier-2 Claude cross-lingual
   (B) DRIFT PREDICTOR— where to search (KML zone graph + behavioural priors)
   (C) BLIND-SPOT MAP — where to place help (CCTV coverage × separation hotspots)
   ▼
ACTION: targeted alert → nearest help point → HUMAN confirms → REUNITE
PRIVACY CORE (cross-cutting): hash at ingest · match blind · reveal-on-confirm + audit · purge
```
