from models.combinaison import CombinaisonCreate, Combinaison
from sqlmodel import Session

def create_combinaison(combinaison_create: CombinaisonCreate, session: Session) -> Combinaison:
    combinaison = Combinaison.model_validate(combinaison_create)
    session.merge(combinaison)
    session.commit()
    return combinaison