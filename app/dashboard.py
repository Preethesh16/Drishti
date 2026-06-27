"""Operator dashboard — Streamlit.  [PERSON C owns the design; PERSON B wired the DB]

Tabs: File · Registry · Matches · Maps · Validation · (Mesh)
Now connected to the LIVE backend: every tab reads/writes the shared registry.db
+ access-controlled drishti_vault.db through `drishti.api` — no CSV, no direct SQLite.
On first launch it auto-seeds (real CSV if present in data/, else a small demo set),
so the DB connection works the instant you run it. Run:  streamlit run app/dashboard.py

Design north star (PERSON C): a panicking, non-literate reporter is served by a
VOLUNTEER. Calm, big-type, voice-first, two big forks: "Lost someone?" /
"Found someone?". Judges should SEE the silos merging, a cross-lingual match with
a human-readable reason, and the reveal-on-confirm privacy moment.
"""
from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Drishti", page_icon="🪔", layout="wide")

# The thin backend door (Person B). Lazy so the app still loads if deps are missing.
def _api():
    from drishti import api
    return api


def _ensure():
    try:
        api = _api()
        msg = api.ensure_seeded()
        return api, msg, None
    except Exception as e:  # pragma: no cover - surfaced in the UI
        return None, None, str(e)


api, seed_msg, init_err = _ensure()

st.title("🪔 Drishti — reuniting the lost at Nashik Kumbh 2027")
st.caption("We don't track people or scan faces. We connect the two halves of "
           "every search — the family looking and the person found — across "
           "centers that today can't see each other, in any language, on weak "
           "data, without ever surveilling anyone.")

# ---- sidebar: live DB connection status + demo controls ---------------------
with st.sidebar:
    st.subheader("🗄️ Registry (live DB)")
    if init_err:
        st.error(f"DB not connected: {init_err}")
    else:
        s = api.stats()
        st.metric("De-identified records", s["total"])
        st.caption(f"open {s['open']} · reunited {s['reunited']} · "
                   f"{s['centers']} centers · {s['languages']} languages")
        st.caption(f"vault: {s['vault_live']} live / {s['vault_purged']} purged (raw PII, 0600)")
        if "demo" in (seed_msg or ""):
            st.info("Demo data (data/ is empty). Drop the real CSV to replace.")
        if st.button("🔁 Reset demo data", use_container_width=True):
            api.reset()
            st.rerun()

tab_file, tab_registry, tab_matches, tab_maps, tab_validation, tab_mesh = st.tabs(
    ["📝 File", "📚 Registry", "🔗 Matches", "🗺️ Maps", "✅ Validation", "📡 Mesh"]
)

# ---------------------------------------------------------------- File (intake)
with tab_file:
    st.header("Intake — staffed booth, voice-first, any language")
    if init_err:
        st.error(f"DB not connected: {init_err}")
    else:
        import base64
        import datetime
        import uuid
        from drishti import config as C
        from drishti import geo, privacy, voice
        from drishti.ingest import Record

        fork = st.radio("What happened?", ["🔍 Lost someone", "🙋 Found someone"],
                        horizontal=True)
        st.caption("Operator holds to speak; the report may be in ANY language "
                   "(Tamil, Bhojpuri…) — Claude translates it and fills the fields.")
        c1, c2, c3 = st.columns(3)
        lang = c1.selectbox("Language", list(C.SARVAM_LANG_CODES.keys()))
        gender = c2.selectbox("Gender", ["Unknown", "Male", "Female"])
        age = c3.selectbox("Age band", C.AGE_ORDER, index=4)
        try:
            seen_near = st.selectbox("Last seen near (landmark / booth)",
                                     [p.name for p in geo.load_points()])
        except Exception:
            seen_near = st.text_input("Last seen near (landmark)", "Ramkund Ghat")
        desc = st.text_area("Description (operator speaks; any language)",
                            placeholder="e.g. saffron kurta, walking stick, hard of hearing")
        with st.expander("Name / phone (optional — most reporters don't know)"):
            name = st.text_input("Name")
            mobile = st.text_input("Mobile")

        if st.button("✓ File report (prints Case-ID slip)"):
            case_id = "KMP-2027-" + uuid.uuid4().hex[:5].upper()
            rtype = "missing" if fork.startswith("🔍") else "found"
            rec = Record(
                case_id=case_id,
                reported_at=datetime.datetime.now().isoformat(timespec="minutes"),
                gender=gender, age_band=age, state="", district="", language=lang,
                last_seen_location=seen_near, reporting_center="Booth Intake",
                physical_description=desc, status="Pending",
                name_hash=privacy.hash_pii(name), mobile_hash=privacy.hash_pii(mobile),
                vault_id=case_id, report_type=rtype)
            try:
                api.file_report(rec, name=name or None, mobile=mobile or None)
                st.success(f"Filed **{case_id}** → registry + vault. Slip printed.")
            except Exception as e:
                st.error(f"Persist failed: {e}")
            # emergency broadcast to nearby booths (person may have drifted)
            try:
                payload = geo.broadcast_alert(seen_near, radius_m=1000)
                st.warning(f"🚨 Emergency signal → **{payload['count']} booths** within "
                           f"1 km of *{seen_near}*: "
                           + ", ".join(b["name"] for b in payload["alerted_booths"][:8]))
            except Exception:
                pass
            # found-flow: speak the "stay here" containment message in their language
            if rtype == "found":
                txt, audio = voice.containment_message(lang)
                st.info(f"🔊 Spoken to the found person in {lang}: “{txt}”")
                if audio:
                    st.audio(base64.b64decode(audio), format="audio/mp3")
            # instant retroactive match against the open pool
            try:
                ms = api.find_matches(case_id, top_k=3)
                if ms:
                    st.markdown("**Instant matches in the open pool:**")
                    for m in ms:
                        st.write(f"• {m['case_id']} — score {m['score']:.0f} "
                                 f"({'🟢 strong' if m['is_strong'] else '🟡 weak'})")
            except Exception:
                pass

