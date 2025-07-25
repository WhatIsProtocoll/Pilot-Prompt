import os
import json
import base64
import threading
import sounddevice as sd
import websocket
import time


audio_thread = None
ws_app = None
stop_event = threading.Event()

API_KEY = os.getenv("OPENAI_API_KEY")
if API_KEY is None:
    raise ValueError("❗ OPENAI_API_KEY environment variable not set.")

URL = "wss://api.openai.com/v1/realtime?intent=transcription"
HEADERS = [
    "Authorization: Bearer " + API_KEY,
    "OpenAI-Beta: realtime=v1"
]

SAMPLE_RATE = 16000
CHANNELS = 1

# Shared session holder (thread-safe via dict)
session_holder = {"id": None}
session_ready = threading.Event()

def send_audio_stream(ws, stop_event, session_holder, session_ready):
    # Wait until session is ready or stop is requested
    session_ready.wait()

    if stop_event.is_set():
        return

    def callback(indata, frames, time_info, status):
        if status:
            print("Audio error:", status)

        if stop_event.is_set() or not ws.sock or not ws.sock.connected:
            raise sd.CallbackStop()

        session_id = session_holder["id"]

        audio_bytes = bytes(indata)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        payload = {
            "type": "input_audio_buffer.append",
            "audio": audio_b64
        }

        try:
            ws.send(json.dumps(payload))
        except Exception as e:
            print("WebSocket send error:", e)
            raise sd.CallbackStop()

    with sd.RawInputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='int16', callback=callback):
        stop_event.wait()

def on_close(ws, close_status_code, close_msg):
    print(f"🔴 Connection closed: {close_status_code} - {close_msg}")
    stop_audio_stream()

def on_error(ws, error):
    print("❗Error:", error)
    stop_audio_stream()

def stop_audio_stream():
    global audio_thread, ws_app

    stop_event.set()

    if audio_thread and audio_thread.is_alive():
        audio_thread.join()
        print("🛑 Audio thread stopped.")

    if ws_app:
        ws_app.close()
        print("🛑 WebSocket closed.")

def start_transcription(output_box=None):
    global ws_app, audio_thread

    def on_message_custom(ws, message):
        data = json.loads(message)
        msg_type = data.get("type", "")

        if msg_type == "transcription_session.created":
            session_holder["id"] = data["session"]["id"]
            print(f"🎙️ Session created: {session_holder['id']}")

            # Start audio stream directly after session creation (no second update needed)
            session_ready.set()

            stop_event.clear()
            audio_thread = threading.Thread(
                target=send_audio_stream,
                args=(ws, stop_event, session_holder, session_ready),
                daemon=True
            )
            audio_thread.start()

        elif msg_type == "input_audio_transcription":
            text = data["input_audio_transcription"]["text"]
            if output_box is not None:
                output_box.append(text)
            else:
                print(f"📝 {text}")

        elif msg_type == "turn_start":
            print("🔊 Turn started.")
        elif msg_type == "turn_end":
            print("🔇 Turn ended.")
        else:
            # Optionally print other messages for debugging
            print("📩 Received:", data)

    def on_open(ws):
        print("✅ Connected to OpenAI Realtime API")

        # Initial session creation with configuration (no need for second update)
        setup = {
            "type": "transcription_session.update",
            "input_audio": {"format": "pcm16"},
            "input_audio_transcription": {
                "model": "gpt-4o-mini-transcribe",
                "prompt": "",
                "language": "en"   # Explicit language
            },
            "turn_detection": {
                "type": "server_vad",
                "threshold": 0.5,
                "prefix_padding_ms": 300,
                "silence_duration_ms": 500
            },
            "input_audio_noise_reduction": {
                "type": "near_field"
            },
            "include": [
                "item.input_audio_transcription.logprobs"
            ]
        }

        ws.send(json.dumps(setup))

    ws_app = websocket.WebSocketApp(
        URL,
        header=HEADERS,
        on_open=on_open,
        on_message=on_message_custom,
        on_close=on_close,
        on_error=on_error
    )

    threading.Thread(target=ws_app.run_forever, daemon=True).start()