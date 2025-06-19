# training_scenarios.py

TRAINING_SCENARIOS = [
    {
        "id": 1,
        "language": "de",
        "prompt": "Du bist am Haltepunkt der Piste 27. Bitte erbitte Startfreigabe.",
        "expected_intent": "startfreigabe",
        "expected_context": {"runway": "27"}
    },
    {
        "id": 2,
        "language": "de",
        "prompt": "Du befindest dich am Rollhalt. Bitte frage nach Rollfreigabe zur Piste 27.",
        "expected_intent": "rollfreigabe",
        "expected_context": {"runway": "27"}
    },
    {
        "id": 3,
        "language": "en",
        "prompt": "You are ready for departure at holding point C. Request take-off clearance.",
        "expected_intent": "takeoff_clearance",
        "expected_context": {"runway": "27"}
    },
    {
        "id": 4,
        "language": "de",
        "prompt": "Du meldest dich bei Langen Information zum ersten Mal auf dieser Frequenz.",
        "expected_intent": "frequenz_neu_anruf",
        "expected_context": {"ziel": "Hamburg", "personen": "2"}
    }
]
