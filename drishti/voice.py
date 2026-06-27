"""Voice I/O via Sarvam AI — ASR, TTS, translate for 22 Indian languages.

Role (per architecture): voice = I/O, Claude = brain. The operator speaks the
family's report in any Indian language; Sarvam transcribes + translates to a
common pivot language; Claude structures it into the 16 fields. On a FOUND log,
Bulbul TTS speaks a containment message to the lost person in THEIR language.

Everything degrades cleanly with no SARVAM_API_KEY:
  - transcribe/translate -> return None / pass text through unchanged
  - speak -> return None (UI shows the text instead)
So the demo runs offline; voice is additive sparkle, never the foundation.

SDK: pip install sarvamai   (https://docs.sarvam.ai)
"""
from __future__ import annotations

from drishti import config as C
from drishti import llm

_client = None

# Models (current Sarvam line). Override here if Sarvam ships new versions.
ASR_MODEL = "saarika:v2"
TTS_MODEL = "bulbul:v1"
TRANSLATE_MODEL = "mayura:v1"


def have_sarvam() -> bool:
    return bool(C.SARVAM_API_KEY) and _get_client() is not None


def _get_client():
    global _client
    if _client is not None:
        return _client
    if not C.SARVAM_API_KEY:
        return None
    try:
        from sarvamai import SarvamAI
        _client = SarvamAI(api_subscription_key=C.SARVAM_API_KEY)
    except Exception:
        _client = None
    return _client


def lang_code(language_name: str) -> str:
    """Dataset language name -> Sarvam code (defaults to Hindi)."""
    return C.SARVAM_LANG_CODES.get((language_name or "").strip(), "hi-IN")


# ---------------------------------------------------------------------------
# Speech -> text   (Sarvam → free local Whisper → None)
# ---------------------------------------------------------------------------
# faster-whisper: free, local, no API key. "base" balances CPU speed vs Indian-
# language accuracy; it auto-downloads (~145MB) on first use and is then cached.
WHISPER_MODEL_SIZE = "base"
_whisper_model = None


def _get_whisper():
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model
    try:
        from faster_whisper import WhisperModel
        _whisper_model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
    except Exception:
        _whisper_model = None
    return _whisper_model


def have_asr() -> bool:
    """True if ANY speech-to-text path is available (Sarvam key or local Whisper)."""
    return have_sarvam() or _get_whisper() is not None


def _to_temp_wav(audio) -> tuple[str, bool]:
    """Materialise a path from a path / bytes / file-like. Returns (path, is_temp)."""
    import os
    import tempfile
    if isinstance(audio, str):
        return audio, False
    data = audio.read() if hasattr(audio, "read") else audio
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    with open(path, "wb") as fh:
        fh.write(data)
    return path, True


def transcribe_local(audio, translate: bool = True) -> str | None:
    """Free local Whisper. translate=True → output English. Returns text or None."""
    model = _get_whisper()
    if model is None:
        return None
    import os
    path, is_temp = _to_temp_wav(audio)
    try:
        segs, _info = model.transcribe(path, task="translate" if translate else "transcribe")
        text = " ".join(s.text for s in segs).strip()
        return text or None
    except Exception:
        return None
    finally:
        if is_temp:
            try:
                os.remove(path)
            except OSError:
                pass


def transcribe(audio_file, language_code: str | None = None) -> str | None:
    """Transcribe speech in its original language. Sarvam → local Whisper → None."""
    client = _get_client()
    if client is not None:
        try:
            path, is_temp = _to_temp_wav(audio_file)
            with open(path, "rb") as fh:
                resp = client.speech_to_text.transcribe(
                    file=fh, model=ASR_MODEL, language_code=language_code or "unknown")
            out = getattr(resp, "transcript", None) or getattr(resp, "text", None)
            if out:
                return out
        except Exception:
            pass
    return transcribe_local(audio_file, translate=False)


def transcribe_to_english(audio_file) -> str | None:
    """Auto-detect + transcribe + TRANSLATE to English. Sarvam → local Whisper → None.
    Pivot-translate at ingest so even the OFFLINE matcher is cross-lingual."""
    client = _get_client()
    if client is not None:
        try:
            path, is_temp = _to_temp_wav(audio_file)
            with open(path, "rb") as fh:
                resp = client.speech_to_text.translate(file=fh, model=ASR_MODEL)
            out = getattr(resp, "transcript", None) or getattr(resp, "text", None)
            if out:
                return out
        except Exception:
            pass
    return transcribe_local(audio_file, translate=True)


