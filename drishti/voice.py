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
# Speech -> text
# ---------------------------------------------------------------------------
def transcribe(audio_file, language_code: str | None = None) -> str | None:
    """Transcribe speech in its original language. `audio_file` is a file object
    or path. Returns transcript text, or None if Sarvam is unavailable."""
    client = _get_client()
    if client is None:
        return None
    try:
        fh = open(audio_file, "rb") if isinstance(audio_file, str) else audio_file
        resp = client.speech_to_text.transcribe(
            file=fh, model=ASR_MODEL, language_code=language_code or "unknown",
        )
        return getattr(resp, "transcript", None) or getattr(resp, "text", None)
    except Exception:
        return None


def transcribe_to_english(audio_file) -> str | None:
    """Auto-detect + transcribe + TRANSLATE to English in one call. This is the
    pivot-translate-at-ingest trick: store an English-normalised description so
    even the OFFLINE matcher compares across languages."""
    client = _get_client()
    if client is None:
        return None
    try:
        fh = open(audio_file, "rb") if isinstance(audio_file, str) else audio_file
        resp = client.speech_to_text.translate(file=fh, model=ASR_MODEL)
        return getattr(resp, "transcript", None) or getattr(resp, "text", None)
    except Exception:
        return None


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
_FIELDS = ["missing_person_name", "gender", "age_band", "state", "district",
           "language", "last_seen_location", "physical_description"]

_STRUCT_SYS = (
    "You structure a panicked, possibly code-mixed verbal missing-person report "
    "into fields for a reunification registry. The report may be in ANY Indian "
    "language (Tamil, Bhojpuri, Bengali, Maithili, ...) — UNDERSTAND it whatever "
    "the language. Detect the spoken language and put its English name in "
    "'language'. Use age bands exactly from: 0-12,13-17,18-40,41-60,61-70,71-80,80+. "
    "gender in Male/Female/Unknown. Leave a field empty if not stated — never "
    "invent. Write 'physical_description' in ENGLISH (concise, factual: clothing "
    "colour, build, marks, aids like stick/glasses) so it matches across languages."
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


if __name__ == "__main__":
    print(f"Sarvam available: {have_sarvam()}")
    print(f"Claude available: {llm.have_claude()}")
    txt, audio = containment_message("Hindi")
    print(f"containment (Hindi): {txt}")
    print(f"  audio: {'<base64 wav>' if audio else 'none (no key — UI shows text)'}")
    demo = structure_report("my father went missing near the banana board, he is old, "
                            "around seventy, wearing white kurta, hard of hearing")
    print(f"structured: {demo if demo else 'none (no ANTHROPIC_API_KEY — operator fills form)'}")
