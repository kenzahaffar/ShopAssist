import json
from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from app.classifier import classify_message
from app.agent import run_agent
from app.audio import transcribe_audio
from app.config import MODE, GROQ_API_KEY


app = FastAPI(
    title="ShopAssist API",
    description="Assistant intelligent pour le service client d'une boutique en ligne.",
    version="1.3.0"
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class MessageRequest(BaseModel):
    message: str = Field(
        min_length=1,
        description="Message envoyé par le client"
    )


def verifier_fichier(nom_fichier):
    chemin = DATA_DIR / nom_fichier

    if not chemin.exists():
        return {
            "status": "attention",
            "message": "Fichier introuvable."
        }

    try:
        with open(chemin, "r", encoding="utf-8") as fichier:
            contenu = json.load(fichier)

        if not isinstance(contenu, list):
            return {
                "status": "attention",
                "message": "Format incorrect : une liste JSON est attendue."
            }

        return {
            "status": "ok",
            "message": "Fichier accessible et JSON valide."
        }

    except json.JSONDecodeError:
        return {
            "status": "attention",
            "message": "Le contenu JSON est invalide."
        }
    except Exception:
        return {
            "status": "attention",
            "message": "Impossible de lire le fichier."
        }


@app.get("/")
def home():
    return {
        "message": "Bienvenue sur ShopAssist",
        "status": "API opérationnelle"
    }


@app.get("/diagnostic")
def diagnostic():
    verifications = {
        "mode": {
            "status": "ok" if MODE in ["mock", "real"] else "attention",
            "value": MODE
        },
        "cle_groq": {
            "status": "ok" if GROQ_API_KEY else (
                "attention" if MODE == "real" else "ok"
            ),
            "message": (
                "Clé Groq configurée."
                if GROQ_API_KEY
                else (
                    "Clé Groq absente."
                    if MODE == "real"
                    else "Non nécessaire en mode mock."
                )
            )
        },
        "fichier_commandes": verifier_fichier("orders.json"),
        "fichier_tickets": verifier_fichier("tickets.json")
    }

    tout_est_ok = all(
        verification["status"] == "ok"
        for verification in verifications.values()
    )

    return {
        "diagnostic": "ok" if tout_est_ok else "attention",
        "verifications": verifications
    }


@app.post("/classify")
def classify(request: MessageRequest):
    debut = perf_counter()

    try:
        resultat = classify_message(request.message)
        latence = round((perf_counter() - debut) * 1000, 2)

        return {
            "resultat": resultat,
            "latence_ms": latence
        }
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/chat")
def chat(request: MessageRequest):
    debut = perf_counter()

    try:
        response = run_agent(request.message)
        latence = round((perf_counter() - debut) * 1000, 2)

        return {
            "message": request.message,
            "response": response,
            "latence_ms": latence
        }
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/voice")
async def voice(file: UploadFile = File(...)):
    debut = perf_counter()

    try:
        audio_content = await file.read()

        if len(audio_content) > 25 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="Le fichier audio dépasse 25 Mo."
            )

        transcription = transcribe_audio(
            audio_content,
            file.filename or "message.wav"
        )

        response = run_agent(transcription)
        latence = round((perf_counter() - debut) * 1000, 2)

        return {
            "transcription": transcription,
            "response": response,
            "latence_ms": latence
        }

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))