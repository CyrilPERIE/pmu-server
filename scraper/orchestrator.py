from scraper.pipelines import scrap_bet, scrap_courses, scrap_participants, scrap_programmes
import logging

logger = logging.getLogger(__name__)

def every_midnight():
    logging.info("every_midnight")
    scrap_programmes.scrap_programmes()
    scrap_courses.scrap_courses()
    scrap_participants.scrap_participants()

def every_five_minutes():
    logging.info("every_five_minutes")
    scrap_bet.scrap_bet()