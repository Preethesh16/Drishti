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

from drishti import config as C
from drishti import i18n

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

# ---- sidebar: website language + live DB status -----------------------------
with st.sidebar:
    ui_lang = st.selectbox("🌐 " + i18n.EN["ui_lang"], list(i18n.UI_LANGS),
                           help="Translates the whole interface.")
    T = i18n.translator(ui_lang)            # t(key) for the chosen UI language
    st.divider()
    st.subheader("🗄️ " + T("registry_live"))
    if init_err:
        st.error(f"DB not connected: {init_err}")
    else:
        s = api.stats()
        st.metric(T("records"), s["total"])
        st.caption(f"open {s['open']} · reunited {s['reunited']} · "
                   f"{s['centers']} centers · {s['languages']} languages")
        st.caption(f"vault: {s['vault_live']} live / {s['vault_purged']} purged (raw PII, 0600)")
        if "demo" in (seed_msg or ""):
            st.info("Demo data (data/ is empty). Drop the real CSV to replace.")
        if st.button("🔁 Reset demo data", use_container_width=True):
            api.reset()
            st.rerun()

st.title("🪔 Drishti — Nashik Kumbh 2027")
st.caption(T("tagline"))

tab_file, tab_registry, tab_matches, tab_maps, tab_validation, tab_mesh = st.tabs(
    [T("tab_file"), T("tab_registry"), T("tab_matches"),
     T("tab_maps"), T("tab_validation"), T("tab_mesh")]
)

