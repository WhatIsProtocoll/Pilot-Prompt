from threading import Lock

shared_transcript = {"text": ""}
shared_lock = Lock()