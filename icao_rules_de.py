# icao_rules_de.py

# icao_rules_de.py

ICAO_RULES_DE = {
    "freigabe_erbeten": {
        "patterns": [
            "erbitte freigabe", "anfrage freigabe", "freigabe erbeten"],
        "response": lambda cs, ctx={}: f"Freigabe erteilt nach {ctx.get('ziel', 'Zielort')} über {ctx.get('sid', 'SID')}, Squawk {ctx.get('squawk', 'XXXX')} — {cs}"
    },

    "rollfreigabe": {
        "patterns": [
            "rollfreigabe", "erbitte rollen", "rolle zur startbahn"],
        "response": lambda cs, ctx={}: f"Rollen Sie zu Haltepunkt {ctx.get('punkt', 'C')}, Piste {ctx.get('runway', '27')} — {cs}"
    },

    "startfreigabe": {
        "patterns": [
            "start frei", "startfreigabe erteilt", "startbahn frei"],
        "response": lambda cs, ctx={}: f"Startbahn {ctx.get('runway', '27')}, Start frei — {cs}"
    },

    "lande_freigabe": {
        "patterns": [
            "landung frei", "freigabe zur landung", "piste frei zur landung"],
        "response": lambda cs, ctx={}: f"Landung frei auf Piste {ctx.get('runway', '27')} — {cs}"
    },

    "frequenzwechsel": {
        "patterns": [
            "wechsel auf frequenz", "kontaktieren sie tower", "wechseln auf"],
        "response": lambda cs, ctx={}: f"Wechseln Sie auf {ctx.get('frequency', '118.5')} — {cs}"
    },

    "frequenz_neu_anruf": {
        "patterns": [
            "kontaktaufnahme", "anruf neue frequenz", "funkkontakt neu"],
        "response": lambda cs, ctx={}: f"{cs}, Funkkontakt hergestellt"
    },

    "squawk_code": {
        "patterns": [
            "squawk", "transpondercode", "stellen sie code ein"],
        "response": lambda cs, ctx={}: f"Squawk {ctx.get('squawk', '7000')} gesetzt — {cs}"
    },

    "durchstarten": {
        "patterns": [
            "durchstarten", "go around", "abbrechen landung"],
        "response": lambda cs, ctx={}: f"Durchstarten, melden Sie Queranflug — {cs}"
    }
}


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