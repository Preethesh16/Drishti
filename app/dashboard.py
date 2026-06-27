"""Operator dashboard — Streamlit.  [PERSON C owns this file]

Tabs: File · Registry · Matches · Maps · Validation · (Mesh)
This is a WORKING SKELETON wired to the real backend so C designs against live
data from minute one. Run:  streamlit run app/dashboard.py

Design north star: a panicking, non-literate reporter is served by a VOLUNTEER.
The UI must be calm, big-type, voice-first, two big forks: "Lost someone?" /
"Found someone?". Judges should SEE: the silos merging, a cross-lingual match
with a human-readable reason, and the reveal-on-confirm privacy moment.
"""
from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Kumbh Setu", page_icon="🪔", layout="wide")

# Lazy imports so the app still loads if optional deps/data are missing.
def _load_records():
    try:
        from setu.ingest import load_records
        recs, _ = load_records()
        return recs, None
    except Exception as e:  # data not present yet
        return [], str(e)


st.title("🪔 Kumbh Setu — reuniting the lost at Nashik Kumbh 2027")
st.caption("We don't track people or scan faces. We connect the two halves of "
           "every search — the family looking and the person found — across "
           "centers that today can't see each other, in any language, on weak "
           "data, without ever surveilling anyone.")

tab_file, tab_registry, tab_matches, tab_maps, tab_validation, tab_mesh = st.tabs(
    ["📝 File", "📚 Registry", "🔗 Matches", "🗺️ Maps", "✅ Validation", "📡 Mesh"]
)

records, err = _load_records()

with tab_file:
    st.header("Intake — voice-first, operator-mediated")
    st.info("PERSON C: build the two big forks (Lost / Found), voice button "
            "(setu.voice), landmark location picker. Keep it brain-dead simple.")
    col1, col2 = st.columns(2)
    col1.button("🔍 Lost someone?", use_container_width=True)
    col2.button("🙋 Found someone?", use_container_width=True)

with tab_registry:
    st.header("The shared registry")
    if err:
        st.warning(f"Data not loaded yet — drop the CSVs into data/. ({err})")
    else:
        st.metric("De-identified records", len(records))
        st.dataframe(
            [{"case_id": r.case_id, "gender": r.gender, "age": r.age_band,
              "language": r.language, "location": r.last_seen_location,
              "status": r.status, "center": r.reporting_center}
             for r in records[:200]],
            use_container_width=True,
        )

with tab_matches:
    st.header("Matches — top-3 with explainable confidence")
    st.info("PERSON C + A: pick a record, call setu.matcher_tier1.find_candidates, "
            "render score + per-signal reasons + the reveal-on-confirm button.")

with tab_maps:
    st.header("Drift predictor & blind-spot map")
    st.info("PERSON C: folium overlays from setu.geo / drift / blindspot (phase 6).")

with tab_validation:
    st.header("THE NUMBER")
    if st.button("Run validation (offline)"):
        try:
            from setu.validate import run
            with st.spinner("scoring…"):
                res = run()
            st.json(res)
        except Exception as e:
            st.error(f"Need data/ populated to run validation: {e}")

with tab_mesh:
    st.header("Offline mesh (simulated)")
    st.info("PERSON B: simulated DTN hop A→B→C→online→match→ack (phase 7).")
