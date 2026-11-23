
import json
from pathlib import Path
from collections import Counter

from app.classifier import classify_message


DOSSIER = Path(__file__).resolve().parent
FICHIER = DOSSIER / "dataset.json"


def evaluer():
    with open(FICHIER, "r", encoding="utf-8") as file:
        dataset = json.load(file)

    total = len(dataset)
    correct = 0
    resultats = []

    print("\n===== EVALUATION SHOPASSIST =====\n")

    for exemple in dataset:
        message = exemple["message"]
        attendu = exemple["expected"]

        try:
            prediction = classify_message(message)
            obtenu = prediction.category.value

        except Exception as error:
            obtenu = "erreur"
            print("Erreur :", error)

        resultat = obtenu == attendu

        if resultat:
            correct += 1

        resultats.append({
            "attendu": attendu,
            "obtenu": obtenu,
            "correct": resultat
        })

        print("Message :", message)
        print("Attendu :", attendu)
        print("Prédit :", obtenu)
        print("Résultat :", "CORRECT" if resultat else "INCORRECT")
        print("-" * 45)

    accuracy = correct / total if total else 0

    print("\n===== RESULTATS =====")
    print("Total des messages :", total)
    print("Prédictions correctes :", correct)
    print("Prédictions incorrectes :", total - correct)
    print("Accuracy :", f"{accuracy * 100:.2f}%")

    print("\n===== ERREURS PAR CATEGORIE =====")

    erreurs = Counter(
        resultat["attendu"]
        for resultat in resultats
        if not resultat["correct"]
    )

    if erreurs:
        for categorie, nombre in erreurs.items():
            print(categorie, ":", nombre)
    else:
        print("Aucune erreur.")

    return accuracy


if __name__ == "__main__":
    evaluer()
