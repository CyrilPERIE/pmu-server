from models.combinaison import CombinaisonCreate
from models.rapport import RapportCreate
from pmu.endpoints import get_course, get_combinaisons, get_rapports_definitifs
from pmu.utils import is_arrivee_definitive
from service.combinaison import create_combinaison
from service.course import get_active_courses, set_course_is_over
from service.deps import get_session
from service.rapport import create_rapport
import logging
logger = logging.getLogger(__name__)

def scrap_bet():
    logger.info("scrap_bet")
    with get_session() as session:
        active_courses = get_active_courses(session)
    logger.info(f"{len(active_courses)} active courses to scrap")
    for active_course in active_courses:
        combinaisons = get_combinaisons(active_course)
        course = get_course(active_course)
        if combinaisons is not None:
            for combinaison in combinaisons["combinaisons"]:
                with get_session() as session:
                    create_combinaison(CombinaisonCreate(id=f"{str(active_course)}-{combinaison['updateTime']}", raw=combinaison), session)
            logger.info(f"scraping course {active_course}")
            logger.info(f"course {active_course} is {'active' if is_arrivee_definitive else 'not active'}")

        if is_arrivee_definitive(course):
            logger.info(f"setting course {active_course} to over")
            with get_session() as session:
                course_over = set_course_is_over(active_course, session)
                logger.info(f"course {active_course} is over: {course_over.is_over}")
            logger.info(f"scraping rapports for {active_course}")
            rapports = get_rapports_definitifs(active_course)
            logger.info(f"scraping rapports for {active_course}")
            if rapports is not None:
                for rapport in rapports:
                    with get_session() as session:
                        type_pari = rapport["typePari"]
                        rapport_created = create_rapport(RapportCreate(id=f"{str(active_course)}-{type_pari}", raw=rapport), session)