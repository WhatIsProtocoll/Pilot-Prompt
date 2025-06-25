import gradio as gr
import torch
import librosa
import geopandas as gpd
import json
from collections import OrderedDict
from shapely.geometry import Point
from transformers import AutoFeatureExtractor, AutoTokenizer, WhisperProcessor, WhisperForConditionalGeneration, pipeline
from pydub import AudioSegment
import torchaudio.transforms as T
from transcription_utils import generate_response, normalize_text_to_callsign, extract_context_from_transcript
from icao_rules_en import ICAO_RULES_EN
from icao_rules_de import ICAO_RULES_DE
from flight_plan_utils import generate_checklist_from_form


# Model setup
MODEL_ID = "tclin/distil-large-v3.5-atcosim-finetune"
processor = WhisperProcessor.from_pretrained(MODEL_ID)
model = WhisperForConditionalGeneration.from_pretrained(MODEL_ID)
model.generation_config.forced_decoder_ids = None

def load_audio(audio_path):
    # Load and resample to 16000 Hz (Whisper expects 16kHz)
    waveform, sr = librosa.load(audio_path, sr=16000)
    return waveform, sr

def process_input(audio, callsign, language):
    if audio is None or callsign.strip() == "":
        return "No input received.", "", ""

    waveform, sample_rate = load_audio(audio)

    # Prepare input WITHOUT specifying task or language
    inputs = processor(
        waveform,
        sampling_rate=sample_rate,
        return_tensors="pt"
    )

    with torch.no_grad():
        predicted_ids = model.generate(inputs.input_features)  # No forced decoder IDs

    transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]

    rules = ICAO_RULES_DE if language == "de" else ICAO_RULES_EN
    context = extract_context_from_transcript(transcription, language)
    response = generate_response(transcription, callsign, rules, context)
    norm_text = normalize_text_to_callsign(transcription)

    if response is None:
        response = ml_fallback_handler(transcription, callsign)

    return transcription, norm_text, response

# Fallback logic (e.g., GPT)
def ml_fallback_handler(transcript, callsign):
    return f"No ICAO phrase matched.\n\nSuggested interpretation: '{transcript}'"


def checklist_markdown(checklist_dict):
    markdown = ""
    for phase, calls in checklist_dict.items():
        markdown += f"### {phase}\n"
        for item in calls:
            markdown += f"- [ ] {item}\n"
        markdown += "\n"
    return markdown


# UI
# First view: Your existing radio transcription assistant
with gr.Blocks() as demo:
    gr.Markdown("## ATCopilot – Radio Communication Assistant")

    # First Tab: Transcription
    with gr.Tab("Transcription"):
        with gr.Row():
            with gr.Column():
                audio_input = gr.Audio(type="filepath", label="Speak your transmission")
                callsign_input = gr.Textbox(label="Your callsign (e.g., D-EABC)")
                language_input = gr.Radio(["de", "en"], label="Language", value="de")
            with gr.Column():
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

        ''' Uncomment if you want to include runway, QNH, reporting point, squawk, and altitude
        with gr.Row():
            Piste = gr.Textbox(label="Runway", value="25L")
            QNH = gr.Textbox(label="QNH", value="1013 hPa")
            report = gr.Textbox(label="Reporting Point", value="Kilo")

        with gr.Row():
            squawk = gr.Textbox(label="Squawk", value="7000")
            #fis = gr.Textbox(label="FIS Name", value="Langen Information")
            alt = gr.Number(label="Altitude (ft)", value=3000)'''

        with gr.Tab("Checklist"):
            checklist_display = checklist_markdown({})

            def wrapper_generate_and_render(*inputs):
                checklist_dict = generate_checklist_from_form(*inputs)
                return checklist_markdown(checklist_dict)

            submit = gr.Button("Generate Checklist")

            checklist_display = gr.Markdown()
            submit.click(
                fn=wrapper_generate_and_render,
                inputs=[cs, airplane_type, num_pax, dep, arr, position],
                outputs=[checklist_display]
            )

if __name__ == "__main__":
    demo.launch()