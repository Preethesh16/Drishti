# 🪔 Drishti — the pitch

**Reuniting the lost at the Nashik Kumbh Mela 2027 — without surveilling anyone.**

> *"We don't track people or scan faces. We connect the two halves of every search —
> the family looking and the person found — across centers that today can't see each
> other, in any language, on weak data, without ever surveilling anyone."*

---

## The problem (one line)
**Center A found someone. Center B has the family. They never talk to each other.**

~10 lost-and-found centers run as disconnected notebooks. The lost person is usually
elderly or a child — non-literate, panicking, doesn't speak the local language, no phone,
**often cannot say their own name.** Names and mobiles are missing or useless (a different
relative calls each time).

## The fix
**One shared, live, de-identified registry** that matches two reports about the same
person on **weak signals** — age, gender, language, location, description — **across
languages**, and reveals identity only at a **human-confirmed reunion**.

## How it works (60 seconds)
1. **Staffed booth, voice-first.** A volunteer's tablet listens; the family speaks any
   language (Tamil, Bhojpuri…). Speech → transcribed → **Claude structures it into fields**.
2. **Privacy at the door.** Name + mobile are hashed instantly; the searchable system
   never sees who it is. A Case-ID slip prints.
3. **One registry.** Every report — missing and found — lands in one shared pool. Silos broken.
4. **Where to look.** A **drift predictor** ranks likely zones (walking speed + behaviour:
   elderly anchor to landmarks, children stay close, adults head for exits) → alert only those.
5. **Match on clues, not names.** Found vs missing on weak signals; **Claude compares
   descriptions across languages** ("saffron saree" = "orange clothes"). Score → band:
   **≥70 auto-alert a human · 40–69 review · <40 none.**
6. **Human confirms → reveal.** Only now does real contact surface, audited, then purged.
   Every booth is told **"stop searching."**

## Why it wins
- **A real number.** `validate.py` recovers hidden duplicates from the 202 labelled rows,
  offline, in seconds. Almost no team brings a metric.
- **The cross-lingual moat.** A SQL/keyword matcher cannot match "saffron saree, rudraksha"
  to "orange clothes, prayer beads." Claude can.
- **Privacy is structural,** not a checkbox: hash at ingest, match blind, reveal-on-confirm
  + audit, purge after reunion.
- **Free & offline-first.** Core matcher + the number run on pandas+stdlib, no key, no GPU.
  Voice works free (local Whisper + Microsoft edge-TTS); a Sarvam key upgrades accuracy.
- **Resilient by design.** LAN → booth↔booth P2P (on LAN loss) → local queue → SMS.

## The honest boundary (say it first)
We don't track the person and we don't scan faces. A human still walks them to a help
point — we make that fast by (a) instantly connecting the two reports and (b) the
**blind-spot map** that places help where separations cluster (high crowd pressure × few
cameras). **No facial recognition. No GPS tracking.**

## The three lines that land
1. *"We match on the two halves of every search — the family looking and the person found."*
2. *"202 hidden duplicates in the data; we recover the large majority — here's the live metric."*
3. *"The system that finds people never needs to know who they are until the moment of reunion."*