# ---------------------------------------------------------------- File (intake)
with tab_file:
    st.header(T("file_header"))
    st.caption(T("nothing_mandatory"))
    if init_err:
        st.error(f"DB not connected: {init_err}")
    else:
        import base64
        import datetime
        import uuid
        from drishti import geo, llm, privacy, voice
        from drishti.ingest import Record

        def _idx(options, value, default=0):
            try:
                return options.index(value)
            except (ValueError, AttributeError):
                return default

        def _clean(x):  # drop the "unknown / not set" placeholders
            return "" if not x or x in ("Unknown", "—") else x

        def _say(text_en, lang_name):
            spoken = voice.translate(text_en, target_code=voice.lang_code(lang_name))
            return spoken, voice.speak(spoken, voice.lang_code(lang_name))

        fork = st.radio(T("what_happened"), [T("lost"), T("found")], horizontal=True)
        langs = list(C.SARVAM_LANG_CODES.keys())
        lang = st.selectbox(T("reporter_lang"), langs,
                            index=_idx(langs, (st.session_state.get("voice") or {})
                                       .get("fields", {}).get("language")))
        asr = ("Sarvam" if voice.have_sarvam() else
               "local Whisper (free)" if voice.have_asr() else "unavailable")
        brain = "Claude" if llm.have_claude() else "built-in heuristics"

        st.markdown("##### " + T("voice_assistant") + f"  ·  _ASR: {asr} · {brain}_")
        vmode = st.radio("vmode", [T("live_convo"), "⚡ One-shot"],
                         horizontal=True, label_visibility="collapsed")

        if vmode == "⚡ One-shot":
            # one recording → fills the whole form
            if st.button(f"{T('ask_in')} {lang}"):
                st.session_state["ask"] = _say(voice.assistant_prompt(), lang)
            ask = st.session_state.get("ask")
            if ask:
                st.info(f"🗣️ {ask[0]}")
                if ask[1]:
                    st.audio(base64.b64decode(ask[1]), format="audio/mp3", autoplay=True)
            clip = st.audio_input(T("record_answer"))
            if clip is not None:
                st.session_state["clip_bytes"] = clip.getvalue()
                if st.button(T("understand_fill")):
                    with st.spinner(f"{asr} + {brain}…"):
                        st.session_state["voice"] = voice.voice_to_fields(clip)
        else:
            # ChatGPT-style: assistant asks one question at a time, by voice
            qs = voice.CONVO_QUESTIONS
            convo = st.session_state.setdefault("convo", {"turn": -1, "collected": {},
                                                          "history": [], "q_text": "", "q_audio": None})

            def _ask_turn(i):
                convo["q_text"], convo["q_audio"] = _say(qs[i], lang)

            if convo["turn"] < 0:
                if st.button("▶ " + T("live_convo"), type="primary"):
                    convo["turn"] = 0
                    _ask_turn(0)
                    st.rerun()
            elif convo["turn"] < len(qs):
                turn = convo["turn"]
                st.info(f"🗣️ ({turn + 1}/{len(qs)}) {convo['q_text']}")
                if convo["q_audio"]:
                    st.audio(base64.b64decode(convo["q_audio"]), format="audio/mp3", autoplay=True)
                ans = st.audio_input(T("record_answer"), key=f"ans{turn}")
                b1, b2 = st.columns(2)
                if ans is not None and b1.button("✅ Answer → next question"):
                    st.session_state["clip_bytes"] = ans.getvalue()
                    with st.spinner(f"{asr} + {brain}…"):
                        txt = voice.transcribe_to_english(ans)
                        ext = (voice.structure_report(txt) or voice._heuristic_fields(txt)) if txt else {}
                        convo["collected"] = voice.merge_fields(convo["collected"], ext)
                        convo["history"].append(txt or "")
                    convo["turn"] += 1
                    if convo["turn"] < len(qs):
                        _ask_turn(convo["turn"])
                    st.rerun()
                if b2.button("⏭ Skip / finish"):
                    convo["turn"] = len(qs)
                    st.rerun()
            else:
                st.success("✅ Conversation complete — review the fields below and file.")
                if st.button("🔄 Restart conversation"):
                    st.session_state.pop("convo", None)
                    st.rerun()
            # feed whatever the conversation collected into the shared form fields
            st.session_state["voice"] = {
                "transcript": " · ".join(t for t in convo.get("history", []) if t),
                "fields": convo.get("collected", {}), "asr": True,
                "structured": llm.have_claude()}
            if convo.get("collected"):
                st.caption("📋 " + " · ".join(f"**{k}**: {vv}" for k, vv in convo["collected"].items()))

        v = st.session_state.get("voice") or {}
        vf = v.get("fields", {}) if v else {}
        if v.get("transcript") and vmode == "⚡ One-shot":
            st.success(f"🗣️ Heard (→ English): “{v['transcript']}”")

        # ---- the form (voice-filled when you transcribe; everything optional) ----
        st.markdown("##### " + T("details_optional"))
        r1, r2, r3 = st.columns(3)
        reporter_name = r1.text_input(T("your_name"), value=vf.get("reporter_name", ""))
        relation = r2.text_input(T("relation"), value=vf.get("relation", ""),
                                 placeholder="son, wife, friend…")
        person_name = r3.text_input(T("their_name"), value=vf.get("missing_person_name", ""))

        g1, g2, g3 = st.columns(3)
        gender = g1.selectbox(T("gender"), ["Unknown", "Male", "Female"],
                              index=_idx(["Unknown", "Male", "Female"], vf.get("gender")))
        age_opts = ["—"] + C.AGE_ORDER
        age = g2.selectbox(T("age"), age_opts, index=_idx(age_opts, vf.get("age_band")))
        try:
            booth_names = [p.name for p in geo.load_points()]
            seen_near = g3.selectbox(T("last_seen"), booth_names,
                                     index=_idx(booth_names, vf.get("last_seen_location")))
        except Exception:
            seen_near = g3.text_input(T("last_seen"), vf.get("last_seen_location", ""))

        h1, h2, h3 = st.columns(3)
        height = h1.selectbox(T("height"), ["Unknown", "Tall", "Average", "Short"],
                              index=_idx(["Unknown", "Tall", "Average", "Short"], vf.get("height")))
        build = h2.selectbox(T("build"), ["Unknown", "Thin", "Average", "Heavy"],
                             index=_idx(["Unknown", "Thin", "Average", "Heavy"], vf.get("build")))
        complexion = h3.selectbox(T("complexion"), ["Unknown", "Fair", "Medium", "Dark"],
                                  index=_idx(["Unknown", "Fair", "Medium", "Dark"], vf.get("complexion")))
        hr1, hr2 = st.columns(2)
        hair_len = hr1.selectbox(T("hair_length"), ["Unknown", "Long", "Short", "Bald"],
                                 index=_idx(["Unknown", "Long", "Short", "Bald"], vf.get("hair_length")))
        hair_color = hr2.text_input(T("hair_color"), value=vf.get("hair_color", ""),
                                    placeholder="black, grey, white…")
        clothing = st.text_input(T("wearing"), value=vf.get("clothing", ""),
                                 placeholder="saffron kurta, blue saree…")
        marks = st.text_input(T("marks"), value=vf.get("marks", ""),
                              placeholder="mole, scar, walking stick, glasses, hard of hearing")
        notes = st.text_area(T("anything_else"), value="")
        mobile = st.text_input(T("contact"), value="")

        if st.button(T("file_report"), type="primary"):
            case_id = "KMP-2027-" + uuid.uuid4().hex[:5].upper()
            rtype = "missing" if fork.startswith("🔍") else "found"
            # compose an English description from the optional appearance fields
            bits = [b for b in [
                _clean(height) and f"{height.lower()} height",
                _clean(build) and f"{build.lower()} build",
                _clean(hair_len) and f"{hair_len.lower()} hair",
                _clean(hair_color) and f"{hair_color} hair",
                _clean(complexion) and f"{complexion.lower()} complexion",
                _clean(clothing), _clean(marks), _clean(notes),
            ] if b]
            desc = ", ".join(bits) or vf.get("physical_description", "")
            rep = "; ".join(b for b in [
                reporter_name and f"reporter: {reporter_name}",
                relation and f"relation: {relation}"] if b)
            rec = Record(
                case_id=case_id,
                reported_at=datetime.datetime.now().isoformat(timespec="minutes"),
                gender=gender, age_band=_clean(age), state="", district="", language=lang,
                last_seen_location=seen_near, reporting_center="Booth Intake",
                physical_description=desc, status="Pending",
                name_hash=privacy.hash_pii(person_name), mobile_hash=privacy.hash_pii(mobile),
                remarks=rep, vault_id=case_id, report_type=rtype)
            try:
                api.file_report(rec, name=person_name or None, mobile=mobile or None)
                st.success(f"Filed **{case_id}** → registry + vault. Slip printed.")
            except Exception as e:
                st.error(f"Persist failed: {e}")
            # keep the voice recording with the case (gitignored, PII-bearing)
            if st.session_state.get("clip_bytes"):
                d = C.ROOT / "data" / "voice_clips"
                d.mkdir(parents=True, exist_ok=True)
                (d / f"{case_id}.wav").write_bytes(st.session_state["clip_bytes"])
                st.caption(f"🎙️ Voice recording saved with {case_id}.")
            # emergency broadcast to nearby booths (person may have drifted)
            try:
                payload = geo.broadcast_alert(seen_near, radius_m=1000)
                st.warning(f"🚨 Emergency signal → **{payload['count']} booths** within "
                           f"1 km of *{seen_near}*: "
                           + ", ".join(b["name"] for b in payload["alerted_booths"][:8]))
            except Exception:
                pass
            if rtype == "found":
                txt, audio = voice.containment_message(lang)
                st.info(f"🔊 Spoken to the found person in {lang}: “{txt}”")
                if audio:
                    st.audio(base64.b64decode(audio), format="audio/mp3")
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
    st.header(T("registry_header"))
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
    st.header(T("matches_header"))
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
                # Tier-2 decision bands (config): auto≥70 alert a human, review≥40, else low
                if m["score"] >= C.MATCH_AUTO:
                    band = "🟢 AUTO"
                elif m["score"] >= C.MATCH_REVIEW:
                    band = "🟡 REVIEW"
                else:
                    band = "⚪ low"
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(
                        f"**{m['case_id']}** · {m['report_type']} · {m['gender']} "
                        f"{m['age_band']} · {m['language']} @ {m['last_seen_location']} "
                        f"· _{m['reporting_center']}_  \n“{m['physical_description']}”")
                    c2.metric("score", f"{m['score']:.0f}", band)
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
    st.header("🗺️ " + T("maps_header"))
    try:
        from drishti import geo, drift, blindspot
        from streamlit_folium import st_folium
        names = [p.name for p in geo.load_points()]
        d_idx = names.index("Ramkund Ghat") if "Ramkund Ghat" in names else 0
        mt1, mt2, mt3 = st.tabs(["🚨 Live broadcast", "🧭 Drift predictor", "📷 Blind-spot map"])

        with mt1:
            left, right = st.columns([1, 2])
            with left:
                origin = st.selectbox("A report comes in near…", names, index=d_idx, key="bc")
                radius = st.slider("Emergency radius (m)", 300, 2000, 1000, 100)
                payload = geo.broadcast_alert(origin, radius_m=radius)
                st.metric("🚨 Booths alerted", payload["count"])
                st.caption("Every booth in the radius gets the signal — the person may have drifted there.")
                for b in payload["alerted_booths"][:12]:
                    st.write(f"• {b['name']} — {b['distance_m']} m")
            with right:
                st_folium(geo.build_map(highlight=origin, radius_m=radius),
                          height=480, use_container_width=True, returned_objects=[])

        with mt2:
            st.caption("Bounded by walking speed (~1–2 km/h) + behavioural priors → "
                       "alert ONLY the likely zones, not all 50 booths.")
            d1, d2, d3 = st.columns(3)
            ls = d1.selectbox("Last seen near", names, index=d_idx, key="dr")
            prof = d2.selectbox("Profile", ["elderly", "child", "adult"])
            elapsed = d3.slider("Missing for (hours)", 0.5, 8.0, 2.0, 0.5)
            for z in drift.predict(ls, elapsed, prof, top_k=6):
                st.write(f"**{z['probability']*100:.0f}%** · {z['name']} "
                         f"({z['distance_m']} m, {z['type']})")
            st.caption("elderly → anchor landmarks · child → close & erratic · adult → exits")

        with mt3:
            st.caption("High crowd-separation pressure × few cameras = where people vanish "
                       "unseen → place kiosks/volunteers here BEFORE the surge.")
            l, r = st.columns([1, 2])
            with l:
                for d in blindspot.rank_blind_spots(top_k=10):
                    st.write(f"🚨 **{d['name']}** — pressure {d['pressure']}, {d['cameras']} cams")
            with r:
                st_folium(blindspot.build_map(top_k=12), height=480,
                          use_container_width=True, returned_objects=[])
    except Exception as e:
        st.warning("Maps need the venv (folium + streamlit-folium) and "
                   "`python scripts/make_nashik_geo.py`.\n\n" + str(e))

