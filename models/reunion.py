from sqlmodel import Field, SQLModel
from sqlalchemy import Column, JSON

class ReunionBase(SQLModel):
    id: str = Field(max_length=14, primary_key=True)
    raw: dict = Field(sa_column=Column(JSON))

class ReunionCreate(ReunionBase):
    pass

class Reunion(ReunionBase, table=True):
    pass