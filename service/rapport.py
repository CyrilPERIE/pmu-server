from models.rapport import Rapport, RapportCreate
from sqlmodel import Session, select, func
from typing import List

def create_rapport(rapport_create: RapportCreate, session: Session) -> Rapport:
    rapport = Rapport.model_validate(rapport_create)
    session.merge(rapport)
    session.commit()
    return rapport

def get_rapports_definitifs_ids(session: Session) -> List[Rapport]:
    return session.exec(select(Rapport.id)).all()

def count_rapports(session: Session) -> int:
    return session.exec(select(func.count(Rapport.id))).first()