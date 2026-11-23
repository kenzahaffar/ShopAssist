
import json
import unicodedata

from groq import Groq

from app.config import GROQ_API_KEY, GROQ_MODEL
from app.tools import (
    consult_order_status,
    check_return_eligibility,
    create_support_ticket
)


MAX_TOURS = 3


def demande_ticket(message: str) -> bool:
    texte = unicodedata.normalize("NFD", message.lower())
    texte = "".join(
        caractere for caractere in texte
        if unicodedata.category(caractere) != "Mn"
    )

    expressions = [
        "cree un ticket",
        "creer un ticket",
        "ouvre un ticket",
        "ouvrir un ticket",
        "je veux un ticket",
        "je souhaite un ticket",
        "cree-moi un ticket",
        "ouvrir un dossier de support"
    ]

    return any(expression in texte for expression in expressions)


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "consult_order_status",
            "description": "Consulter le statut d'une commande.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Identifiant de la commande, par exemple C1001."
                    }
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_return_eligibility",
            "description": "Vérifier si une commande peut être retournée.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Identifiant de la commande."
                    }
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_support_ticket",
            "description": "Créer un ticket de support uniquement à la demande explicite du client.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Identifiant de la commande."
                    },
                    "reason": {
                        "type": "string",
                        "description": "Motif du ticket."
                    }
                },
                "required": ["order_id", "reason"]
            }
        }
    }
]


def execute_tool(name: str, arguments: dict, ticket_authorized: bool):
    if name == "consult_order_status":
        return consult_order_status(arguments["order_id"])

    if name == "check_return_eligibility":
        return check_return_eligibility(arguments["order_id"])

    if name == "create_support_ticket":
        if not ticket_authorized:
            return {
                "created": False,
                "message": "Création non autorisée."
            }

        return create_support_ticket(
            arguments["order_id"],
            arguments["reason"],
            customer_requested=True
        )

    return {"error": "Outil inconnu."}


def run_agent(message: str) -> str:
    if not GROQ_API_KEY:
        raise ValueError("La clé API Groq est manquante.")

    client = Groq(api_key=GROQ_API_KEY)

    ticket_authorized = demande_ticket(message)

    available_tools = TOOLS if ticket_authorized else TOOLS[:2]

    messages = [
        {
            "role": "system",
            "content": (
                "Tu es ShopAssist, un assistant de service client. "
                "Tu aides les clients concernant leurs commandes et retours. "
                "Utilise les outils pour obtenir des informations fiables. "
                "N'invente jamais un statut, une date, un lien ou une information. "
                "Utilise uniquement les résultats retournés par les outils. "
                "Ne prétends jamais qu'un e-mail a été envoyé ou qu'un lien de suivi existe. "
                "Si une commande est expédiée, indique simplement qu'elle est expédiée. "
                "Si une commande est introuvable, explique-le clairement. "
                "Ne crée jamais de ticket sans demande explicite du client. "
                "Ne prétends jamais avoir créé un ticket si l'outil ne l'a pas confirmé. "
                "Ne promets aucune notification ou action qui n'existe pas dans le projet. "
                "Si une information manque, demande-la au client. "
                "Réponds en français avec des phrases simples."
            )
        },
        {
            "role": "user",
            "content": message
        }
    ]

    for tour in range(MAX_TOURS):
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            tools=available_tools,
            tool_choice="auto",
            temperature=0
        )

        assistant_message = response.choices[0].message

        if not assistant_message.tool_calls:
            return assistant_message.content or "Je n'ai pas pu produire une réponse."

        messages.append({
            "role": "assistant",
            "content": assistant_message.content or "",
            "tool_calls": [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments
                    }
                }
                for call in assistant_message.tool_calls
            ]
        })

        for call in assistant_message.tool_calls:
            name = call.function.name
            arguments = json.loads(call.function.arguments)

            result = execute_tool(
                name,
                arguments,
                ticket_authorized
            )

            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result, ensure_ascii=False)
            })

    return "La demande nécessite trop d'étapes. Veuillez reformuler votre question."
