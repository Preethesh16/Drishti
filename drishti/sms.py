"""SMS bridge (SIMULATED) — the bottom of the connectivity ladder.

When there is no LAN and no booth-to-booth peer, a booth can still get a report
in/out over a single SMS. Inbound is a compact pipe-delimited line a low-end
phone or field radio can send; outbound is the family/booth notification. No paid
gateway — this formats/parses the messages; a real deploy swaps in a gateway.

Inbound format:  TYPE|GENDER|AGE|STATE|LOCATION
  e.g.  MISSING|F|65|Bihar|SectorB   ·   FOUND|M|8|UP|West Hall

Run:  python -m drishti.sms
"""
from __future__ import annotations

_GENDER = {"M": "Male", "F": "Female", "U": "Unknown"}


def parse_inbound(line: str) -> dict | None:
    """Parse 'TYPE|GENDER|AGE|STATE|LOCATION' → partial report dict, or None."""
    parts = [p.strip() for p in (line or "").split("|")]
    if len(parts) < 5:
        return None
    rtype, gender, age, state, location = parts[:5]
    band = None
    if age.isdigit():
        a = int(age)
        bands = [(12, "0-12"), (17, "13-17"), (40, "18-40"), (60, "41-60"),
                 (70, "61-70"), (80, "71-80"), (200, "80+")]
        band = next(b for hi, b in bands if a <= hi)
    return {
        "report_type": "found" if rtype.strip().lower().startswith("found") else "missing",
        "gender": _GENDER.get(gender.strip().upper(), "Unknown"),
        "age_band": band or "",
        "state": state,
        "last_seen_location": location,
    }


def format_match_alert(case_id: str, match_case: str, booth: str, score: float) -> str:
    """Outbound SMS to a booth/volunteer when a strong match appears."""
    return (f"DRISHTI: possible match for {case_id} <-> {match_case} "
            f"(score {score:.0f}). Check {booth}. Reply Y to confirm. Helpline 112.")


def format_reunion(case_id: str, contact: str | None) -> str:
    """Outbound SMS to the family once a reunion is human-confirmed."""
    who = f" Call {contact}." if contact else ""
    return f"DRISHTI: {case_id} REUNITED. Please come to the nearest help booth.{who}"


def format_broadcast(origin: str, n_booths: int) -> str:
    """Outbound emergency signal summarising the proximity broadcast."""
    return (f"DRISHTI ALERT: new report near {origin}. {n_booths} nearby booths "
            f"notified — watch for a drifting lost person. Reply FOUND|G|age|state|loc.")


if __name__ == "__main__":
    for line in ("MISSING|F|65|Bihar|SectorB", "FOUND|M|8|UP|West Hall", "garbage"):
        print(f"{line!r:32} -> {parse_inbound(line)}")
    print(format_match_alert("KMP-2027-0A1B", "KS00463", "Ramkund Booth", 82))
    print(format_reunion("KMP-2027-0A1B", "98765 06506"))
    print(format_broadcast("Ramkund Ghat", 11))
