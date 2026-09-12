from pmu.types.types import ProgrammeIdentifier
from service.utils.deps import get_session
from service.reunion import get_reunions_between_dates
import pandas as pd


def load_reunions(start_date: ProgrammeIdentifier, end_date: ProgrammeIdentifier) -> pd.DataFrame:
    """
    Charge les programmes depuis la base de données.
    """
    session = get_session()
    with session:
        programme_ids = get_reunions_between_dates(session, start_date, end_date)
        return pd.DataFrame([programme.model_dump() for programme in programme_ids])