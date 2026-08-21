from typing import TypeVar
from sqlmodel import Session, SQLModel

TModel = TypeVar("TModel", bound=SQLModel)

def upsert(model: type[TModel], payload: SQLModel, session: Session, *, commit: bool = True) -> TModel:
    """Insère ou met à jour une entité. `commit=False` permet de batcher un lot."""
    entity = model.model_validate(payload)
    merged = session.merge(entity)
    if commit:
        session.commit()
    return merged