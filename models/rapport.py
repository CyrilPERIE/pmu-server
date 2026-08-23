from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, JSON
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.course import Course

class RapportBase(SQLModel):
    id: str = Field(max_length=100, primary_key=True)
    raw: dict = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class RapportCreate(RapportBase):
    course_id: str

class Rapport(RapportBase, table=True):
    course_id: str = Field(foreign_key="course.id")
    course: "Course" = Relationship(back_populates="rapports")