from models.participant import ParticipantCreate
from pmu.endpoints import get_course
from service.course import get_daily_courses
from service.participant import create_participant
import logging
logger = logging.getLogger(__name__)

def scrap_participants():
    logger.info("scrap_participants")
    course_identifiers = get_daily_courses()
    logger.info(f"{len(course_identifiers)} courses to scrap")
    for course_identifier in course_identifiers:
        logger.info(f"scraping course {course_identifier}")
        course = get_course(course_identifier)
        logger.info(f"scraping {len(course['participants'])} participants for {course_identifier}")
        participants = course['participants']
        for participant in participants:
            logger.info(f"scraping participant {participant['id']} for {course_identifier}")
            create_participant(ParticipantCreate(id=f"{str(course_identifier)}/P{participant['id']}", raw=participant))