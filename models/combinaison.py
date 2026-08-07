from sqlmodel import Field, SQLModel
from sqlalchemy import Column, JSON

class CombinaisonBase(SQLModel):
    id: str = Field(max_length=32, primary_key=True)
    raw: dict = Field(sa_column=Column(JSON))

class CombinaisonCreate(CombinaisonBase):
    pass

class Combinaison(CombinaisonBase, table=True):
    pass