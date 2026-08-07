from models.participant import ParticipantCreate
from pmu.endpoints import get_course, get_participants
from service.deps import get_session
from service.course import get_daily_courses
from service.participant import create_participant
import logging
logger = logging.getLogger(__name__)

def scrap_participants():
    logger.info("scrap_participants")
    with get_session() as session:
        course_identifiers = get_daily_courses(session)
    logger.info(f"{len(course_identifiers)} courses to scrap")
    for course_identifier in course_identifiers:
        logger.info(f"scraping course {course_identifier}")
        res = get_participants(course_identifier)
        logger.info(f"scraping {len(res['participants'])} participants for {course_identifier}")
        participants = res['participants']
        for participant in participants:
            logger.info(f"scraping participant {participant['numPmu']} for {course_identifier}")
            with get_session() as session:
                create_participant(ParticipantCreate(id=f"{str(course_identifier)}/P{participant['numPmu']}", raw=participant), session)