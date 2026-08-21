from models.rapport import Rapport, RapportCreate
from sqlmodel import Session
from service.utils.crud import upsert

def create_rapport(rapport_create: RapportCreate, session: Session) -> Rapport:
    return upsert(Rapport, rapport_create, session)