import gradio as gr
import numpy as np
import torch
import librosa
import geopandas as gpd
import json
from collections import OrderedDict
from shapely.geometry import Point
from transformers import AutoFeatureExtractor, AutoTokenizer, WhisperProcessor, WhisperForConditionalGeneration, pipeline
from pydub import AudioSegment
import torchaudio.transforms as T
from transcription_utils import normalize_text_to_callsign, extract_context_from_transcript, get_icao_response, clean_transcript, strip_callsign_from_transcript, callsign_matches
from icao_rules_en import ICAO_RULES_EN
from icao_rules_de import ICAO_RULES_DE
from flight_plan_utils import generate_checklist_from_form
from faster_whisper import WhisperModel
from silero_vad import load_silero_vad, get_speech_timestamps
import re
from live_transcription import start_transcription, stop_audio_stream, send_audio_stream, poll_transcript
from shared import shared_transcript, shared_lock
import sounddevice as sd

sd.default.device = (1, None)  

# Model setup
MODEL_ID = "tclin/whisper-large-v3-turbo-atcosim-finetune"
processor = WhisperProcessor.from_pretrained(MODEL_ID)
model = WhisperForConditionalGeneration.from_pretrained(MODEL_ID)
model.generation_config.forced_decoder_ids = None
model.generation_config.pad_token_id = model.generation_config.eos_token_id

# Real-time setup
RTModel = WhisperModel(
    "jacktol/whisper-medium.en-fine-tuned-for-ATC-faster-whisper",
    device="cpu",
    compute_type="int8"
)


def load_audio(audio_path):
    # Load and resample to 16000 Hz (Whisper expects 16kHz)
    waveform, sr = librosa.load(audio_path, sr=16000)
    return waveform, sr

def process_input(audio, callsign, language):
    response, intent = "", None

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
    print(f"Raw transcription: {transcription}")

    extracted_cs = normalize_text_to_callsign(transcription)
    print(f"Normalized text: {extracted_cs}")
    print(f"Input callsign: {callsign}")
    
    transcription = clean_transcript(transcription)
    print(f"Transcription: {transcription}")

    context = extract_context_from_transcript(transcription, language)
    print(f"Extracted context: {context}")
    
    if callsign_matches(callsign, extracted_cs):
        cleaned = strip_callsign_from_transcript(transcription, callsign, ICAO_RULES_EN if language == "en" else ICAO_RULES_DE)
        response, intent = get_icao_response(cleaned, callsign, context, language)
        print(f"Generated response: {response}")
    
    if not response:
        response = "No relevant transmission detected for your callsign."

    return transcription, extracted_cs, response


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

    with gr.Tab("Live Transcription"):

        timer = gr.Timer(1)
        live_output = gr.Textbox(
            label="Live Transcription",
            lines=10,
            interactive=False,
            value=poll_transcript,   # periodically call this function
            every=timer                  # every 1 second
        )
        status = gr.Textbox(label="Status", interactive=False)
        start_button = gr.Button("Start Live Transcription")
        stop_button = gr.Button("Stop")

        def start():
            with shared_lock:
                shared_transcript["full_text"] = ""
                shared_transcript["current"] = ""
            start_transcription(live_output)  # start the websocket + audio thread
            return "🔴 Listening..."  # update status


        def stop():
            stop_audio_stream()
            return "🛑 Stopped."

        start_button.click(fn=start, outputs=[status])
        stop_button.click(fn=stop, outputs=[status])

    # First Tab: Transcription
    with gr.Tab("Transcription"):
        with gr.Row():
            with gr.Column():
                audio_input = gr.Audio(type="filepath", label="Speak your transmission")
                callsign_input = gr.Textbox(label="Your callsign (e.g., D-EABC)")
                language_input = gr.Radio(["en", "de"], label="Language", value="en")
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