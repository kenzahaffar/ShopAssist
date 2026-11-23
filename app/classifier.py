
import json
from groq import Groq
from pydantic import ValidationError

from app.schemas import ClassificationResult, Category
from app.config import MODE, GROQ_API_KEY, GROQ_MODEL


def classify_local(message: str) -> ClassificationResult:
    text = message.lower()

    if any(word in text for word in ["paiement", "payer", "carte", "facture", "débité"]):
        category = "paiement"
        justification = "Le message concerne le paiement."

    elif any(word in text for word in ["retour", "rembourser", "remboursement", "échanger", "rendre"]):
        category = "retour"
        justification = "Le message concerne un retour ou un remboursement."

    elif any(word in text for word in ["livraison", "livré", "livree", "colis", "paquet", "livreur", "expédié", "expedie", "retard"]):
        category = "livraison"
        justification = "Le message concerne la livraison."

    elif any(word in text for word in ["commande", "commander", "c1"]):
        category = "commande"
        justification = "Le message concerne une commande."

    else:
        category = "autre"
        justification = "La catégorie du message n'est pas clairement identifiée."

    return ClassificationResult(
        category=category,
        confidence=0.60,
        justification=justification,
        needs_review=True
    )


def classify_message(message: str) -> ClassificationResult:
    if not message.strip():
        return ClassificationResult(
            category="autre",
            confidence=1.0,
            justification="Le message est vide.",
            needs_review=True
        )

    if MODE == "mock":
        result = classify_local(message)
        result.confidence = 0.90 if result.category != Category.AUTRE else 0.50
        result.needs_review = result.category == Category.AUTRE
        return result

    if MODE == "real":
        if not GROQ_API_KEY:
            raise ValueError("La clé API Groq est manquante.")

        client = Groq(api_key=GROQ_API_KEY)

        prompt = f"""
Tu es un classificateur de messages pour une boutique en ligne.

Choisis une seule catégorie parmi :
livraison, paiement, commande, retour, autre.

Règles de classification :
- Si le client parle de sa commande, de sa confirmation ou de sa modification, choisis commande.
- Si le client demande où est sa commande ou veut connaître son état, choisis commande.
- Si le client parle de son colis, du livreur, d'un retard de livraison ou de la date de livraison, choisis livraison.
- Si le client parle de facture, carte bancaire ou paiement, choisis paiement.
- Si le client parle de remboursement, échange ou retour d'article, choisis retour.
- Si le message est une simple salutation ou une demande trop vague, choisis autre.

Exemples importants :
Message : Où est ma commande C1001 ?
Catégorie : commande

Message : Mon colis n'est toujours pas arrivé.
Catégorie : livraison

Message : Quand sera livré mon paquet ?
Catégorie : livraison

Message : Je veux modifier ma commande.
Catégorie : commande

Message : Je souhaite obtenir un remboursement.
Catégorie : retour

Message : Bonjour, comment allez-vous ?
Catégorie : autre

Message à classer : {message}

Retourne uniquement un JSON valide avec exactement ces quatre champs :
category, confidence, justification, needs_review.

confidence doit être un nombre entre 0 et 1.
needs_review doit être un booléen.
Si le message est ambigu, utilise autre et needs_review=true.
"""

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        content = response.choices[0].message.content

        try:
            if not content:
                raise ValueError("Réponse vide de Groq.")

            start = content.find("{")
            end = content.rfind("}")

            if start == -1 or end == -1:
                raise ValueError("JSON introuvable.")

            data = json.loads(content[start:end + 1])

            if not isinstance(data, dict):
                raise ValueError("Format JSON invalide.")

            data.setdefault("needs_review", False)

            classification = ClassificationResult.model_validate(data)

            classification.needs_review = (
                classification.confidence < 0.70
                or classification.category == Category.AUTRE
            )

            return classification

        except (ValueError, json.JSONDecodeError, ValidationError, TypeError):
            return classify_local(message)

    raise ValueError("Mode invalide.")
