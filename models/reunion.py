from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, JSON
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.course import Course
    from models.programme import Programme

class ReunionBase(SQLModel):
    id: str = Field(max_length=14, primary_key=True)
    raw: dict = Field(sa_column=Column(JSON))

class ReunionCreate(ReunionBase):
    programme_id: str

class Reunion(ReunionBase, table=True):
    programme_id: str = Field(foreign_key="programme.id")
    programme: "Programme" = Relationship(back_populates="reunions")
    courses: list["Course"] = Relationship(back_populates="reunion")