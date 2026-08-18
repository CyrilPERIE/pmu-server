from fastapi import APIRouter, BackgroundTasks
from pmu.types.types import CourseIdentifier, ProgrammeIdentifier
from scraper.pipelines.recuperation.historize import historize as run_historize, HIGHEST_DATE, LOWEST_DATE
from service.course import get_active_courses_identifiers, get_courses, set_course_is_over
from service.deps import get_session
from service.participant import get_participants_by_course_identifier
from service.rapport import get_rapports_definitifs_ids
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scrap", tags=["scrap"])

@router.get("/historize")
def historize(background_tasks: BackgroundTasks, start_date: str | None = None, end_date: str | None = None) -> dict[str, str]:
    start = LOWEST_DATE
    end = HIGHEST_DATE
    if start_date and type(start_date) == str and start_date.isdigit() and len(start_date) == 8:
        start = ProgrammeIdentifier(start_date)
    if end_date and type(end_date) == str and end_date.isdigit() and len(end_date) == 8:
        end = ProgrammeIdentifier(end_date)
    background_tasks.add_task(run_historize, start, end)
    return {"message": "Historization started"}

@router.get("/refresh-inactive-courses")
def refresh_inactive_courses() -> dict[str, str]:
    with get_session() as session:
        rapports_definitifs_ids = get_rapports_definitifs_ids(session)
        unique_rapports_definitifs_ids = list[str](set[str]([rapport.split("-")[0] for rapport in rapports_definitifs_ids]))
        active_courses = get_active_courses_identifiers(session)
        str_active_courses = [str(course) for course in active_courses]
        logger.info(f"Found {len(str_active_courses)} active courses")
        count = 0
        for str_active_course in str_active_courses:
            if str_active_course in unique_rapports_definitifs_ids:
                set_course_is_over(CourseIdentifier(str_active_course), session)
                count += 1
        logger.info(f"Set {count} courses to over")
        return {"message": f"{count} courses set to over and {len(str_active_courses) - count} courses not set to over"}

@router.get("/courses-without-participants")
def courses_without_participants() -> dict[str, str]:
    print("courses_without_participants")
    with get_session() as session:
        courses = get_courses(session)
        courses_ids = [str(course) for course in courses]
        courses_without_participants = []
        for course_id in courses_ids:
            participants = get_participants_by_course_identifier(CourseIdentifier(course_id), session)
            if len(participants) == 0:
                courses_without_participants.append(course_id)
        return {"message": f"Found {len(courses_without_participants)} courses without participants: {courses_without_participants}"}