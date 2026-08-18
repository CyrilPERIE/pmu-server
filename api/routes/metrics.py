from fastapi import APIRouter
from service.deps import get_session
from service.course import count_active_courses, count_courses, count_inactive_courses
from service.rapport import count_rapports

router = APIRouter(prefix="/metrics", tags=["metrics"])

@router.get("/")
def get_metrics() -> dict[str, int]:
    with get_session() as session:
        res_count_courses = count_courses(session)
        res_count_active_courses = count_active_courses(session)
        res_count_inactive_courses = count_inactive_courses(session)
        res_count_rapports = count_rapports(session)
        return {"count_courses": res_count_courses, "count_active_courses": res_count_active_courses, "count_inactive_courses": res_count_inactive_courses, "count_rapports": res_count_rapports}