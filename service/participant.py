from models.participant import ParticipantCreate, Participant
from sqlmodel import Session


def create_participant(participant_create: ParticipantCreate, session: Session) -> None:
    participant = Participant.model_validate(participant_create)
    session.merge(participant)
    session.commit()
    return participant