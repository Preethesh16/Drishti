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
    """Translate text. Falls back to returning the input unchanged with no key."""
    client = _get_client()
    if client is None or not text:
        return text
    try:
        resp = client.text.translate(
            input=text, source_language_code=source_code,
            target_language_code=target_code, model=TRANSLATE_MODEL,
        )
        return getattr(resp, "translated_text", None) or text
    except Exception:
        return text


# ---------------------------------------------------------------------------
# Text -> speech (containment message)
# ---------------------------------------------------------------------------
def speak(text: str, language_code: str = "hi-IN", speaker: str = "Meera") -> str | None:
    """Return base64 WAV of `text` spoken in `language_code`, or None offline."""
    client = _get_client()
    if client is None:
        return None
    try:
        resp = client.text_to_speech.convert(
            text=text, target_language_code=language_code,
            speaker=speaker, model=TTS_MODEL,
        )
        audios = getattr(resp, "audios", None)
        return audios[0] if audios else getattr(resp, "audio", None)
    except Exception:
        return None


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
    "into fields for a reunification registry. Use age bands exactly from: "
    "0-12,13-17,18-40,41-60,61-70,71-80,80+. gender in Male/Female/Unknown. "
    "Leave a field empty if not stated — never invent. Keep physical_description "
    "concise and factual (clothing colour, build, marks, aids like stick/glasses)."
)


def structure_report(transcript: str) -> dict | None:
    """Claude turns a free-text transcript into the registry fields. Returns a
    dict (subset of the 16 columns) or None if Claude is unavailable."""
    if not transcript:
        return None
    user = (
        f"Transcript:\n\"\"\"{transcript}\"\"\"\n\n"
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