# ---------------------------------------------------------------- Validation
with tab_validation:
    st.header(T("validation_header"))
    if st.button(T("run_validation")):
        try:
            from drishti.validate import run
            with st.spinner("scoring…"):
                res = run()
            st.json(res)
        except Exception as e:
            st.error(f"Need data/ populated to run validation on real data: {e}")

# ---------------------------------------------------------------- Mesh
with tab_mesh:
    st.header("📡 " + T("mesh_header"))
    st.caption("Capture NEVER blocks. Normal: booths sync to central over LAN. LAN down: "
               "booths sync peer-to-peer with neighbours. Worst case: one SMS carries the report.")
    from drishti import mesh, sms
    if st.button("▶ Run booth↔booth P2P sim (LAN-loss fallback)"):
        res = mesh.run_demo()
        for e in res["events"]:
            st.write(e)
        st.success(f"Converged (terminal-status-wins): {res['converged']} · "
                   f"central state: {res['final']}")
    st.divider()
    st.markdown("##### 📨 SMS bridge (no-signal fallback)")
    st.caption("A low-end phone / field radio sends: TYPE|GENDER|AGE|STATE|LOCATION")
    line = st.text_input("Inbound SMS", "MISSING|F|65|Bihar|SectorB")
    parsed = sms.parse_inbound(line)
    st.write("parsed →", parsed or "invalid format")
