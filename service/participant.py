from models.participant import ParticipantCreate, Participant
from sqlmodel import Session
from service.utils.crud import upsert


def create_participant(participant_create: ParticipantCreate, session: Session) -> None:
    return upsert(Participant, participant_create, session)