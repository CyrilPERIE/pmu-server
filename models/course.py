from sqlmodel import Field, SQLModel
from sqlalchemy import Column, JSON

class CourseBase(SQLModel):
    id: str = Field(unique=True, index=True, max_length=14, primary_key=True)
    raw: dict = Field(sa_column=Column(JSON))
    is_over: bool = Field(default=False)

class CourseCreate(CourseBase):
    pass

class Course(CourseBase, table=True):
    pass