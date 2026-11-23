
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.classifier import classify_message
from app.agent import run_agent


app = FastAPI(
    title="ShopAssist API",
    description="Assistant intelligent pour le service client d'une boutique en ligne.",
    version="1.0.0"
)


class MessageRequest(BaseModel):
    message: str = Field(
        min_length=1,
        description="Message envoyé par le client"
    )


@app.get("/")
def home():
    return {
        "message": "Bienvenue sur ShopAssist",
        "status": "API opérationnelle"
    }


@app.post("/classify")
def classify(request: MessageRequest):
    try:
        return classify_message(request.message)

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@app.post("/chat")
def chat(request: MessageRequest):
    try:
        response = run_agent(request.message)

        return {
            "message": request.message,
            "response": response
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
