"""Multi-language UI (i18n) for the website.

English is the source of truth. Hindi + Marathi ship offline (always work). Any
other selected language is live-translated by Claude once and cached; with no
key it falls back to English. So the operator can run the whole site in their
language.
"""
from __future__ import annotations

# display name -> language English-name + code (code is just informational)
UI_LANGS = {
    "English": "English", "हिन्दी (Hindi)": "Hindi", "मराठी (Marathi)": "Marathi",
    "தமிழ் (Tamil)": "Tamil", "বাংলা (Bengali)": "Bengali",
    "ગુજરાતી (Gujarati)": "Gujarati", "తెలుగు (Telugu)": "Telugu",
    "ಕನ್ನಡ (Kannada)": "Kannada",
}

# Source strings (keys are stable; values are English).
EN = {
    "tagline": "We don't track people or scan faces. We connect the two halves of every search.",
    "ui_lang": "Website language",
    "registry_live": "Registry (live DB)",
    "records": "De-identified records",
    "tab_file": "📝 File", "tab_registry": "📚 Registry", "tab_matches": "🔗 Matches",
    "tab_maps": "🗺️ Maps", "tab_validation": "✅ Validation", "tab_mesh": "📡 Mesh",
    "file_header": "Intake — staffed booth, voice-first, any language",
    "nothing_mandatory": "Nothing here is mandatory. Say or fill in whatever is known.",
    "what_happened": "What happened?",
    "lost": "🔍 Lost someone", "found": "🙋 Found someone",
    "reporter_lang": "Reporter's language",
    "voice_assistant": "🎙️ Voice assistant",
    "ask_in": "🔊 Ask the questions in",
    "record_answer": "🎙️ Record the reporter's answer (kept with the case)",
    "understand_fill": "🧠 Understand & auto-fill the form",
    "live_convo": "🎙️ Live conversation",
    "details_optional": "📝 Details (all optional)",
    "your_name": "Your name", "relation": "Relation to them", "their_name": "Their name",
    "gender": "Gender", "age": "Age band", "last_seen": "Last seen near (booth)",
    "height": "Height", "build": "Build", "complexion": "Complexion",
    "hair_length": "Hair length", "hair_color": "Hair colour",
    "wearing": "What are they wearing?", "marks": "Marks / aids",
    "anything_else": "Anything else", "contact": "Contact mobile (optional)",
    "file_report": "✓ File report (prints Case-ID slip)",
    "registry_header": "The shared registry — one pool, all centers",
    "matches_header": "Matches — top-3 with explainable confidence",
    "maps_header": "Nashik Kumbh — broadcast · where to search · where to place help",
    "validation_header": "THE NUMBER", "run_validation": "Run validation (offline)",
    "mesh_header": "Connectivity ladder — LAN → booth↔booth P2P → SMS",
}

HI = {
    "tagline": "हम लोगों को ट्रैक नहीं करते या चेहरे स्कैन नहीं करते। हम हर खोज के दो हिस्सों को जोड़ते हैं।",
    "ui_lang": "वेबसाइट की भाषा", "registry_live": "रजिस्ट्री (लाइव डीबी)",
    "records": "पहचान रहित रिकॉर्ड",
    "tab_file": "📝 दर्ज करें", "tab_registry": "📚 रजिस्ट्री", "tab_matches": "🔗 मिलान",
    "tab_maps": "🗺️ नक्शा", "tab_validation": "✅ सत्यापन", "tab_mesh": "📡 मेश",
    "file_header": "पंजीकरण — बूथ पर, आवाज़ से, किसी भी भाषा में",
    "nothing_mandatory": "यहाँ कुछ भी अनिवार्य नहीं है। जो पता हो वही बताएं या भरें।",
    "what_happened": "क्या हुआ?",
    "lost": "🔍 कोई खो गया", "found": "🙋 कोई मिला",
    "reporter_lang": "बताने वाले की भाषा",
    "voice_assistant": "🎙️ आवाज़ सहायक", "ask_in": "🔊 इस भाषा में सवाल पूछें",
    "record_answer": "🎙️ जवाब रिकॉर्ड करें (केस के साथ रखा जाएगा)",
    "understand_fill": "🧠 समझें और फॉर्म भरें",
    "live_convo": "🎙️ सीधी बातचीत",
    "details_optional": "📝 विवरण (सभी वैकल्पिक)",
    "your_name": "आपका नाम", "relation": "उनसे रिश्ता", "their_name": "उनका नाम",
    "gender": "लिंग", "age": "आयु वर्ग", "last_seen": "आख़िरी बार कहाँ देखा (बूथ)",
    "height": "कद", "build": "शरीर", "complexion": "रंग",
    "hair_length": "बालों की लंबाई", "hair_color": "बालों का रंग",
    "wearing": "उन्होंने क्या पहना है?", "marks": "निशान / सहारा",
    "anything_else": "और कुछ", "contact": "संपर्क मोबाइल (वैकल्पिक)",
    "file_report": "✓ रिपोर्ट दर्ज करें (केस-आईडी पर्ची)",
    "registry_header": "साझा रजिस्ट्री — एक पूल, सभी केंद्र",
    "matches_header": "मिलान — समझाने योग्य भरोसे के साथ शीर्ष-3",
    "maps_header": "नासिक कुंभ — प्रसारण · कहाँ खोजें · मदद कहाँ रखें",
    "validation_header": "वह आँकड़ा", "run_validation": "सत्यापन चलाएँ (ऑफ़लाइन)",
    "mesh_header": "कनेक्टिविटी सीढ़ी — LAN → बूथ P2P → SMS",
}

