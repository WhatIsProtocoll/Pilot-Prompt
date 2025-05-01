import gradio as gr
import torch
import torchaudio
import os
import tempfile
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from pydub import AudioSegment
import torchaudio.transforms as T

torchaudio.set_audio_backend("soundfile")

MODEL_ID = "jlvdoorn/whisper-small-atcosim"

processor = WhisperProcessor.from_pretrained(MODEL_ID)
model = WhisperForConditionalGeneration.from_pretrained(MODEL_ID)
model.eval()

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

def load_audio(audio_path, target_sr=16000):
    try:
        waveform, sample_rate = torchaudio.load(audio_path)
    except Exception as e:
        audio = AudioSegment.from_file(audio_path)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            audio.export(tmp.name, format="wav")
            waveform, sample_rate = torchaudio.load(tmp.name)
            os.remove(tmp.name)

    if sample_rate != target_sr:
        waveform = T.Resample(orig_freq=sample_rate, new_freq=target_sr)(waveform)
        sample_rate = target_sr

    return waveform, sample_rate

def detect_intent(text, callsign):
    normalized_text = normalize_text_to_callsign(text)
    norm_callsign = callsign.replace("-", "").lower()
    norm_text = normalized_text.replace("-", "").replace(" ", "").lower()

    if norm_callsign not in norm_text:
        return None, normalized_text

    text = text.lower()
    if "cleared to land" in text:
        return "landing_clearance", normalized_text
    if "cleared for takeoff" in text:
        return "takeoff_clearance", normalized_text
    if "contact tower" in text or "change frequency" in text:
        return "frequency_change", normalized_text
    if "squawk" in text:
        return "squawk_assignment", normalized_text
    return "unknown", normalized_text

def generate_response(intent, callsign, runway="27"):
    if intent == "landing_clearance":
        return f"{callsign}, roger, cleared to land runway {runway}"
    if intent == "takeoff_clearance":
        return f"{callsign}, ready for departure runway {runway}"
    if intent == "frequency_change":
        return f"{callsign}, switching frequency, goodbye"
    if intent == "squawk_assignment":
        return f"{callsign}, squawk set, thank you"
    return "Keine Standardantwort gefunden."

def process_input(audio, callsign):
    if audio is None or callsign == "":
        return "Keine Eingabe erhalten.", "", ""

    tmp_path = audio  # audio ist jetzt ein Pfad, keine Binärdaten mehr
    waveform, sample_rate = load_audio(tmp_path)
    inputs = processor(waveform.squeeze(), sampling_rate=sample_rate, return_tensors="pt")

    with torch.no_grad():
        predicted_ids = model.generate(inputs.input_features)
    transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]

    intent, norm_text = detect_intent(transcription, callsign)
    if intent:
        response = generate_response(intent, callsign)
    else:
        response = "Keine relevante Nachricht für dein Rufzeichen erkannt."

    return transcription, norm_text, response

# Gradio UI
demo = gr.Interface(
    fn=process_input,
    inputs=[
        gr.Audio(type="filepath", label="🎙️ Sprich deinen Funkspruch"),
        gr.Textbox(label="✈️ Dein Rufzeichen (z. B. D-EABC)")
    ],
    outputs=[
        gr.Textbox(label="📝 Transkription"),
        gr.Textbox(label="🔍 Erkanntes Rufzeichen im Transkript"),
        gr.Textbox(label="💬 Antwortvorschlag")
    ],
    title="🛫 Flugfunk Transkription & Antwort",
    description="Sprich deinen ATC-Funkspruch direkt ins Mikrofon und erhalte sofort eine Antwortempfehlung.",
    live=False
)

if __name__ == "__main__":
    demo.launch()