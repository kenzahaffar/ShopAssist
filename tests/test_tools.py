import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.tools import create_support_ticket


def test_refuser_ticket_commande_inexistante():
    resultat = create_support_ticket(
        "C9999",
        "Problème de livraison",
        customer_requested=True
    )

    assert resultat["created"] is False
    assert resultat["message"] == "Commande introuvable."


def test_refuser_ticket_sans_demande_explicite():
    resultat = create_support_ticket(
        "C1001",
        "Problème de livraison",
        customer_requested=False
    )

    assert resultat["created"] is False
    assert "explicitement" in resultat["message"]


def test_creer_ticket_valide(tmp_path, monkeypatch):
    import app.tools as tools

    monkeypatch.setattr(
        tools,
        "TICKETS_FILE",
        tmp_path / "tickets.json"
    )

    resultat = tools.create_support_ticket(
        "C1001",
        "Retard de livraison",
        customer_requested=True
    )

    assert resultat["created"] is True
    assert resultat["ticket"]["order_id"] == "C1001"
    assert resultat["ticket"]["reason"] == "Retard de livraison"
    assert resultat["ticket"]["status"] == "open"