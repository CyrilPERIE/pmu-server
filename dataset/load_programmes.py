import pandas as pd
from service.programme import get_programme_dates_between_dates
from service.utils.deps import get_session
from pmu.types.types import ProgrammeIdentifier

def load_programmes(start_date: ProgrammeIdentifier, end_date: ProgrammeIdentifier) -> pd.DataFrame:
    """
    Charge les programmes depuis la base de données.
    """
    session = get_session()
    with session:
        programme_ids = get_programme_dates_between_dates(session, start_date, end_date)
        return pd.DataFrame([programme.model_dump() for programme in programme_ids])