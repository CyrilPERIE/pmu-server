"""Couverture des courses par leurs entités filles.

Permet de répondre à « quelles courses ont effectivement des participants et des
rapports définitifs ? » sans rapatrier les JSON.
"""

import pandas as pd

from dataset.utils import DATE_WINDOW, load_sql
from pmu.types.types import ProgrammeIdentifier

ENTITES_FILLES = ("participant", "rapport")

COUVERTURE_QUERY = "\nunion all\n".join(
    f"""
select '{entite}' as entite, course_id, count(*) as nombre
from {entite}
where {DATE_WINDOW}
group by 1, 2
"""
    for entite in ENTITES_FILLES
)


def load_couverture_courses(
    start_date: ProgrammeIdentifier, end_date: ProgrammeIdentifier
) -> pd.DataFrame:
    """Nombre de participants et de rapports rattachés à chaque course."""
    frame = load_sql(COUVERTURE_QUERY, start_date, end_date)
    return frame.pivot(index="course_id", columns="entite", values="nombre")
