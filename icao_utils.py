# icao_utils.py
import re
from icao_rules_en import ICAO_RULES_EN, NUMBER_WORDS_EN, words_to_number_en
from icao_rules_de import ICAO_RULES_DE, NUMBER_WORDS_DE, words_to_number_de

ICAO_TO_LETTER = {
    "alfa": "A", "bravo": "B", "charlie": "C", "delta": "D", "echo": "E",
    "foxtrot": "F", "golf": "G", "hotel": "H", "india": "I", "juliett": "J",
    "kilo": "K", "lima": "L", "mike": "M", "november": "N", "oscar": "O",
    "papa": "P", "quebec": "Q", "romeo": "R", "sierra": "S", "tango": "T",
    "uniform": "U", "victor": "V", "whiskey": "W", "x-ray": "X",
    "yankee": "Y", "zulu": "Z"
}

def normalize_text_to_callsign(text):
    words = text.lower().split()
    callsign_raw = ""
    for word in words:
        if word in ICAO_TO_LETTER:
            callsign_raw += ICAO_TO_LETTER[word]
        elif word in ["dash", "hyphen"]:
            callsign_raw += "-"
        elif len(word) == 1:
            callsign_raw += word.upper()
    return callsign_raw

def extract_context_from_transcript(transcript, language="en"):
    context = {}
    transcript_lc = transcript.lower()

    if language == "de":
        from icao_rules_de import words_to_number_de
        words_to_number = words_to_number_de
        runway_pattern = r"piste\s((?:\w+\s?){1,2})"
        squawk_pattern = r"squawk\s(\d{4})|code\s(\d{4})"
    else:
        from icao_rules_en import words_to_number_en
        words_to_number = words_to_number_en
        runway_pattern = r"runway\s((?:\w+\s?){1,2})"
        squawk_pattern = r"squawk\s(\d{4})"

    # Runway
    runway_match = re.search(runway_pattern, transcript_lc)
    if runway_match:
        runway_words = runway_match.group(1).strip().split()
        context["runway"] = words_to_number(runway_words)

    # Squawk
    squawk_match = re.search(squawk_pattern, transcript_lc)
    if squawk_match:
        context["squawk"] = squawk_match.group(1) or squawk_match.group(2)

    # Frequency
    freq_match = re.search(r"(\d{3}\.\d{1,3})", transcript)
    if freq_match:
        context["frequency"] = freq_match.group(1)

    return context

def detect_intent_by_rule(text, callsign, rules):
    norm_text = text.lower()
    for intent, rule in rules.items():
        for pattern in rule["patterns"]:
            if pattern in norm_text:
                return intent, rule["response"]
    return None, None

def generate_response(text, callsign, rules, context=None):
    if context is None:
        context = extract_context_from_transcript(text)
    intent, response_fn = detect_intent_by_rule(text, callsign, rules)
    if intent and response_fn:
        return response_fn(callsign, context)
    return None