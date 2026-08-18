from datetime import date
from models.programme import ProgrammeCreate
from pmu.endpoints import get_programme
from pmu.types.types import ProgrammeIdentifier
from pmu.utils import date_to_programme_date
from service.deps import get_session
from service.programme import create_programme
import logging
logger = logging.getLogger(__name__)

def scrap_past_programmes(programme_identifier: ProgrammeIdentifier) -> None:
    logger.info("scrap_programmes")
    programme = get_programme(programme_identifier)
    if programme:
        with get_session() as session:
            create_programme(ProgrammeCreate(id=str(programme_identifier), raw=programme), session)