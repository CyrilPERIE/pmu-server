from models.course import Course
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

def update_count_courses(session: Session) -> int:
    count = session.exec(select(func.count(Course.id))).one()
    print(count)
    metric = Metrics(type=MetricType.COUNT, value=count, name="count_courses")
    return create_metric(metric, session)