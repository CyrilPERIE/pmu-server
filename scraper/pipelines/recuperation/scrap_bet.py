import datetime
from models.combinaison import CombinaisonCreate
from models.rapport import RapportCreate
from pmu.endpoints import get_course, get_combinaisons, get_rapports_definitifs
from pmu.utils import is_arrivee_definitive, is_course_annulee
from service.combinaison import create_combinaison
from service.course import get_active_courses_identifiers, set_course_is_over
from service.deps import get_session
from service.rapport import create_rapport
import logging

logger = logging.getLogger(__name__)


def scrap_bet() -> None:
    """
    Récupération des côtes, de l'argent misé pour les différentes courses actives recensées dans ma base de données.\n
    Cela pourrait permettre des approches supplémentaires dans la conception de modèles statistiques et prédictifs
    """
    logger.info("scrap_bet")
    with get_session() as session:
        ## Récupération des courses actives dans la base de données
        active_courses = get_active_courses_identifiers(session)
    logger.info(f"{len(active_courses)} active courses to scrap")
    for active_course in active_courses:
        '''
        Récupération de données contextuelles pour la suite.
        -- Combinaisons: Côtes par pari, mises en jeu
        -- Course: Récupération en l'état de la course
        '''
        combinaisons = get_combinaisons(active_course)
        course = get_course(active_course)
        '''
        Stockage de toutes les combinaisons dans la base de données
        '''
        if combinaisons is not None:
            for combinaison in combinaisons["combinaisons"]:
                with get_session() as session:
                    create_combinaison(CombinaisonCreate(id=f"{str(active_course)}-{combinaison['updateTime']}", raw=combinaison, course_id=str(active_course)), session)
            logger.info(f"scraping course {active_course}")
            logger.info(f"course {active_course} is {'active' if is_arrivee_definitive else 'not active'}")

        '''
        Si la course n'est plus d'actualité alors on la passe en inactive dans la base de données et on récupère les rapports définitifs.
        '''
        if is_arrivee_definitive(course) or is_course_annulee(course) or active_course.is_in_past_days():
            logger.info(f"setting course {active_course} to over")
            with get_session() as session:
                course_over = set_course_is_over(active_course, session)
                logger.info(f"course {active_course} is over: {course_over.is_over}")

            rapports = get_rapports_definitifs(active_course)
            logger.info(f"scraping rapports for {active_course}")
            if rapports is not None:
                for rapport in rapports:
                    with get_session() as session:
                        type_pari = rapport["typePari"]
                        create_rapport(RapportCreate(id=f"{str(active_course)}-{type_pari}", raw=rapport, course_id=str(active_course)), session)