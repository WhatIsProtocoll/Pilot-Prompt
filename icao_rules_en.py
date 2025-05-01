# icao_rules.py
import re

ICAO_RULES_EN = {
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

def words_to_number_en(words):
    return ''.join(NUMBER_WORDS_EN.get(w, w) for w in words)

NUMBER_WORDS_EN = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9"
}