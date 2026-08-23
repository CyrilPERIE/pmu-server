from models.course import Course
from models.programme import Programme
from models.reunion import Reunion
from service.utils.crud import upsert
from service.utils.deps import get_session
from sqlmodel import Session, select
from sqlalchemy import func
from models.metrics import MetricType, Metrics

def get_metrics(session: Session) -> list[Metrics]:
    return session.exec(select(Metrics)).all()

def create_metric(metric: Metrics, session: Session) -> Metrics:
    return upsert(Metrics, metric, session)

def update_metrics() -> None:
    with get_session() as session:
        update_count_courses(session)
        update_count_reunions(session)
        update_count_programmes(session)
        update_count_courses_over(session)
        update_count_courses_incoming(session)
        update_count_mean_courses_by_programme(session)

def update_count_courses(session: Session) -> int:
    count = session.exec(select(func.count(Course.id))).one()
    metric = Metrics(type=MetricType.COUNT, value=count, name="Nombre de courses récupérées")
    return create_metric(metric, session)

def update_count_programmes(session: Session) -> int:
    count = session.exec(select(func.count(Programme.id))).one()
    metric = Metrics(type=MetricType.COUNT, value=count, name="Nombre de programmes récupérés")
    return create_metric(metric, session)

def update_count_reunions(session: Session) -> int:
    count = session.exec(select(func.count(Reunion.id))).one()
    metric = Metrics(type=MetricType.COUNT, value=count, name="Nombre de réunions récupérées")
    return create_metric(metric, session)

def update_count_courses_over(session: Session) -> int:
    count = session.exec(select(func.count(Course.id)).where(Course.is_over == True)).one()
    metric = Metrics(type=MetricType.COUNT, value=count, name="Nombre de courses terminées")
    return create_metric(metric, session)

def update_count_courses_incoming(session: Session) -> int:
    count = session.exec(select(func.count(Course.id)).where(Course.is_over == False)).one()
    metric = Metrics(type=MetricType.COUNT, value=count, name="Nombre de courses en cours de récupération")
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
    metric = Metrics(type=MetricType.COUNT, value=count, name="Nombre moyen de courses par jour")
    return create_metric(metric, session)