MR = {
    "tagline": "आम्ही लोकांचा माग काढत नाही किंवा चेहरे स्कॅन करत नाही। आम्ही प्रत्येक शोधाचे दोन भाग जोडतो।",
    "ui_lang": "वेबसाइट भाषा", "registry_live": "नोंदणी (लाइव्ह डीबी)",
    "records": "ओळख नसलेल्या नोंदी",
    "tab_file": "📝 नोंद", "tab_registry": "📚 नोंदणी", "tab_matches": "🔗 जुळणी",
    "tab_maps": "🗺️ नकाशा", "tab_validation": "✅ पडताळणी", "tab_mesh": "📡 मेश",
    "file_header": "नोंदणी — बूथवर, आवाजाने, कोणत्याही भाषेत",
    "nothing_mandatory": "इथे काहीही सक्तीचे नाही। माहित असेल तेच सांगा किंवा भरा।",
    "what_happened": "काय झाले?",
    "lost": "🔍 कोणी हरवले", "found": "🙋 कोणी सापडले",
    "reporter_lang": "सांगणाऱ्याची भाषा",
    "voice_assistant": "🎙️ आवाज सहाय्यक", "ask_in": "🔊 या भाषेत प्रश्न विचारा",
    "record_answer": "🎙️ उत्तर रेकॉर्ड करा (केससोबत ठेवले जाईल)",
    "understand_fill": "🧠 समजून घ्या आणि फॉर्म भरा",
    "live_convo": "🎙️ थेट संभाषण",
    "details_optional": "📝 तपशील (सर्व ऐच्छिक)",
    "your_name": "तुमचे नाव", "relation": "त्यांच्याशी नाते", "their_name": "त्यांचे नाव",
    "gender": "लिंग", "age": "वयोगट", "last_seen": "शेवटचे कुठे पाहिले (बूथ)",
    "height": "उंची", "build": "बांधा", "complexion": "वर्ण",
    "hair_length": "केसांची लांबी", "hair_color": "केसांचा रंग",
    "wearing": "त्यांनी काय घातले आहे?", "marks": "खुणा / आधार",
    "anything_else": "अजून काही", "contact": "संपर्क मोबाइल (ऐच्छिक)",
    "file_report": "✓ अहवाल नोंदवा (केस-आयडी पावती)",
    "registry_header": "सामायिक नोंदणी — एक पूल, सर्व केंद्रे",
    "matches_header": "जुळणी — स्पष्ट करता येणारी शीर्ष-3",
    "maps_header": "नाशिक कुंभ — प्रसारण · कुठे शोधावे · मदत कुठे ठेवावी",
    "validation_header": "तो आकडा", "run_validation": "पडताळणी चालवा (ऑफलाइन)",
    "mesh_header": "कनेक्टिव्हिटी शिडी — LAN → बूथ P2P → SMS",
}

_STATIC = {"English": EN, "Hindi": HI, "Marathi": MR}
_cache: dict[str, dict] = {}


def _claude_translate(target: str) -> dict | None:
    import json
    from drishti import llm
    if not llm.have_claude():
        return None
    prompt = ("Translate ONLY the values of this JSON into " + target +
              " (keep keys identical, keep any emoji, keep it short and natural for a "
              "missing-person help app). Return JSON only.\n" +
              json.dumps(EN, ensure_ascii=False))
    out = llm.complete_json(prompt, system="You localise UI strings for Indian languages.",
                            max_tokens=3000)
    return out if isinstance(out, dict) else None


def strings_for(display_name: str) -> dict:
    """Return the full string dict for a UI-language display name (EN-filled)."""
    lang = UI_LANGS.get(display_name, "English")
    if lang in _STATIC:
        return {**EN, **_STATIC[lang]}
    if lang in _cache:
        return _cache[lang]
    translated = _claude_translate(lang)
    merged = {**EN, **translated} if translated else EN
    _cache[lang] = merged
    return merged


def translator(display_name: str):
    """Return a t(key) function for the chosen UI language."""
    s = strings_for(display_name)
    return lambda key: s.get(key, EN.get(key, key))


if __name__ == "__main__":
    for name in ("English", "हिन्दी (Hindi)", "मराठी (Marathi)"):
        t = translator(name)
        print(f"{name:18} file={t('tab_file')}  ·  {t('file_report')}")
