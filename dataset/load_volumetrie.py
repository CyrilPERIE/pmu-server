"""Volumétrie quotidienne de chaque entité collectée.

Une seule requête, en union, permet de comparer les rythmes de collecte des
programmes, réunions, courses, participants, rapports et combinaisons.
"""

import pandas as pd

from dataset.utils import DATE_WINDOW, PROGRAMME_DATE, load_sql
from pmu.types.types import ProgrammeIdentifier

ENTITES = ("programme", "reunion", "course", "participant", "rapport")

VOLUMETRIE_QUERY = "\nunion all\n".join(
    f"""
select
    '{entite}' as entite,
    ({PROGRAMME_DATE})::timestamp as date_programme,
    count(*) as nombre
from {entite}
where {DATE_WINDOW}
group by 1, 2
"""
    for entite in ENTITES
)


def load_volumetrie(
    start_date: ProgrammeIdentifier, end_date: ProgrammeIdentifier
) -> pd.DataFrame:
    """Retourne le nombre d'enregistrements par entité et par jour de programme."""
    frame = load_sql(VOLUMETRIE_QUERY, start_date, end_date)
    frame["entite"] = pd.Categorical(frame["entite"], categories=ENTITES, ordered=True)
    return frame.sort_values(["entite", "date_programme"], ignore_index=True)
