from models.reunion import Reunion, ReunionCreate
from sqlmodel import Session


def create_reunion(reunion_create: ReunionCreate, session: Session) -> None:
    reunion = Reunion.model_validate(reunion_create)
    session.merge(reunion)
    session.commit()
    return reunion