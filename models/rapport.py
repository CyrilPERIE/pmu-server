from sqlmodel import Field, SQLModel
from sqlalchemy import Column, JSON

class RapportBase(SQLModel):
    id: str = Field(unique=True, index=True, max_length=14, primary_key=True)
    raw: dict = Field(sa_column=Column(JSON))

class RapportCreate(RapportBase):
    pass

class Rapport(RapportBase, table=True):
    pass