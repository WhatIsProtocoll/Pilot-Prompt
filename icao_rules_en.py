# icao_rules.py
import re

ICAO_RULES_EN = {
    "clearance_request": {
        "patterns": [
            "cleared to"
        ],
        "response": lambda cs, ctx={}: f"Cleared to {ctx.get('destination', 'destination')} via {ctx.get('sid', 'SID')}, squawk {ctx.get('squawk', 'XXXX'), {cs}}"
    },
    "startup_request": {
        "patterns": [
            "startup approved"
        ],
        "response": lambda cs, ctx={}: f"Startup approved, contact ground on {ctx.get('frequency', '121.9'), {cs}}"
    },
    "taxi_clearance": {
        "patterns": [
            "taxi to holding point",
            "taxi to runway"
        ],
        "response": lambda cs, ctx={}: f"Taxi to holding point {ctx.get('point', 'C')}, runway {ctx.get('runway', '27'), {cs}}"
    },
    "tower_frequency": {
        "patterns": [
            "contact tower",
        ],
        "response": lambda cs, ctx={}: f"Contact Tower on {ctx.get('frequency', '121.9'), {cs}}"
    },
    "takeoff_clearance": {
        "patterns": [
            "cleared for takeoff",
            "line up and wait"
        ],
        "response": lambda cs, ctx={}: f"Cleared for takeoff runway {ctx.get('runway', '27'), {cs}}"
    },
    "landing_clearance": {
        "patterns": [
            "cleared to land",
            "continue approach",
            "final runway"
        ],
        "response": lambda cs, ctx={}: f"Roger, cleared to land runway {ctx.get('runway', '27'), {cs}}"
    },
    "frequency_change": {
        "patterns": [
            "contact tower",
            "switch to",
            "change frequency"
        ],
        "response": lambda cs, ctx={}: f"Switching to {ctx.get('frequency', '118.5')}, goodbye, {cs}"
    },
    "squawk_assignment": {
        "patterns": [
            "squawk",
            "squawk code",
            "set transponder"
        ],
        "response": lambda cs, ctx={}: f"Squawk {ctx.get('squawk', '7000'), {cs}}"
    },
    "go_around": {
        "patterns": [
            "go around",
            "going around"
        ],
        "response": lambda cs, ctx={}: f"Roger, go around, report downwind, {cs}"
    }
}

def words_to_number_en(words):
    return ''.join(NUMBER_WORDS_EN.get(w, w) for w in words)

NUMBER_WORDS_EN = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9"
}