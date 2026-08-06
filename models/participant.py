from sqlmodel import Field, SQLModel
from sqlalchemy import Column, JSON

class ParticipantBase(SQLModel):
    id: str = Field(unique=True, index=True, max_length=20, primary_key=True)
    raw: dict = Field(sa_column=Column(JSON))

class ParticipantCreate(ParticipantBase):
    pass

class Participant(ParticipantBase, table=True):
    pass