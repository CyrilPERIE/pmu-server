from sqlmodel import Field, SQLModel
from sqlalchemy import Column, JSON

class ProgrammeBase(SQLModel):
    id: str = Field(max_length=14, primary_key=True)
    raw: dict = Field(sa_column=Column(JSON))
    is_scraped: bool = Field(default=False)

class ProgrammeCreate(ProgrammeBase):
    pass

class Programme(ProgrammeBase, table=True):
    pass
