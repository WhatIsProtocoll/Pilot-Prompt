from threading import Lock

shared_transcript = {"full_text": "", "current": ""}
shared_lock = Lock()