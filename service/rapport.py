from models.rapport import Rapport, RapportCreate
from sqlmodel import Session

def create_rapport(rapport_create: RapportCreate, session: Session) -> Rapport:
    rapport = Rapport.model_validate(rapport_create)
    session.merge(rapport)
    session.commit()
    return rapport