from typing import List
from models.programme import ProgrammeCreate
from pmu.types.types import ProgrammeIdentifier
from sqlmodel import Session, select, update
from models.programme import Programme
from service.utils.crud import upsert

def create_programme(programme_create: ProgrammeCreate, session: Session) -> Programme:
    return upsert(Programme, programme_create, session)

def get_not_scraped_programme_dates(session: Session) -> List[str]:
    return session.exec(select(Programme.id).where(Programme.is_scraped == False)).all()

def set_programme_scraped(programme_identifier: ProgrammeIdentifier, session: Session) -> None:
    session.exec(update(Programme).where(Programme.id == str(programme_identifier)).values(is_scraped=True))
    session.commit()