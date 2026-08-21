from models.reunion import Reunion, ReunionCreate
from sqlmodel import Session
from service.utils.crud import upsert


def create_reunion(reunion_create: ReunionCreate, session: Session) -> None:
    return upsert(Reunion, reunion_create, session)