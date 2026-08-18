from typing import List
from models.participant import ParticipantCreate, Participant
from pmu.types.types import CourseIdentifier
from sqlmodel import Session, select


def create_participant(participant_create: ParticipantCreate, session: Session) -> None:
    participant = Participant.model_validate(participant_create)
    session.merge(participant)
    session.commit()
    return participant

def get_participants_by_course_identifier(course_identifier: CourseIdentifier, session: Session) -> List[Participant]:
    return session.exec(select(Participant).where(Participant.id.like(f"{course_identifier}/%"))).all()