from models.rapport import RapportCreate
from pmu.endpoints import get_course, get_rapports_definitifs
from pmu.utils import is_course_terminée
from service.course import get_active_courses, set_course_is_over
from service.rapport import create_rapport
import logging
logger = logging.getLogger(__name__)

def scrap_bet():
    logger.info("scrap_bet")
    active_courses = get_active_courses()
    logger.info(f"{len(active_courses)} active courses to scrap")
    for active_course in active_courses:
        logger.info(f"scraping rapports for {active_course}")
        rapports = get_rapports_definitifs(active_course)
        logger.info(f"scraping {len(rapports)} rapports for {active_course}")
        create_rapport(RapportCreate(id=str(active_course), raw=rapports))
        course = get_course(active_course)
        logger.info(f"scraping course {active_course}")
        is_course_active = is_course_terminée(course)
        logger.info(f"course {active_course} is {'active' if is_course_active else 'not active'}")
        if not is_course_active:
            logger.info(f"setting course {active_course} to over")
            set_course_is_over(active_course)