from models.combinaison import CombinaisonCreate, Combinaison
from sqlmodel import Session
from service.utils.crud import upsert

def create_combinaison(combinaison_create: CombinaisonCreate, session: Session) -> Combinaison:
    return upsert(Combinaison, combinaison_create, session)