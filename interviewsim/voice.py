import whisper
import tempfile
import os

_model = None

def load_model():
    global _model
    if _model is None:
        _model = whisper.load_model("base")  # small & fast
    return _model

def transcribe(audio_bytes: bytes) -> str:
    model = load_model()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name
    try:
        result = model.transcribe(tmp_path)
        return result["text"].strip()
    finally:
        os.unlink(tmp_path)