# ---------------------------------------------------------------------------
# Text translate (pivot descriptions to a common language)
# ---------------------------------------------------------------------------
def translate(text: str, target_code: str = C.PIVOT_LANG,
              source_code: str = "auto") -> str:
    """Translate text. Sarvam (Mayura) → Claude fallback → input unchanged.
    So a Tamil/Bhojpuri complaint becomes usable English even without Sarvam."""
    if not text:
        return text
    client = _get_client()
    if client is not None:
        try:
            resp = client.text.translate(
                input=text, source_language_code=source_code,
                target_language_code=target_code, model=TRANSLATE_MODEL,
            )
            out = getattr(resp, "translated_text", None)
            if out:
                return out
        except Exception:
            pass
    # Claude fallback (multilingual) — no Sarvam key needed
    if llm.have_claude():
        lang = "English" if target_code.startswith("en") else target_code
        out = llm.complete(
            f"Translate to {lang}. Output ONLY the translation:\n\n{text}",
            system="You are a precise translator for Indian languages.", max_tokens=400)
        if out:
            return out.strip()
    return text


# ---------------------------------------------------------------------------
# Text -> speech (containment message)
# ---------------------------------------------------------------------------
# Microsoft (edge-tts) neural voices per language — FREE, no API key. Fallback
# for TTS when Sarvam/Bulbul isn't configured.
EDGE_VOICES = {
    "hi-IN": "hi-IN-SwaraNeural", "ta-IN": "ta-IN-PallaviNeural",
    "bn-IN": "bn-IN-TanishaaNeural", "te-IN": "te-IN-ShrutiNeural",
    "kn-IN": "kn-IN-SapnaNeural", "gu-IN": "gu-IN-DhwaniNeural",
    "mr-IN": "mr-IN-AarohiNeural", "ml-IN": "ml-IN-SobhanaNeural",
    "pa-IN": "pa-IN-OjasNeural", "ur-IN": "ur-IN-GulNeural",
    "en-IN": "en-IN-NeerjaNeural",
}


def _edge_tts(text: str, language_code: str) -> str | None:
    """Microsoft Edge neural TTS (free) → base64 MP3, or None if unavailable."""
    try:
        import asyncio, base64, os, tempfile
        import edge_tts
    except Exception:
        return None
    voice = EDGE_VOICES.get(language_code, EDGE_VOICES["en-IN"])
    fd, path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    try:
        asyncio.run(edge_tts.Communicate(text, voice).save(path))
        with open(path, "rb") as fh:
            return base64.b64encode(fh.read()).decode()
    except Exception:
        return None
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def speak(text: str, language_code: str = "hi-IN", speaker: str = "Meera") -> str | None:
    """Speak `text` in `language_code` → base64 audio. Sarvam (Bulbul) first, then
    Microsoft edge-tts (free) fallback, else None. The demo always has a voice."""
    client = _get_client()
    if client is not None:
        try:
            resp = client.text_to_speech.convert(
                text=text, target_language_code=language_code,
                speaker=speaker, model=TTS_MODEL,
            )
            audios = getattr(resp, "audios", None)
            out = audios[0] if audios else getattr(resp, "audio", None)
            if out:
                return out
        except Exception:
            pass
    return _edge_tts(text, language_code)


# Containment message text per language. Stopping drift is half the solve.
_CONTAINMENT = {
    "hi-IN": "कृपया यहीं रुकें। आपके परिवार से संपर्क किया जा रहा है। आप सुरक्षित हैं।",
    "bn-IN": "অনুগ্রহ করে এখানেই থাকুন। আপনার পরিবারের সাথে যোগাযোগ করা হচ্ছে। আপনি নিরাপদ।",
    "en-IN": "Please stay here. Your family is being contacted. You are safe.",
}


def containment_message(language_name: str) -> tuple[str, str | None]:
    """Return (text, base64_audio_or_None) telling the found person to stay put,
    in their language. Used by the FOUND flow."""
    code = lang_code(language_name)
    text = _CONTAINMENT.get(code) or translate(_CONTAINMENT["en-IN"], target_code=code)
    return text, speak(text, language_code=code)


# ---------------------------------------------------------------------------
# Speech transcript -> structured 16 fields (Claude is the brain)
# ---------------------------------------------------------------------------
_FIELDS = ["missing_person_name", "reporter_name", "relation", "gender", "age_band",
           "height", "build", "hair_length", "hair_color", "complexion",
           "clothing", "marks", "language", "last_seen_location", "physical_description"]

