# icao_rules_de.py

ICAO_RULES_DE = {
    "einladung_vorfeld": {
        "patterns": [
            "erbitte abfluginformationen"],
        "response": lambda cs, vorfeld, ctx={}: f"{vorfeld} – {cs}"
    },
    
    "anmeldung_vorfeld": {
        "patterns": [
            "erbitte rollinformationen"],
        "response": lambda cs, airplane_type, num_pax, dep, arr, position, ctx={}: f"{cs}, {airplane_type}, {num_pax} Personen, VFR-Flug von {dep} nach {arr}, an {position}, erbitte Rollinformationen"
    },

    "rollfreigabe": {
        "patterns": [
            "rollen sie", "QNH", "Piste", "in Benutzung"],
        "response": lambda cs, Piste, QNH, ctx={}: f"Rolle zum Rollhalt der Piste {Piste}, QNH {QNH} — {cs}"
    },

    "einladung_twr": {
        "patterns": [
            "erbitte abfluginformationen"],
        "response": lambda cs, twr, ctx={}: f"{twr} – {cs}"
    },

    "abflugbereit": {
        "patterns": [
            "Radio", "Info"],
        "response": lambda cs, Piste, report, ctx={}: f" {cs}, abflugbereit am Rollhalt der Piste {Piste}, zum Abflug über {report} "
    },

    "startfreigabe": {
        "patterns": [
            "start frei", "freigabe zum start", "piste frei zum start"],
        "response": lambda cs, Piste, ctx={}: f"Piste {Piste} Start frei — {cs}"
    },

    "abmeldung_twr": {
        "patterns": [
            "erbitte abfluginformationen"],
        "response": lambda cs, report, ctx={}: f"{cs} am Ende der {report} Strecke. Erbitte Verlassen der Frequenz zum Melden bei FIS."
    },

    "squawk_info": {
        "patterns": [
            "Squawk 7000", "Transpondercode 7000", "Transpondercode 7 0 0 0"],
        "response": lambda cs, squawk, ctx={}: f" Squawk {squawk} – {cs}"
    },

    "einladung_fis": {
        "patterns": [
            "erbitte abfluginformationen"],
        "response": lambda cs, fis, ctx={}: f"{fis} – {cs}"
    },

    "anmeldung_fis": {
        "patterns": [
            "erbitte rollinformationen"],
        "response": lambda cs, airplane_type, num_pax, dep, arr, report, alt, ctx={}: f"{cs}, {airplane_type}, {num_pax} Personen, VFR-Flug von {dep} nach {arr}, soeben {report} Strecke verlassen in {alt} Fuß Höhe, erbitte Verkehrsinformationen"
    },

    "verkehrsinformationen": {
        "patterns": [
            "identifiziert", "Squawk", "Transponder", "QNH"],
        "response": lambda cs, QNH, squawk, ctx={}: f"QNH {QNH}, Squawk {squawk} – {cs}."
    },

    "frequency_change": {
        "patterns": [
            "wechseln sie auf", "wechseln sie zu", "wechseln sie auf die frequenz"],
        "response": lambda cs, fis2, ctx={}: f"Wechsel auf {fis2} – {cs}."
    },

    "abmeldung_fis": {
        "patterns": [
            "verlassen"],
        "response": lambda cs, arr, ctx={}: f"{cs} Erbitte Verlassen der Frequenz zum Melden in {arr} "
    },

    "einladung_arr": {
        "patterns": [
            "erbitte abfluginformationen"],
        "response": lambda cs, arr_info, ctx={}: f"{arr_info} – {cs}"
    },

    "anmeldung_arr_info": {
        "patterns": [
            "Info", "Radio"],
        "response": lambda cs, airplane_type, num_pax, dep, arr, position, alt, report, ctx={}: f"{cs}, {airplane_type}, {num_pax}, VFR-Flug von {dep} nach {arr}, {position} vom Flugplatz, in {alt} Fuß Höhe, zur Landung über {report} ",
    },

    "anflug_frei": {
        "patterns": [
            "identifiziert", "Anflug", "Squwak"],
        "response": lambda cs, squawk, ctx={}: f" Squawk {squawk} — {cs}"
    },

    "report_point": {
        "patterns": [
            "Höhe", "Fuß", "stellen sie code ein"],
        "response": lambda cs, report, alt, ctx={}: f"{cs} über {report} in {alt} Fuß Höhe, melde Queranflug"
    },

    "durchstarten": {
        "patterns": [
            "durchstarten", "go around", "abbrechen landung"],
        "response": lambda cs, ctx={}: f" {cs} – startet durch."
    }
}

PHASE_MAPPING = {
    "einladung_vorfeld": "Pre-Start / Taxi",
    "anmeldung_vorfeld": "Pre-Start / Taxi",
    "rollfreigabe": "Pre-Start / Taxi",

    "einladung_info": "Departure / Takeoff",
    "abflugbereit": "Departure / Takeoff",
    "startfreigabe": "Departure / Takeoff",
    "abmeldung_twr": "Departure / Takeoff",
    "squawk_info": "Departure / Takeoff",

    "einladung_fis": "Enroute / Cruise",
    "anmeldung_fis": "Enroute / Cruise",
    "verkehrsinformationen": "Enroute / Cruise",
    "abmeldung_fis": "Enroute / Cruise",
    #"frequency_change": "Enroute / Cruise",
    "squawk_info": "Enroute / Cruise",

    "einladung_arr": "Arrival / Traffic Circuit",
    "anmeldung_arr_info": "Arrival / Traffic Circuit",
    "anflug_frei": "Arrival / Traffic Circuit",
    "report_point": "Arrival / Traffic Circuit",
    "durchstarten": "Arrival / Traffic Circuit"
}

PHASE_ORDER = [
    "Pre-Start / Taxi",
    "Departure / Takeoff",
    "Enroute / Cruise",
    "Arrival / Traffic Circuit"
]

NUMBER_WORDS_DE = {
    "null": "0",
    "eins": "1",
    "zwo": "2",  # Luftfahrt-Variante von zwei
    "zwei": "2",
    "drei": "3",
    "vier": "4",
    "fünf": "5",
    "sechs": "6",
    "sieben": "7",
    "acht": "8",
    "neun": "9",
    "zehn": "10",
    "elf": "11",
    "zwölf": "12"
}

def words_to_number_de(words):
    return ''.join(NUMBER_WORDS_DE.get(w.lower(), w) for w in words)