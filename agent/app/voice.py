"""Voice routes: speech-to-text (Groq Whisper Turbo) and text-to-speech (Edge-TTS)."""
import os
import edge_tts
from fastapi import APIRouter, UploadFile
from fastapi.responses import Response
from groq import Groq
from pydantic import BaseModel

router = APIRouter()

@router.post("/stt")
async def stt(file: UploadFile):
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    r = client.audio.transcriptions.create(file=(file.filename or "audio.webm", await file.read()), model="whisper-large-v3-turbo")
    return {"text": r.text}

class TTSIn(BaseModel):
    text: str
    voice: str = "en-US-AriaNeural"

@router.post("/tts")
async def tts(t: TTSIn):
    audio = b""
    async for chunk in edge_tts.Communicate(t.text, t.voice).stream():
        if chunk["type"] == "audio": audio += chunk["data"]
    return Response(audio, media_type="audio/mpeg")
