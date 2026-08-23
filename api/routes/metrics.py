from models.metrics import Metrics
from service import metrics
from service.utils.deps import get_session
from fastapi import APIRouter

router = APIRouter(prefix="/metrics", tags=["metrics"])

@router.get("/")
def get_metrics() -> list[Metrics]:
    with get_session() as session:
        return metrics.get_metrics(session)

@router.get("/update")
def update_metrics() -> None:
    metrics.update_metrics()
    return {"message": "Metrics updated"}
