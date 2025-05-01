import gradio as gr
import torch
import torchaudio
import os
import tempfile
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from pydub import AudioSegment
import torchaudio.transforms as T
from icao_rules import generate_response, normalize_text_to_callsign, extract_context_from_transcript

# Modell
MODEL_ID = "jlvdoorn/whisper-small-atcosim"
processor = WhisperProcessor.from_pretrained(MODEL_ID)
model = WhisperForConditionalGeneration.from_pretrained(MODEL_ID)
model.eval()

def load_audio(audio_path, target_sr=16000):
    try:
        waveform, sample_rate = torchaudio.load(audio_path)
    except Exception:
        audio = AudioSegment.from_file(audio_path)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            audio.export(tmp.name, format="wav")
            waveform, sample_rate = torchaudio.load(tmp.name)
            os.remove(tmp.name)

    if sample_rate != target_sr:
        waveform = T.Resample(orig_freq=sample_rate, new_freq=target_sr)(waveform)
    return waveform, target_sr

# Platzhalter für ML-basierten Fallback (z. B. GPT API)
def ml_fallback_handler(transcript, callsign):
    return f"⚠️ Kein ICAO-Muster erkannt.\n\n📝 Vorschlag basierend auf Freitext: '{transcript}'"

# Hauptlogik
def process_input(audio, callsign):
    if audio is None or callsign.strip() == "":
        return "Keine Eingabe erhalten.", "", ""

    waveform, sample_rate = load_audio(audio)
    inputs = processor(waveform.squeeze(), sampling_rate=sample_rate, return_tensors="pt", language="en")
    with torch.no_grad():
        attention_mask = inputs.get("attention_mask", None)
        predicted_ids = model.generate(inputs.input_features, attention_mask=attention_mask)
    transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]

    context = extract_context_from_transcript(transcription)
    response = generate_response(transcription, callsign, context)

    if response is None:
        norm_text = normalize_text_to_callsign(transcription)
        response = ml_fallback_handler(transcription, callsign)
    else:
        norm_text = normalize_text_to_callsign(transcription)

    return transcription, norm_text, response

# UI
demo = gr.Interface(
    fn=process_input,
    inputs=[
        gr.Audio(type="filepath", label="🎙️ Sprich deinen Funkspruch"),
        gr.Textbox(label="✈️ Dein Rufzeichen (z. B. D-EABC)")
    ],
    outputs=[
        gr.Textbox(label="📝 Transkription"),
        gr.Textbox(label="📛 Erkanntes Rufzeichen (aus Transkript)"),
        gr.Textbox(label="💬 Antwortvorschlag")
    ],
    title="🛫 Flugfunk ATC-Parser",
    description="Regelbasiertes ICAO-Funkanalyse-Tool mit Fallback auf ML-Modell bei unbekannten Funksprüchen.",
    live=False
)

if __name__ == "__main__":
    demo.launch()