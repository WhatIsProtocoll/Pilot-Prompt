# icao_utils.py
import re
from icao_rules_en import ICAO_RULES_EN, WORD_TO_NUMBER_EN
from icao_rules_de import ICAO_RULES_DE, WORD_TO_NUMBER_DE

ICAO_TO_LETTER = {
    "alfa": "A", "bravo": "B", "charlie": "C", "delta": "D", "echo": "E",
    "foxtrot": "F", "golf": "G", "hotel": "H", "india": "I", "juliett": "J",
    "kilo": "K", "lima": "L", "mike": "M", "november": "N", "oscar": "O",
    "papa": "P", "quebec": "Q", "romeo": "R", "sierra": "S", "tango": "T",
    "uniform": "U", "victor": "V", "whiskey": "W", "x-ray": "X",
    "yankee": "Y", "zulu": "Z"
}

REGISTRATION_PREFIXES = {"D","OE","HB", "G", "F", "I", "EC", "LX", "LN"}


def normalize_text_to_callsign(text):
    words = text.lower().split()
    letters = []

    for word in words:
        if word in ICAO_TO_LETTER:
            letters.append(ICAO_TO_LETTER[word])
        elif len(word) == 1:
            letters.append(word.upper())
        else:
            break  # Stop at first unrelated word

    raw_callsign = ''.join(letters)

    # Match known registration prefix
    for prefix in sorted(REGISTRATION_PREFIXES, key=len, reverse=True):
        if raw_callsign.startswith(prefix):
            return f"{prefix}-{raw_callsign[len(prefix):]}"

    return raw_callsign  # fallback without dash

def clean_transcript(transcript):
    # Fix common transcription issues
    transcript = transcript.lower()
    transcript = re.sub(r"\b[qQ]\s*(and|n)\s*[hH]\b", "QNH", transcript)
    transcript = re.sub(r"\bvee\s*eff\s*are\b", "VFR", transcript)
    transcript = re.sub(r"\beye\s*eff\s*are\b", "IFR", transcript)
    transcript = re.sub(r"\bsquak\b", "squawk", transcript)
    transcript = re.sub(r"transponder\s*code", "squawk", transcript)
    transcript = re.sub(r"\brun\s*way\b", "runway", transcript)
    transcript = re.sub(r"\bdecimal\b", ".", transcript)

    words = transcript.split()
    cleaned = []
    buffer = []

    def flush_number_buffer():
        if buffer:
            digits = [WORD_TO_NUMBER_EN.get(w, "") for w in buffer]
            if all(digits):
                cleaned.append("".join(digits))
                buffer.clear()
                return True
        return False

    def flush_phonetic_buffer():
        if buffer:
            letters = [ICAO_TO_LETTER.get(w, "") for w in buffer]
            if not all(letters):
                return False

            callsign_raw = "".join(letters)

            # ✅ Check for known registration prefix, regardless of length
            for prefix in sorted(REGISTRATION_PREFIXES, key=len, reverse=True):
                if callsign_raw.startswith(prefix):
                    cleaned.append(f"{prefix}-{callsign_raw[len(prefix):]}")
                    buffer.clear()
                    return True

            # Fallback: not a callsign → treat as taxiway or letters
            cleaned.extend(letters)
            buffer.clear()
            return True
        return False

    for word in words:
        if word in WORD_TO_NUMBER_EN:
            buffer.append(word)
        elif word in ICAO_TO_LETTER:
            buffer.append(word)
        else:
            # Flush buffer before unrelated word
            if not flush_number_buffer():
                flush_phonetic_buffer()
            cleaned.append(word.upper() if word in ["qnh", "vfr", "ifr", "squawk"] else word)

    flush_number_buffer()
    flush_phonetic_buffer()

    return " ".join(cleaned)

def extract_context_from_transcript(transcript, language="en"):
    context = {}
    transcript_lc = transcript.lower()

    # Load number conversion
    if language == "de":
        from icao_rules_de import words_to_number_de
        words_to_number = words_to_number_de
    else:
        from icao_rules_en import words_to_number_en
        words_to_number = words_to_number_en

    # --- Runway ---
    runway_matches = re.findall(r"runway\s+(\d{1,2})\b", transcript_lc)
    if runway_matches:
        context["runway"] = runway_matches[0].zfill(2)  # Ensure '08' not '8'

    # --- QNH ---
    qnh_match = re.search(r"qnh\s+(\d{3,4})\b", transcript_lc)
    if qnh_match:
        context["qnh"] = qnh_match.group(1)

    # --- Squawk ---
    squawk_match = re.search(r"(?:squawk|code|transpondercode)\s+(\d{4})", transcript_lc)
    if squawk_match:
        context["squawk"] = squawk_match.group(1)

    # --- Taxiways ---
    taxi_match = re.search(
        r"(?:via\s+taxiways?\s+)([a-z\s\-&]+?)(?=\s+(?:wind|qnh|short of runway|holding short|runway|\Z))",
        transcript_lc
    )
    if taxi_match:
        taxi_raw = taxi_match.group(1)
        taxiways = re.findall(r"\b[a-z]{1,2}\b", taxi_raw)  # Match A, B, NB, etc.
        if taxiways:
            context["taxiways"] = ", ".join(tw.upper() for tw in taxiways)

    # --- Hold short ---
    hold_match = re.search(r"hold(?:ing)? short of runway\s+(\d{2})", transcript_lc)
    if hold_match:
        context["hold_short_runway"] = hold_match.group(1)

    # --- Frequency ---
    freq_match = re.search(r"\b(\d{3}\.\d{1,3})\b", transcript)
    if freq_match:
        context["frequency"] = freq_match.group(1)

    return context

def callsign_matches(full, heard):
    def strip(c): return c.replace("-", "").upper()
    full_clean = strip(full)
    heard_clean = strip(heard)

    if heard_clean == full_clean:
        return True
    elif heard_clean.startswith(full_clean[0]) and full_clean.endswith(heard_clean[1:]):
        return True  # matches like D-BG → D-EIBG
    return False

def strip_callsign_from_transcript(transcript, callsign, phonetic_map):
    words = transcript.lower().split()
    letters = []

    for word in words:
        if word in phonetic_map:
            letters.append(phonetic_map[word])
        else:
            break

    detected = "".join(letters)
    formatted_detected = None

    # Match known registration prefix
    for prefix in sorted(REGISTRATION_PREFIXES, key=len, reverse=True):
        if detected.startswith(prefix):
            formatted_detected = f"{prefix}-{detected[len(prefix):]}"
            break

    if not formatted_detected:
        formatted_detected = detected  # fallback

    cleaned_text = " ".join(words[len(letters):]).strip()
    return cleaned_text

def get_icao_response(transcript, callsign, context={}, language="en"):
    rules = ICAO_RULES_EN if language == "en" else ICAO_RULES_DE

    for intent, rule in rules.items():
        for pattern in rule["patterns"]:
            if pattern.lower() in transcript.lower():
                try:
                    response = rule["response"](callsign.upper(), ctx=context)
                    return response, intent
                except TypeError as e:
                    print("Missing context for rule:", e)
                    cleaned = strip_callsign_from_transcript(transcript, callsign, ICAO_TO_LETTER)
                    return f"{cleaned} — {callsign.upper()}", None

    cleaned = strip_callsign_from_transcript(transcript, callsign, ICAO_TO_LETTER)
    return f"{cleaned} — {callsign.upper()}", None
