import gradio as gr
import torch
import torchaudio
import os
import tempfile
import geopandas as gpd
import json
from collections import OrderedDict
from shapely.geometry import Point
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from pydub import AudioSegment
import torchaudio.transforms as T
from transcription_utils import generate_response, normalize_text_to_callsign, extract_context_from_transcript
from icao_rules_en import ICAO_RULES_EN
from icao_rules_de import ICAO_RULES_DE
from flight_plan_utils import generate_checklist_from_form


# Model setup
MODEL_ID = "openai/whisper-small"
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

# Fallback logic (e.g., GPT)
def ml_fallback_handler(transcript, callsign):
    return f"No ICAO phrase matched.\n\nSuggested interpretation: '{transcript}'"


def checklist_ui_from_dict(checklist_dict):
    markdown = ""
    for phase, calls in checklist_dict.items():
        markdown += f"### {phase}\n"
        for call in calls:
            markdown += f"- [ ] {call}\n"
        markdown += "\n"
    return markdown

# Main processing logic
def process_input(audio, callsign, language):
    if audio is None or callsign.strip() == "":
        return "No input received.", "", ""

    waveform, sample_rate = load_audio(audio)
    inputs = processor(
        waveform.squeeze(),
        sampling_rate=sample_rate,
        return_tensors="pt",
        language=language,
        task="transcribe"
    )
    with torch.no_grad():
        predicted_ids = model.generate(inputs.input_features)
    transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]

    rules = ICAO_RULES_DE if language == "de" else ICAO_RULES_EN
    context = extract_context_from_transcript(transcription, language)
    response = generate_response(transcription, callsign, rules, context)

    if response is None:
        norm_text = normalize_text_to_callsign(transcription)
        response = ml_fallback_handler(transcription, callsign)
    else:
        norm_text = normalize_text_to_callsign(transcription)

    return transcription, norm_text, response


# UI
# First view: Your existing radio transcription assistant
with gr.Blocks() as demo:
    gr.Markdown("## ATCopilot – Radio Communication Assistant")

    # First Tab: Transcription
    with gr.Tab("Transcription"):
        with gr.Row():
            audio_input = gr.Audio(type="filepath", label="Speak your transmission")
            callsign_input = gr.Textbox(label="Your callsign (e.g., D-EABC)")
            language_input = gr.Radio(["de", "en"], label="Language", value="de")
        with gr.Row():
            transcription_output = gr.Textbox(label="Transcription")
            callsign_output = gr.Textbox(label="Extracted Callsign")
            response_output = gr.Textbox(label="Suggested Response")
        transcribe_btn = gr.Button("Analyze")
        transcribe_btn.click(
            fn=process_input,
            inputs=[audio_input, callsign_input, language_input],
            outputs=[transcription_output, callsign_output, response_output]
        )

    # ✅ Second Tab: Checklist Generator
    with gr.Tab("Checklist Generator"):
        with gr.Row():
            cs = gr.Textbox(label="Callsign", value="D-ABCD")
            airplane_type = gr.Textbox(label="Aircraft Type", value="C172")
            num_pax = gr.Number(label="Number of PAX", value=2)

        with gr.Row():
            dep = gr.Textbox(label="Departure ICAO", value="EDFE")
            arr = gr.Textbox(label="Arrival ICAO", value="EDFN")
            position = gr.Textbox(label="Start Position", value="Vorfeld A")

        with gr.Row():
            Piste = gr.Textbox(label="Runway", value="25L")
            QNH = gr.Textbox(label="QNH", value="1013 hPa")
            report = gr.Textbox(label="Reporting Point", value="Kilo")

        with gr.Row():
            squawk = gr.Textbox(label="Squawk", value="7000")
            #fis = gr.Textbox(label="FIS Name", value="Langen Information")
            alt = gr.Number(label="Altitude (ft)", value=3000)

        with gr.Tab("Checklist"):
            checklist_display = gr.Markdown(label="Generated Checklist")

            def wrapper_generate_and_render(*inputs):
                checklist_dict = generate_checklist_from_form(*inputs)

                # Add a debug print (optional)
                print("Returned type:", type(checklist_dict))

                return checklist_ui_from_dict(checklist_dict)

            submit = gr.Button("Generate Checklist")

            submit.click(
                fn=wrapper_generate_and_render,
                inputs=[cs, airplane_type, num_pax, dep, arr, position, Piste, QNH, report, squawk, alt],
                outputs=[checklist_display]
            )

if __name__ == "__main__":
    demo.launch()