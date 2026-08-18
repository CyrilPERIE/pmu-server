from typing import List
from models.programme import ProgrammeCreate
from pmu.types.types import ProgrammeIdentifier
from sqlmodel import Session, select, update
from models.programme import Programme


def create_programme(programme_create: ProgrammeCreate, session: Session) -> Programme:
    programme = Programme.model_validate(programme_create)
    session.merge(programme)
    session.commit()
    return programme

def get_not_scraped_programme_dates(session: Session) -> List[str]:
    return session.exec(select(Programme.id).where(Programme.is_scraped == False)).all()

def set_programme_scraped(programme_identifier: ProgrammeIdentifier, session: Session) -> None:
    session.exec(update(Programme).where(Programme.id == str(programme_identifier)).values(is_scraped=True))
    session.commit()

def get_programme_by_identifier(programme_identifier: ProgrammeIdentifier, session: Session) -> Programme:
    return session.exec(select(Programme).where(Programme.id == str(programme_identifier))).first()

def get_programmes(session: Session, limit: int = None, offset: int = None) -> List[Programme]:
    return session.exec(select(Programme).limit(limit).offset(offset)).all()

def get_programme_identifiers(session: Session) -> List[ProgrammeIdentifier]:
    return [ProgrammeIdentifier(programme_id) for programme_id in session.exec(select(Programme.id)).all()]