from typing import List
from models.programme import ProgrammeCreate
from sqlmodel import Session, select
from models.programme import Programme


def create_programme(programme_create: ProgrammeCreate, session: Session) -> Programme:
    programme = Programme.model_validate(programme_create)
    session.merge(programme)
    session.commit()
    return programme

def get_not_scraped_programme_dates(session: Session) -> List[str]:
    return session.exec(select(Programme.id).where(Programme.is_scraped == False)).all()
    