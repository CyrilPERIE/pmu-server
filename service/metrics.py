from models.combinaison import Combinaison
from models.course import Course
from models.programme import Programme
from models.reunion import Reunion
from models.participant import Participant
from service.utils.crud import upsert
from sqlmodel import Session, select
from sqlalchemy import func
from models.metrics import MetricType, Metrics

def get_metrics(session: Session) -> list[Metrics]:
    return session.exec(select(Metrics)).all()

def create_metric(metric: Metrics, session: Session) -> Metrics:
    return upsert(Metrics, metric, session)

def update_count_combinaisons(session: Session) -> int:
    count = session.exec(select(func.count(Combinaison.id))).one()
    metric = Metrics(type=MetricType.COUNT, value=count, name="Nombre de combinaisons récupérées")
    return create_metric(metric, session)

def update_count_courses(session: Session) -> int:
    count = session.exec(select(func.count(Course.id))).one()
    metric = Metrics(type=MetricType.COUNT, value=count, name="Nombre de courses récupérées")
    return create_metric(metric, session)

def update_count_courses_incoming(session: Session) -> int:
    count = session.exec(select(func.count(Course.id)).where(Course.is_over == False)).one()
    metric = Metrics(type=MetricType.COUNT, value=count, name="Nombre de courses en cours de récupération")
    return create_metric(metric, session)

def update_count_courses_over(session: Session) -> int:
    count = session.exec(select(func.count(Course.id)).where(Course.is_over == True)).one()
    metric = Metrics(type=MetricType.COUNT, value=count, name="Nombre de courses terminées")
    return create_metric(metric, session)

def update_count_participants(session: Session) -> int:
    count = session.exec(select(func.count(Participant.id))).one()
    metric = Metrics(type=MetricType.COUNT, value=count, name="Nombre de participants récupérés")
    return create_metric(metric, session)

def update_count_programmes(session: Session) -> int:
    count = session.exec(select(func.count(Programme.id))).one()
    metric = Metrics(type=MetricType.COUNT, value=count, name="Nombre de programmes récupérés")
    return create_metric(metric, session)

def update_count_reunions(session: Session) -> int:
    count = session.exec(select(func.count(Reunion.id))).one()
    metric = Metrics(type=MetricType.COUNT, value=count, name="Nombre de réunions récupérées")
    return create_metric(metric, session)

def update_count_mean_courses_by_programme(session: Session) -> int:
    courses_by_programme = (
        select(
            Reunion.programme_id,
            func.count(Course.id).label("course_count")
        )
        .join(Course, Course.reunion_id == Reunion.id)
        .group_by(Reunion.programme_id)
        .subquery()
    )
    count = session.exec(
        select(func.avg(courses_by_programme.c.course_count))
    ).one()
    metric = Metrics(type=MetricType.COUNT, value=count, name="Nombre moyen de courses par programme")
    return create_metric(metric, session)

def update_count_mean_participants_by_course(session: Session) -> int:
    participants_by_course = (
        select(
            Course.id,
            func.count(Participant.id).label("participant_count")
        )
        .join(Participant, Participant.course_id == Course.id)
        .group_by(Course.id)
    )
    count = session.exec(
        select(func.avg(participants_by_course.c.participant_count))
    ).one()
    metric = Metrics(type=MetricType.COUNT, value=count, name="Nombre moyen de participants par course")
    return create_metric(metric, session)

def update_count_mean_reunions_by_programme(session: Session) -> int:
    reunions_by_programme = (
        select(
            Programme.id,
            func.count(Reunion.id).label("reunion_count")
        )
        .join(Reunion, Reunion.programme_id == Programme.id)
        .group_by(Programme.id)
        .subquery()
    )
    count = session.exec(
        select(func.avg(reunions_by_programme.c.reunion_count))
    ).one()
    metric = Metrics(type=MetricType.COUNT, value=count, name="Nombre moyen de réunions par programme")
    return create_metric(metric, session)

def update_lowest_year_programme(session: Session) -> int:
    programmes_ids = session.exec(select(Programme.id)).all()
    programmes_years = [int(programmes_id[4:]) for programmes_id in programmes_ids]
    lowest = min(programmes_years)
    metric = Metrics(type=MetricType.COUNT, value=lowest, name="Année la plus ancienne des programmes")
    return create_metric(metric, session)
