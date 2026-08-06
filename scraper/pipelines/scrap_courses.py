from models.course import CourseCreate
from models.reunion import ReunionCreate
from pmu.endpoints import get_programme
from pmu.types.types import ProgrammeIdentifier
from service.course import create_course
from service.programme import get_not_scraped_programme_date
from service.reunion import create_reunion
import logging

logger = logging.getLogger(__name__)


def scrap_courses():
    logger.info("scrap_courses")
    programme_dates = get_not_scraped_programme_date()
    logger.info(f"{len(programme_dates)} programmes non scrapés")
    for programme_date in programme_dates:
        logger.info(f"scraping courses for {programme_date}")
        programme = get_programme(ProgrammeIdentifier(programme_date))
        reunions = programme['programme']['reunions']
        if reunions:
            logger.info(f"scraping {len(reunions)} reunions for {programme_date}")
        for reunion in reunions:
            logger.info(f"scraping reunion {reunion['numOfficiel']} for {programme_date}")
            reunion_number = reunion['numOfficiel']
            create_reunion(ReunionCreate(id=f"{programme_date}/R{reunion_number}", raw=reunion))
            courses = reunion['courses']
            logger.info(f"scraping {len(courses)} courses for {programme_date}")
            for course in courses:
                logger.info(f"scraping course {course['numExterne']} for {programme_date}")
                course_number = course['numExterne']
                create_course(CourseCreate(id=f"{programme_date}/R{reunion_number}/C{course_number}", raw=course))