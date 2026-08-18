from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, JSON
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.course import Course

class ParticipantBase(SQLModel):
    id: str = Field(max_length=20, primary_key=True)
    raw: dict = Field(sa_column=Column(JSON))

class ParticipantCreate(ParticipantBase):
    course_id: str  

class Participant(ParticipantBase, table=True):
    course_id: str = Field(foreign_key="course.id")
    course: "Course" = Relationship(back_populates="participants")