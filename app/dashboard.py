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

st.set_page_config(page_title="Drishti", page_icon="🪔", layout="wide")

# Lazy imports so the app still loads if optional deps/data are missing.
def _load_records():
    try:
        from drishti.ingest import load_records
        recs, _ = load_records()
        return recs, None
    except Exception as e:  # data not present yet
        return [], str(e)


st.title("🪔 Drishti — reuniting the lost at Nashik Kumbh 2027")
st.caption("We don't track people or scan faces. We connect the two halves of "
           "every search — the family looking and the person found — across "
           "centers that today can't see each other, in any language, on weak "
           "data, without ever surveilling anyone.")

tab_file, tab_registry, tab_matches, tab_maps, tab_validation, tab_mesh = st.tabs(
    ["📝 File", "📚 Registry", "🔗 Matches", "🗺️ Maps", "✅ Validation", "📡 Mesh"]
)

records, err = _load_records()

with tab_file:
    st.header("Intake — staffed booth, voice-first, any language")
    from drishti import config as C
    fork = st.radio("What happened?", ["🔍 Lost someone", "🙋 Found someone"],
                    horizontal=True)
    lang = st.selectbox("Reporter's language", list(C.SARVAM_LANG_CODES.keys()))
    st.caption("Operator holds to speak; the report may be in ANY language "
               "(Tamil, Bhojpuri…) — Claude translates it and fills the fields.")
    try:
        from drishti import geo
        names = [p.name for p in geo.load_points()]
        seen_near = st.selectbox("Last seen near (landmark / booth)", names)
    except Exception:
        seen_near = st.text_input("Last seen near (landmark)", "Ramkund Ghat")
    desc = st.text_area("Description (operator speaks; any language)",
                        placeholder="e.g. saffron kurta, walking stick, hard of hearing")
    if st.button("✓ File report (prints Case-ID slip)"):
        try:
            from drishti import geo
            payload = geo.broadcast_alert(seen_near, radius_m=1000)
            st.success(f"Filed · slip printed. 🚨 Emergency signal sent to "
                       f"**{payload['count']} booths** within 1 km of *{seen_near}* "
                       f"(the person may have drifted there).")
            st.write(", ".join(b["name"] for b in payload["alerted_booths"][:10]))
        except Exception as e:
            st.warning(f"Run scripts/make_nashik_geo.py first. ({e})")
        if fork.startswith("🙋"):
            try:
                import base64
                from drishti import voice
                txt, audio = voice.containment_message(lang)
                st.info(f"🔊 Spoken to the found person in {lang}: “{txt}”")
                if audio:
                    st.audio(base64.b64decode(audio), format="audio/mp3")
            except Exception as e:
                st.caption(f"(voice fallback unavailable: {e})")

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
    st.info("PERSON C + A: pick a record, call drishti.matcher_tier1.find_candidates, "
            "render score + per-signal reasons + the reveal-on-confirm button.")

with tab_maps:
    st.header("🗺️ Nashik Kumbh — named landmarks · booths every ~500 m · live broadcast")
    try:
        from drishti import geo
        from streamlit_folium import st_folium
        pts = geo.load_points()
        names = [p.name for p in pts]
        default = names.index("Ramkund Ghat") if "Ramkund Ghat" in names else 0
        left, right = st.columns([1, 2])
        with left:
            origin = st.selectbox("A report comes in near…", names, index=default)
            radius = st.slider("Emergency radius (m)", 300, 2000, 1000, 100)
            payload = geo.broadcast_alert(origin, radius_m=radius)
            st.metric("🚨 Booths alerted", payload["count"])
            st.caption("Every booth in the radius gets the signal — the lost "
                       "person may have walked there.")
            for b in payload["alerted_booths"][:12]:
                st.write(f"• {b['name']} — {b['distance_m']} m")
        with right:
            fmap = geo.build_map(highlight=origin, radius_m=radius)
            st_folium(fmap, height=520, use_container_width=True,
                      returned_objects=[])
    except Exception as e:
        st.warning("Map needs the venv (folium + streamlit-folium) and "
                   "`python scripts/make_nashik_geo.py`.\n\n" + str(e))

with tab_validation:
    st.header("THE NUMBER")
    if st.button("Run validation (offline)"):
        try:
            from drishti.validate import run
            with st.spinner("scoring…"):
                res = run()
            st.json(res)
        except Exception as e:
            st.error(f"Need data/ populated to run validation: {e}")

with tab_mesh:
    st.header("Offline mesh (simulated)")
    st.info("PERSON B: simulated DTN hop A→B→C→online→match→ack (phase 7).")
