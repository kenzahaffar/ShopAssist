
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ORDERS_FILE = DATA_DIR / "orders.json"
TICKETS_FILE = DATA_DIR / "tickets.json"


def load_orders():
    with open(ORDERS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def consult_order_status(order_id: str):
    orders = load_orders()

    for order in orders:
        if order["order_id"] == order_id:
            return {
                "found": True,
                "order_id": order["order_id"],
                "product": order["product"],
                "status": order["status"]
            }

    return {
        "found": False,
        "message": "Commande introuvable."
    }


def check_return_eligibility(order_id: str):
    orders = load_orders()

    for order in orders:
        if order["order_id"] == order_id:

            if order["status"] != "delivered":
                return {
                    "order_id": order_id,
                    "eligible": False,
                    "reason": "La commande n'est pas encore livrée."
                }

            days = order["days_since_delivery"]

            if days <= 14:
                return {
                    "order_id": order_id,
                    "eligible": True,
                    "reason": "La commande est livrée depuis moins de 14 jours."
                }

            return {
                "order_id": order_id,
                "eligible": False,
                "reason": "Le délai de retour de 14 jours est dépassé."
            }

    return {
        "found": False,
        "message": "Commande introuvable."
    }


def create_support_ticket(
    order_id: str,
    reason: str,
    customer_requested: bool = False
):
    if not customer_requested:
        return {
            "created": False,
            "message": "Le client doit demander explicitement la création d'un ticket."
        }

    orders = load_orders()

    if not any(order["order_id"] == order_id for order in orders):
        return {
            "created": False,
            "message": "Commande introuvable."
        }

    if not reason.strip():
        return {
            "created": False,
            "message": "Le motif du ticket est obligatoire."
        }

    if TICKETS_FILE.exists():
        with open(TICKETS_FILE, "r", encoding="utf-8") as file:
            tickets = json.load(file)
    else:
        tickets = []

    ticket = {
        "ticket_id": f"T{len(tickets) + 1:03d}",
        "order_id": order_id,
        "reason": reason,
        "status": "open"
    }

    tickets.append(ticket)

    with open(TICKETS_FILE, "w", encoding="utf-8") as file:
        json.dump(tickets, file, indent=4, ensure_ascii=False)

    return {
        "created": True,
        "ticket": ticket
    }
