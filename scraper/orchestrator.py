from scraper.pipelines.recuperation import scrap_bet, scrap_courses, scrap_participants, scrap_programmes
import logging

from scraper.pipelines.recuperation.update_metrics import update_metrics
from service import metrics

logger = logging.getLogger(__name__)

def every_day() -> None:
    logger.info("every_day")
    scrap_programmes.scrap_programmes()
    scrap_courses.scrap_courses()
    scrap_participants.scrap_participants()

def every_five_minutes() -> None:
    logger.info("every_five_minutes")
    scrap_bet.scrap_bet()
    update_metrics()