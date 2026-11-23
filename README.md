
# ShopAssist
### Assistant intelligent pour le service client d'une boutique en ligne

## 1. Présentation

ShopAssist est un assistant intelligent destiné à aider une boutique en ligne à traiter les messages de ses clients.

Il utilise un modèle d'intelligence artificielle pour comprendre les demandes et un agent pour consulter les commandes, vérifier les conditions de retour et créer des tickets de support.

## 2. Fonctionnalités

Le projet propose quatre fonctionnalités principales :

- **Classification des messages :** reconnaître cinq catégories : livraison, paiement, commande, retour et autre.
- **Consultation des commandes :** rechercher une commande et afficher son état.
- **Vérification des retours :** vérifier si une commande respecte le délai de retour de 14 jours.
- **Création de tickets :** créer un ticket de support uniquement si le client le demande explicitement et si sa commande existe.

## 3. Technologies utilisées

- Python
- FastAPI
- Groq API
- Pydantic
- JSON
- Pytest

## 4. Structure du projet

```text
ShopAssist/
├── app/
│   ├── main.py
│   ├── classifier.py
│   ├── agent.py
│   ├── tools.py
│   ├── schemas.py
│   └── config.py
├── data/
│   ├── orders.json
│   └── tickets.json
├── evaluation/
│   ├── dataset.json
│   ├── evaluer.py
│   └── comparer_prompts.py
├── tests/
│   └── test_tools.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md