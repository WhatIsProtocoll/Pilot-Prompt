# icao_rules.py
import re

ICAO_RULES_EN = {
    "ramp_call_request": {
        "patterns": [
            "request departure information"
        ],
        "response": lambda cs, ramp, ctx={}: f"{ramp} – {cs}"
    },

    "ramp_checkin": {
        "patterns": [
            "request taxi information"
        ],
        "response": lambda cs, airplane_type, num_pax, dep, arr, position, ctx={}: f"{cs}, {airplane_type}, {num_pax} persons, VFR flight from {dep} to {arr}, at {position}, request taxi information"
    },

    "taxi_clearance": {
    "patterns": [
        "taxi to holding point", "QNH", "runway", "in use", "via"
    ],
    "response": lambda cs, ctx={}: (
        f"Taxi to holding point runway {ctx.get('runway', '08')} "
        f"via taxiways {ctx.get('taxiways', 'Alpha')} "
        f"QNH {ctx.get('qnh', '1013')}, "
        f"holding short of runway {ctx.get('hold_short_runway', ctx.get('runway', '08'))} — {cs}"
    )
    },

    "tower_checkin": {
        "patterns": [
            "request departure information"
        ],
        "response": lambda cs, twr, ctx={}: f"{twr} – {cs}"
    },

    "ready_for_departure": {
        "patterns": [
            "radio", "information"
        ],
        "response": lambda cs, ctx={}: f"{cs}, ready for departure at holding point runway 22, for departure via Kilo"
    },

    "takeoff_clearance": {
        "patterns": [
            "cleared for takeoff", "takeoff clearance", "runway clear for takeoff"
        ],
        "response": lambda cs, ctx={}: f"Runway 22, cleared for takeoff — {cs}"
    },

    "tower_checkout": {
        "patterns": [
            "request departure information"
        ],
        "response": lambda cs, ctx={}: f"{cs}, end of Kilo route. Request frequency change to report to FIS."
    },

    "squawk_info": {
        "patterns": [
            "squawk 7000", "transponder code 7000", "transponder code seven zero zero zero"
        ],
        "response": lambda cs, ctx={}: f"Squawk 7000 — {cs}"
    },

    "fis_checkin": {
        "patterns": [
            "request departure information"
        ],
        "response": lambda cs, fis, ctx={}: f"{fis} – {cs}"
    },

    "fis_enroute_report": {
        "patterns": [
            "request taxi information"
        ],
        "response": lambda cs, airplane_type, num_pax, dep, arr, ctx={}: f"{cs}, {airplane_type}, {num_pax} persons, VFR flight from {dep} to {arr}, just left Kilo route at 2000 feet, request traffic information"
    },

    "traffic_info": {
        "patterns": [
            "identified", "squawk", "transponder", "QNH"
        ],
        "response": lambda cs, ctx={}: f"QNH 1013, squawk 7000 — {cs}"
    },

    "frequency_change": {
        "patterns": [
            "contact", "switch to", "change frequency"
        ],
        "response": lambda cs, fis2, ctx={}: f"Switching to {fis2} — {cs}"
    },

    "fis_checkout": {
        "patterns": [
            "leaving", "changing frequency"
        ],
        "response": lambda cs, arr, ctx={}: f"{cs}, request frequency change to report in {arr}"
    },

    "arrival_info_checkin": {
        "patterns": [
            "request departure information"
        ],
        "response": lambda cs, arr_info, ctx={}: f"{arr_info} – {cs}"
    },

    "arrival_report": {
        "patterns": [
            "information", "radio"
        ],
        "response": lambda cs, airplane_type, num_pax, dep, arr, ctx={}: f"{cs}, {airplane_type}, {num_pax} persons, VFR flight from {dep} to {arr}, 5 miles south of the airfield at 3000 feet, for landing via Yankee"
    },

    "approach_clearance": {
        "patterns": [
            "identified", "approach", "squawk"
        ],
        "response": lambda cs, squawk, ctx={}: f"Squawk {squawk} — {cs}"
    },

    "report_point": {
        "patterns": [
            "altitude", "feet", "set code"
        ],
        "response": lambda cs, ctx={}: f"{cs}, over Yankee at 2000 feet, reporting base leg"
    },

    "go_around": {
        "patterns": [
            "go around", "going around", "abort landing"
        ],
        "response": lambda cs, ctx={}: f"{cs} — going around"
    },

    "arrival_apron_checkin": {
        "patterns": [
            "vacated runway", "clear of runway", "on apron"
        ],
        "response": lambda cs, arr_apron, ctx={}: f"{arr_apron} – {cs}"
    },
    
    "taxi_to_parking": {
    "patterns": [
        "taxi to general aviation", "taxi to parking", "taxi to stand"
    ],
    "response": lambda cs, ctx={}: f"Taxiing to general aviation parking, {cs}"
    }
}

PHASE_MAPPING = {
    "ramp_call_request": "Pre-Start / Taxi",
    "ramp_checkin": "Pre-Start / Taxi",
    "taxi_clearance": "Pre-Start / Taxi",

    "tower_checkin": "Departure / Takeoff",
    "ready_for_departure": "Departure / Takeoff",
    "takeoff_clearance": "Departure / Takeoff",
    "tower_checkout": "Departure / Takeoff",
    "squawk_info": "Departure / Takeoff",

    "fis_checkin": "Enroute / Cruise",
    "fis_enroute_report": "Enroute / Cruise",
    "traffic_info": "Enroute / Cruise",
    "fis_checkout": "Enroute / Cruise",
    "frequency_change": "Enroute / Cruise",

    "arrival_info_checkin": "Arrival / Traffic Circuit",
    "arrival_report": "Arrival / Traffic Circuit",
    "approach_clearance": "Arrival / Traffic Circuit",
    "report_point": "Arrival / Traffic Circuit",
    "go_around": "Arrival / Traffic Circuit",

    "arrival_apron_checkin": "After Landing / Apron",
    "taxi_to_parking": "After Landing / Apron"

}

PHASE_ORDER = [
    "Pre-Start / Taxi",
    "Departure / Takeoff",
    "Enroute / Cruise",
    "Arrival / Traffic Circuit",
    "After Landing / Apron"
]

def words_to_number_en(words):
    return ''.join(WORD_TO_NUMBER_EN.get(w, w) for w in words)

WORD_TO_NUMBER_EN = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9"
}