# invite_rules_de.py

INVITE_RULES_DE = {
    "einladung_vorfeld": {
        "patterns": [
            "vorfeld", "apron", "ground", "ground control"],
        "required_keys": ["rufzeichen", "typ", "personen", "ziel", "position", "bitte"]
    },
    "einladung_turm": {
        "patterns": [
            "turm", "tower"],
        "required_keys": ["rufzeichen", "typ", "personen", "ziel", "piste"]
    },
    "einladung_fis": {
        "patterns": [
            "langen information", "fluginformation"],
        "required_keys": ["rufzeichen", "typ", "personen", "ziel", "position", "höhe", "transponder"]
    },
    "einladung_rollhalt": {
        "patterns": [
            "haltepunkt", "rollhalt", "abflugbereit"],
        "required_keys": ["rufzeichen", "abflugbereit", "rollhalt", "runway"]
    },
    "einladung_radio": {
        "patterns": [
            "info", "radio", "flugleitung"],
        "required_keys": ["rufzeichen", "typ", "personen", "ziel", "position"]
    }
}

def detect_invite_intent(text):
    text_lc = text.lower()
    for intent, rule in INVITE_RULES_DE.items():
        for pattern in rule["patterns"]:
            if pattern in text_lc:
                return intent, rule.get("required_keys", [])
    return None, []