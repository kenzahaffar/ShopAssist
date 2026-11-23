import json
from pathlib import Path

from groq import Groq
from app.config import GROQ_API_KEY, GROQ_MODEL


DOSSIER = Path(__file__).resolve().parent
FICHIER = DOSSIER / "dataset.json"

PROMPT_V1 = """
Tu es un assistant de service client pour une boutique en ligne.

Classe le message dans une seule catégorie :
livraison, paiement, commande, retour ou autre.

Retourne uniquement un JSON avec les champs :
category, confidence, justification, needs_review.

Le message est : {message}
"""

PROMPT_V2 = """
Tu es un classificateur de messages pour une boutique en ligne.

Choisis une seule catégorie parmi :
livraison, paiement, commande, retour, autre.

Règles :
- Une question sur l'état, la confirmation ou la modification d'une commande
  appartient à la catégorie commande.
- Une question sur un colis, un livreur, un retard ou une date de livraison
  appartient à la catégorie livraison.
- Une question sur une carte bancaire, une facture ou un paiement
  appartient à la catégorie paiement.
- Une demande de remboursement, d'échange ou de retour
  appartient à la catégorie retour.
- Une salutation ou une demande vague appartient à la catégorie autre.

Exemples :
- Où est ma commande C1001 ? -> commande
- Mon colis n'est pas arrivé. -> livraison
- Ma carte bancaire est refusée. -> paiement
- Je veux un remboursement. -> retour
- Bonjour, comment allez-vous ? -> autre

Retourne uniquement un JSON valide avec exactement ces champs :
category, confidence, justification, needs_review.

confidence doit être un nombre entre 0 et 1.
needs_review doit être un booléen.

Si le message est ambigu, choisis autre et needs_review=true.

Message à classer : {message}
"""


def classifier_avec_prompt(client, prompt, message):
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "user", "content": prompt.format(message=message)}
        ],
        temperature=0
    )

    contenu = response.choices[0].message.content

    if not contenu:
        raise ValueError("Réponse vide.")

    debut = contenu.find("{")
    fin = contenu.rfind("}")

    if debut == -1 or fin == -1:
        raise ValueError("Réponse JSON introuvable.")

    resultat = json.loads(contenu[debut:fin + 1])
    categorie = resultat.get("category")

    categories_valides = [
        "livraison", "paiement", "commande", "retour", "autre"
    ]

    if categorie not in categories_valides:
        raise ValueError("Catégorie invalide.")

    return categorie


def evaluer_prompt(client, dataset, nom, prompt):
    correct = 0
    erreurs = 0

    print(f"\n===== {nom} =====")

    for exemple in dataset:
        message = exemple["message"]
        attendu = exemple["expected"]

        try:
            obtenu = classifier_avec_prompt(client, prompt, message)
        except Exception as error:
            obtenu = "erreur"
            erreurs += 1
            print("Erreur :", error)

        if obtenu == attendu:
            correct += 1

        print("Message :", message)
        print("Attendu :", attendu)
        print("Prédit :", obtenu)
        print("Résultat :", "CORRECT" if obtenu == attendu else "INCORRECT")
        print("-" * 40)

    accuracy = correct / len(dataset) if dataset else 0

    print(f"Résultats {nom} :")
    print("Messages :", len(dataset))
    print("Corrects :", correct)
    print("Erreurs techniques :", erreurs)
    print("Accuracy :", f"{accuracy * 100:.2f}%")

    return accuracy


def main():
    if not GROQ_API_KEY:
        raise ValueError("La clé API Groq est manquante dans le fichier .env.")

    with open(FICHIER, "r", encoding="utf-8") as file:
        dataset = json.load(file)

    client = Groq(api_key=GROQ_API_KEY)

    score_v1 = evaluer_prompt(client, dataset, "PROMPT V1", PROMPT_V1)
    score_v2 = evaluer_prompt(client, dataset, "PROMPT V2", PROMPT_V2)

    print("\n===== COMPARAISON FINALE =====")
    print("Prompt V1 :", f"{score_v1 * 100:.2f}%")
    print("Prompt V2 :", f"{score_v2 * 100:.2f}%")

    difference = (score_v2 - score_v1) * 100
    print("Différence :", f"{difference:+.2f} points")

    if difference > 0:
        print("Conclusion : le prompt V2 donne de meilleurs résultats.")
    elif difference < 0:
        print("Conclusion : le prompt V1 donne de meilleurs résultats.")
    else:
        print("Conclusion : les deux prompts donnent le même résultat.")


if __name__ == "__main__":
    main()