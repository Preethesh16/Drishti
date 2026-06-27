# 🎬 Drishti — 3-minute demo script

**Setup:** `.venv/bin/python -m streamlit run app/dashboard.py` → open http://localhost:8501
(auto-seeds 2,500 de-identified records; voice + maps work with no API keys).

---

### 0:00 — The hook (sidebar + Registry tab)
> "80 million people at the Kumbh. Every day families get separated — usually an elderly
> parent or a child who can't say their own name. Today ~10 lost-and-found centers are
> disconnected notebooks."

Point at the **sidebar**: one live registry, N records, X centers, Y languages, vault
live/purged. Open **📚 Registry** → "This is every center's reports in *one* pool. The
silos are broken."

### 0:30 — Voice intake, any language (📝 File tab)
> "A panicking villager won't use an app — but they'll talk to a volunteer."

- Hit **🎙️ record**, speak a report (even in Hindi/Tamil). Click **🧠 Transcribe & auto-fill**.
- Show it transcribed **to English** and the **fields auto-filled** (ASR: local Whisper/Sarvam;
  understanding: Claude). "No form. Name/phone optional — most don't know them."
- Pick **Found**, file it → **Case-ID slip**, the 🔊 **"stay here" message** plays in their
  language, and a **🚨 emergency broadcast** lights up nearby booths.

### 1:15 — Where to search (🗺️ Maps → Drift predictor)
> "We don't search everywhere. We predict where they drifted."

- **Drift predictor**: last seen Ramkund, profile *elderly*, 2h → ranked zones (anchors to
  temples). Switch to *adult* → it shifts to **exits**. "Alert only those booths."

### 1:45 — The match (🔗 Matches tab) — the core
> "Names are useless here. We match on clues."

- Pick an open case → **top-3** with **score + per-signal reasons** + **band** (🟢 AUTO /
  🟡 REVIEW). "Claude matched the descriptions *across languages* — a SQL database can't."

### 2:15 — The privacy money-shot (same tab)
- Click **✅ Confirm reunion** → real **name + mobile appear ONLY now**, audited, then
  **purged** (hash kept). "The system that finds people never knew who they were until this moment."

### 2:35 — The proof (✅ Validation tab)
- Click **Run validation** → **recall on the 202 known duplicates** + recall@1/3/5.
  "Almost no team brings a real number."

### 2:50 — Resilience + the honest boundary (📡 Mesh tab)
- Run the **booth↔booth P2P sim**: LAN down → booths converge → terminal status wins.
  "Capture never blocks: LAN → P2P → SMS."
> "We don't track anyone and we don't scan faces. A human still brings them in — we make
> that fast, and we place help where the **blind-spot map** says people vanish."

---

**If asked "how does a wandering person become a 'found' record?"** → Blind-spot map tab:
high crowd-pressure × few cameras = where to put catch-points; plus the containment message
that makes found people stay put.
