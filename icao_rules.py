# icao_rules.py
import re

NUMBER_WORDS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9"
}

ICAO_TO_LETTER = {
    "alfa": "A", "bravo": "B", "charlie": "C", "delta": "D", "echo": "E",
    "foxtrot": "F", "golf": "G", "hotel": "H", "india": "I", "juliett": "J",
    "kilo": "K", "lima": "L", "mike": "M", "november": "N", "oscar": "O",
    "papa": "P", "quebec": "Q", "romeo": "R", "sierra": "S", "tango": "T",
    "uniform": "U", "victor": "V", "whiskey": "W", "x-ray": "X",
    "yankee": "Y", "zulu": "Z"
}

ICAO_RULES = {
    "clearance_request": {
        "patterns": [
            "request clearance",
            "standby for clearance",
            "request IFR clearance"
        ],
        "response": lambda cs, ctx={}: f"{cs}, cleared to {ctx.get('destination', 'destination')} via {ctx.get('sid', 'SID')}, squawk {ctx.get('squawk', 'XXXX')}"
    },
    "startup_request": {
        "patterns": [
            "request startup",
            "startup approved"
        ],
        "response": lambda cs, ctx={}: f"{cs}, startup approved, contact ground on {ctx.get('frequency', '121.9')}"
    },
    "taxi_clearance": {
        "patterns": [
            "request taxi",
            "taxi to holding point",
            "taxi to runway"
        ],
        "response": lambda cs, ctx={}: f"{cs}, taxi to holding point {ctx.get('point', 'C')}, runway {ctx.get('runway', '27')}"
    },
    "takeoff_clearance": {
        "patterns": [
            "cleared for takeoff",
            "line up and wait"
        ],
        "response": lambda cs, ctx={}: f"{cs}, cleared for takeoff runway {ctx.get('runway', '27')}"
    },
    "landing_clearance": {
        "patterns": [
            "cleared to land",
            "continue approach",
            "final runway"
        ],
        "response": lambda cs, ctx={}: f"{cs}, roger, cleared to land runway {ctx.get('runway', '27')}"
    },
    "frequency_change": {
        "patterns": [
            "contact tower",
            "switch to",
            "change frequency"
        ],
        "response": lambda cs, ctx={}: f"{cs}, switching to {ctx.get('frequency', '118.5')}, goodbye"
    },
    "squawk_assignment": {
        "patterns": [
            "squawk",
            "squawk code",
            "set transponder"
        ],
        "response": lambda cs, ctx={}: f"{cs}, squawk {ctx.get('squawk', '7000')}"
    },
    "go_around": {
        "patterns": [
            "go around",
            "going around"
        ],
        "response": lambda cs, ctx={}: f"{cs}, roger, go around, report downwind"
    }
}

def words_to_number(words):
    return ''.join(NUMBER_WORDS.get(w, w) for w in words)

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

def extract_context_from_transcript(transcript):
    context = {}

    # Runway detection: e.g. "runway two nine"
    runway_match = re.search(r"runway\s((?:\w+\s?){1,2})", transcript.lower())
    if runway_match:
        runway_words = runway_match.group(1).strip().split()
        context["runway"] = words_to_number(runway_words)

    # Squawk detection: e.g. "squawk 7000"
    squawk_match = re.search(r"squawk\s(\d{4})", transcript.lower())
    if squawk_match:
        context["squawk"] = squawk_match.group(1)

    # Frequency: e.g. "contact tower on one one eight decimal five"
    freq_match = re.search(r"(\d{3}\.\d{1,3})", transcript)
    if freq_match:
        context["frequency"] = freq_match.group(1)

    return context

def detect_intent_by_rule(text, callsign):
    norm_text = text.lower()
    for intent, rule in ICAO_RULES.items():
        for pattern in rule["patterns"]:
            if pattern in norm_text:
                return intent, rule["response"]
    return None, None

def generate_response(text, callsign, context=None):
    if context is None:
        context = extract_context_from_transcript(text)
    intent, response_fn = detect_intent_by_rule(text, callsign)
    if intent and response_fn:
        return response_fn(callsign, context)
    return None