# ---------------------------------------------------------------- Registry
with tab_registry:
    st.header("The shared registry — one pool, all centers")
    if init_err:
        st.error(f"DB not connected: {init_err}")
    else:
        only_open = st.toggle("Show only open (matchable) cases", value=False)
        recs = api.list_records(open_only=only_open, limit=300)
        st.caption(f"{len(recs)} records — de-identified (no name/mobile; those live "
                   "hashed in the vault and surface only at reunion).")
        st.dataframe(
            [{"case_id": r.case_id, "type": r.report_type, "gender": r.gender,
              "age": r.age_band, "language": r.language,
              "location": r.last_seen_location, "center": r.reporting_center,
              "status": r.status, "reported_at": r.reported_at}
             for r in recs],
            use_container_width=True, hide_index=True,
        )

# ---------------------------------------------------------------- Matches
with tab_matches:
    st.header("Matches — top-3 with explainable confidence")
    if init_err:
        st.error(f"DB not connected: {init_err}")
    else:
        open_recs = api.list_records(open_only=True)
        if not open_recs:
            st.warning("No open cases in the registry.")
        else:
            labels = {f"{r.case_id} · {r.report_type} · {r.gender} {r.age_band} · "
                      f"{r.language} @ {r.last_seen_location} ({r.reporting_center})": r.case_id
                      for r in open_recs}
            picked = st.selectbox("Pick an open report to match", list(labels))
            case_id = labels[picked]
            target = api.get_record(case_id)
            st.caption(f"“{target.physical_description}”")

            matches = api.find_matches(case_id, top_k=3)
            if not matches:
                st.info("No candidates in the time-windowed open pool yet.")
            for m in matches:
                strong = "🟢 strong" if m["is_strong"] else "🟡 weak"
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(
                        f"**{m['case_id']}** · {m['report_type']} · {m['gender']} "
                        f"{m['age_band']} · {m['language']} @ {m['last_seen_location']} "
                        f"· _{m['reporting_center']}_  \n“{m['physical_description']}”")
                    c2.metric("score", f"{m['score']:.0f}", strong)
                    st.caption("why: " + " · ".join(f"{k}+{v}" for k, v in m["reasons"].items()))
                    # the reveal-on-confirm privacy moment
                    if st.button(f"✅ Confirm reunion: {case_id} ↔ {m['case_id']}",
                                 key=f"confirm_{case_id}_{m['case_id']}"):
                        res = api.confirm(case_id, m["case_id"], actor="operator",
                                          reason="operator-confirmed at help point")
                        st.session_state["last_confirm"] = res
                        st.rerun()

            res = st.session_state.get("last_confirm")
            if res:
                st.success(f"🎉 {res['summary']} — both marked Reunited.")
                contacts = [f"{c}: {v.get('reporter_mobile') or '—'} "
                            f"({v.get('missing_person_name') or 'unnamed'})"
                            for c, v in res["revealed"].items()]
                st.markdown("**Revealed contact (call now):** " +
                            (" · ".join(contacts) if contacts else "—"))
                st.caption(f"Raw PII purged from the vault for {res['purged']} "
                           "(hash kept). Every reveal/purge is in audit.log.")
                if st.button("Dismiss"):
                    del st.session_state["last_confirm"]
                    st.rerun()

# ---------------------------------------------------------------- Maps
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

# ---------------------------------------------------------------- Validation
with tab_validation:
    st.header("THE NUMBER")
    if st.button("Run validation (offline)"):
        try:
            from drishti.validate import run
            with st.spinner("scoring…"):
                res = run()
            st.json(res)
        except Exception as e:
            st.error(f"Need data/ populated to run validation on real data: {e}")

# ---------------------------------------------------------------- Mesh
with tab_mesh:
    st.header("Offline mesh (simulated)")
    st.info("PERSON B: simulated DTN hop A→B→C→online→match→ack (phase B5).")
