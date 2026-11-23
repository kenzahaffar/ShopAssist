from enum import Enum
from pydantic import BaseModel, Field


class Category(str, Enum):
    LIVRAISON = "livraison"
    PAIEMENT = "paiement"
    COMMANDE = "commande"
    RETOUR = "retour"
    AUTRE = "autre"


class ClassificationResult(BaseModel):
    category: Category
    confidence: float = Field(ge=0, le=1)
    justification: str = Field(min_length=1)
    needs_review: bool