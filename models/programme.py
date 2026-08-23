from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, JSON
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.reunion import Reunion

class ProgrammeBase(SQLModel):
    id: str = Field(max_length=14, primary_key=True)
    raw: dict = Field(sa_column=Column(JSON))
    is_scraped: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ProgrammeCreate(ProgrammeBase):
    pass

class Programme(ProgrammeBase, table=True):
    
    reunions: list["Reunion"] = Relationship(back_populates="programme")
