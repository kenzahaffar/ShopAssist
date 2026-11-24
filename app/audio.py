
from groq import Groq
from app.config import GROQ_API_KEY


AUDIO_MODEL = "whisper-large-v3-turbo"


def transcribe_audio(audio_content: bytes, filename: str) -> str:
    if not GROQ_API_KEY:
        raise ValueError("La clé API Groq est absente du fichier .env.")

    if not audio_content:
        raise ValueError("Le fichier audio est vide.")

    client = Groq(api_key=GROQ_API_KEY)

    transcription = client.audio.transcriptions.create(
        file=(filename, audio_content),
        model=AUDIO_MODEL,
        response_format="json",
        temperature=0
    )

    text = transcription.text.strip()

    if not text:
        raise ValueError("Aucun message vocal n'a été détecté.")

    return text