_STRUCT_SYS = (
    "You structure a panicked, possibly code-mixed verbal missing-person report "
    "into fields for a reunification registry. The report may be in ANY Indian "
    "language (Tamil, Bhojpuri, Bengali, Maithili, ...) — UNDERSTAND it whatever the "
    "language. Detect the spoken language → its English name in 'language'. "
    "NOTHING is mandatory: leave any field as \"\" if not stated — NEVER invent. "
    "Allowed values: gender ∈ Male/Female/Unknown; age_band ∈ "
    "0-12,13-17,18-40,41-60,61-70,71-80,80+; height ∈ Tall/Average/Short; "
    "build ∈ Thin/Average/Heavy; hair_length ∈ Long/Short/Bald; "
    "complexion ∈ Fair/Medium/Dark. 'reporter_name' = who is reporting; "
    "'relation' = their relation to the missing person (son, wife, ...); "
    "'missing_person_name' = the lost person; 'clothing' = what they are wearing; "
    "'marks' = scars/moles/aids (stick, glasses, hearing). Write "
    "'physical_description' as a concise ENGLISH summary of the visual attributes "
    "(height, build, hair, complexion, clothing, marks) so it matches across languages."
)


def assistant_prompt() -> str:
    """The question the voice assistant asks the reporter (spoken in their language)."""
    return (
        "Namaste. I am here to help you find them. Please tell me whatever you know — "
        "nothing is compulsory. Your name and your relation to them. The missing "
        "person's name, their age and whether they are male or female. Are they tall, "
        "average, or short; thin or heavy; long or short hair and its colour; their "
        "skin tone. What clothes are they wearing, and any marks, scars, glasses, or a "
        "walking stick. And the nearest booth or landmark where you last saw them."
    )


def structure_report(transcript: str) -> dict | None:
    """Claude reads a free-text report in ANY language, translates/understands it,
    and returns the registry fields (description normalised to English). Returns a
    dict (subset of the 16 columns) or None if Claude is unavailable.

    This is the heart of the voice assistant: a Tamil complaint in → structured,
    English-normalised missing-person details out, ready for the matcher."""
    if not transcript:
        return None
    user = (
        f"Verbal report (any Indian language):\n\"\"\"{transcript}\"\"\"\n\n"
        f"Return JSON with keys: {_FIELDS}."
    )
    return llm.complete_json(user, system=_STRUCT_SYS)


def _heuristic_fields(text: str) -> dict:
    """No-Claude fallback: pull a few obvious fields from English text so the
    voice demo still autofills something useful without an Anthropic key."""
    import re
    t = (text or "").lower()
    out = {"physical_description": (text or "").strip()}
    fem = re.search(r"\b(woman|women|mother|wife|girl|daughter|sister|lady|aunt|"
                    r"grandmother|she|her)\b", t)
    male = re.search(r"\b(man|men|father|husband|boy|son|brother|uncle|"
                     r"grandfather|he|his)\b", t)
    if male and not fem:
        out["gender"] = "Male"
    elif fem and not male:
        out["gender"] = "Female"
    m = re.search(r"\b(\d{1,3})\s*(years|year|yr|saal)?\b", t)
    if m:
        age = int(m.group(1))
        bands = [(12, "0-12"), (17, "13-17"), (40, "18-40"), (60, "41-60"),
                 (70, "61-70"), (80, "71-80"), (200, "80+")]
        out["age_band"] = next(b for hi, b in bands if age <= hi)
    return out


def voice_to_fields(audio) -> dict:
    """THE voice-assistant entrypoint for the website: speech (any language) →
    English transcript → structured missing-person fields. `audio` is bytes /
    path / file-like (e.g. Streamlit st.audio_input). Always returns a dict:
        {transcript, fields, asr, structured}
    degrading gracefully (Sarvam → Whisper for ASR; Claude → heuristic for fields)."""
    transcript = transcribe_to_english(audio)
    if not transcript:
        return {"transcript": None, "fields": {}, "asr": False, "structured": False}
    fields = structure_report(transcript)
    if fields:
        return {"transcript": transcript, "fields": fields, "asr": True, "structured": True}
    return {"transcript": transcript, "fields": _heuristic_fields(transcript),
            "asr": True, "structured": False}


if __name__ == "__main__":
    print(f"Sarvam available: {have_sarvam()}")
    print(f"Claude available: {llm.have_claude()}")
    txt, audio = containment_message("Hindi")
    print(f"containment (Hindi): {txt}")
    print(f"  audio: {'<base64 wav>' if audio else 'none (no key — UI shows text)'}")
    demo = structure_report("my father went missing near the banana board, he is old, "
                            "around seventy, wearing white kurta, hard of hearing")
    print(f"structured: {demo if demo else 'none (no ANTHROPIC_API_KEY — operator fills form)'}")
