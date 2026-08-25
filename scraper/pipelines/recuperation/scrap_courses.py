from models.course import CourseCreate
from models.reunion import ReunionCreate
from pmu.endpoints import get_programme
from pmu.types.types import ProgrammeIdentifier
from service.course import create_course
from service.utils.deps import get_session
from service.programme import get_not_scraped_programme_dates, set_programme_scraped
from service.reunion import create_reunion
import logging
from scraper.pipelines.utils.pipeline_decorator import log_scraper

logger = logging.getLogger(__name__)

@log_scraper
def scrap_courses() -> None:
    '''
    Récupération des courses pour tous les programmes disponibles en base de données et qui sont flagés `is_scraped==False`.\n
    Les courses récupérées sont créées en base et par défaut actives afin de permettre aux robots de récupération des paris de prendre à minima
    les rapports finaux.\n
    Une fois la récupération des courses actives terminées alors le programme passe en `is_scraped==True`\n
    '''
    logger.info("scrap_courses")
    with get_session() as session:
        programme_dates = get_not_scraped_programme_dates(session)
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
            reunion_id = f"{programme_date}/R{reunion_number}"
            with get_session() as session:
                create_reunion(ReunionCreate(id=reunion_id, raw=reunion, programme_id=programme_date), session)
            courses = reunion['courses']
            logger.info(f"scraping {len(courses)} courses for {programme_date}")

            for course in courses:
                logger.info(f"scraping course {course['numExterne']} for {programme_date}")
                course_number = course['numExterne']
                with get_session() as session:
                    create_course(CourseCreate(id=f"{reunion_id}/C{course_number}", raw=course, reunion_id=reunion_id), session)

        with get_session() as session:
            set_programme_scraped(ProgrammeIdentifier(programme_date), session)