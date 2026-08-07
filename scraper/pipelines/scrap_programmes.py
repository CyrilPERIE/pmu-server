from datetime import date
from models.programme import ProgrammeCreate
from pmu.endpoints import get_programme
from pmu.types.types import ProgrammeIdentifier
from pmu.utils import date_to_programme_date
from service.deps import get_session
from service.programme import create_programme
import logging

logger = logging.getLogger(__name__)

def scrap_programmes():
    logger.info("scrap_programmes")
    programme_identifier = ProgrammeIdentifier(date_to_programme_date(date.today()))
    programmes = get_programme(programme_identifier)
    programmes_disponibles = programmes["programme"]["datesProgrammesDisponibles"]
    logger.info(f"{len(programmes_disponibles)} dates de programmes disponibles")
    if programmes_disponibles:
        for programme_date in programmes_disponibles:
            logger.info(f"scraping programme for {programme_date}")
            programme = get_programme(ProgrammeIdentifier(programme_date))
            with get_session() as session:
                create_programme(ProgrammeCreate(id=programme_date, raw=programme), session)
    ## Stockage des dates des programmes disponibles
    logger.info("scrap_programmes finished !")
    return programmes