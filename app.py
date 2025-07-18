import gradio as gr
import torch
import librosa
import geopandas as gpd
import time
import socket
import subprocess
import os
from collections import OrderedDict
from shapely.geometry import Point
from transformers import AutoFeatureExtractor, AutoTokenizer, WhisperProcessor, WhisperForConditionalGeneration, pipeline
from pydub import AudioSegment
import torchaudio.transforms as T
from transcription_utils import normalize_text_to_callsign, extract_context_from_transcript, get_icao_response, clean_transcript, strip_callsign_from_transcript, callsign_matches
from icao_rules_en import ICAO_RULES_EN
from icao_rules_de import ICAO_RULES_DE
from flight_plan_utils import generate_checklist_from_form
from whisper_streaming.whisper_mic_client import run_mic_client, stop_mic_client, transcription_queue
from whisper_streaming.whisper_server_launcher import launch_whisper_server
import sounddevice as sd
import threading
from queue import Empty
from threading import Event
import signal

stop_event = Event()
sd.default.device = (1, None)
whisper_proc = None   

# Model setup
MODEL_ID = "tclin/distil-large-v3.5-atcosim-finetune"
processor = WhisperProcessor.from_pretrained(MODEL_ID)
model = WhisperForConditionalGeneration.from_pretrained(MODEL_ID)
model.generation_config.forced_decoder_ids = None

######################### Audio Processing ######################### 
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

def checklist_markdown(checklist_dict):
    markdown = ""
    for phase, calls in checklist_dict.items():
        markdown += f"### {phase}\n"
        for item in calls:
            markdown += f"- [ ] {item}\n"
        markdown += "\n"
    return markdown

def start_whisper_server():
    cmd = [
        "python", "whisper_streaming/whisper_online_server.py",
        "--model_dir", "whisper-tiny-mlx",
        "--backend", "mlx-whisper",
        "--lan", "en",
        "--task", "transcribe",
        "--port", "43007",
        "--buffer_trimming", "sentence",
        "--buffer_trimming_sec", "5"
    ]

    # Start as a background process
    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid  # Optional: makes it a separate process group (for easier management)
    )

def wait_for_server(host, port, timeout=10):
    """Wait for a TCP server to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                print("✅ Whisper server is ready.")
                return True
        except OSError:
            time.sleep(0.5)
    raise RuntimeError("❗ Whisper server did not become ready in time.")

def transcribe_stream():
    while True:
        text = transcription_queue.get()
        yield text

def stop_transcription():
    stop_mic_client()

    global whisper_proc
    if whisper_proc:
        try:
            whisper_proc.terminate()
            whisper_proc.wait(timeout=5)
            whisper_proc = None
            return "🛑 Whisper server and mic client stopped."
        except Exception as e:
            return f"Error stopping Whisper server: {e}"
    else:
        return "Mic client stopped. No Whisper server running."

######################### Gradio UI Setup #########################

# UI
with gr.Blocks() as demo:
    gr.Markdown("## ATCopilot – Radio Communication Assistant")

    # First View: Live Transcription
    with gr.Tab("Live Transcription"):
        live_output_stream = gr.Textbox(label="Live Transcription", lines=10, interactive=False)

        start_btn = gr.Button("Start Transcription")
        stop_btn = gr.Button("Stop Transcription")
        stop_btn.click(fn=stop_transcription, outputs=[])

        def start():
            threading.Thread(target=run_mic_client, daemon=True).start()

        start_btn.click(fn=start, outputs=[])

        def is_phrasing_point(text):
            return text.strip().endswith((".", "!", "?", "over", "out", "roger", "cleared", "ready"))

        def generator():
            buffer = ""
            full_transcript = ""
            last_time = time.time()

            while True:
                new_text = transcription_queue.get()
                current_time = time.time()

                # If there's a gap >1.5 seconds between chunks, assume pause
                if current_time - last_time > 1.5:
                    # Treat buffer as completed "sentence" on pause
                    if buffer.strip():
                        full_transcript += buffer.strip() + "\n\n"
                        buffer = ""

                buffer += new_text + " "
                last_time = current_time

                yield full_transcript + buffer.strip()

        demo.load(generator, outputs=[live_output_stream])


    # Second Tab: Transcription
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

    # Third Tab: Checklist Generator
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
                image_path, checklist_dict = generate_checklist_from_form(*inputs)
                return image_path, checklist_markdown(checklist_dict)

            submit = gr.Button("Generate Checklist")

            route_image = gr.Image(label="Route over FIS Airspaces", type="filepath")
            checklist_display = gr.Markdown()

            submit.click(
                fn=wrapper_generate_and_render,
                inputs=[cs, airplane_type, num_pax, dep, arr, position],
                outputs=[route_image, checklist_display]
            )

if __name__ == "__main__":
    print("🚀 Starting Whisper Server...")
    whisper_proc = launch_whisper_server()

    print("⏳ Waiting for Whisper server to become ready...")
    wait_for_server("localhost", 43007)

    print("🖥️ Launching Webapp...")
    demo.launch()