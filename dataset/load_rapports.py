"""Chargement des rapports définitifs sous forme tabulaire.

Un rapport correspond à un couple (course, type de pari) et contient une liste de
lignes de dividendes. `load_rapports` en donne la synthèse (une ligne par
rapport) ; `load_dividendes` déplie les lignes pour les types de paris demandés.
"""

from typing import Sequence

import pandas as pd

from dataset.utils import DATE_WINDOW, PROGRAMME_DATE, load_sql
from pmu.types.types import ProgrammeIdentifier

RAPPORTS_QUERY = f"""
select
    id,
    course_id,
    substring(id, 1, 8) as programme_id,
    ({PROGRAMME_DATE})::timestamp as date_programme,
    raw ->> 'typePari' as type_pari,
    raw ->> 'famillePari' as famille_pari,
    raw ->> 'audience' as audience,
    (raw ->> 'miseBase')::float as mise_base,
    raw ->> 'dividendeUnite' as dividende_unite,
    coalesce((raw ->> 'rembourse')::boolean, false) as rembourse,
    json_array_length(raw -> 'rapports') as nombre_lignes,
    (raw -> 'rapports' -> 0 ->> 'dividendePourUnEuro')::float as dividende_premier,
    (raw -> 'rapports' -> 0 ->> 'nombreGagnants')::float as gagnants_premier,
    json_array_length(raw -> 'rapports' -> 0 -> 'combinaison') as taille_combinaison,
    lignes.dividende_min,
    lignes.dividende_max,
    lignes.gagnants_total,
    created_at,
    updated_at
from rapport
left join lateral (
    select
        min((ligne ->> 'dividendePourUnEuro')::float) as dividende_min,
        max((ligne ->> 'dividendePourUnEuro')::float) as dividende_max,
        sum((ligne ->> 'nombreGagnants')::float) as gagnants_total
    from json_array_elements(rapport.raw -> 'rapports') as ligne
) as lignes on true
where {DATE_WINDOW}
order by id
"""

DIVIDENDES_QUERY = f"""
select
    id as rapport_id,
    course_id,
    ({PROGRAMME_DATE})::timestamp as date_programme,
    raw ->> 'typePari' as type_pari,
    (raw ->> 'miseBase')::float as mise_base,
    ligne.position,
    ligne.valeur ->> 'libelle' as libelle,
    (ligne.valeur ->> 'dividende')::float as dividende,
    (ligne.valeur ->> 'dividendePourUnEuro')::float as dividende_pour_un_euro,
    (ligne.valeur ->> 'nombreGagnants')::float as nombre_gagnants,
    json_array_length(ligne.valeur -> 'combinaison') as taille_combinaison
from rapport
cross join lateral json_array_elements(rapport.raw -> 'rapports')
    with ordinality as ligne(valeur, position)
where {DATE_WINDOW}
    and raw ->> 'typePari' = any(:types_pari)
"""


def load_rapports(
    start_date: ProgrammeIdentifier, end_date: ProgrammeIdentifier
) -> pd.DataFrame:
    """Charge les rapports de la fenêtre, une ligne par (course, type de pari)."""
    return load_sql(RAPPORTS_QUERY, start_date, end_date)


def load_dividendes(
    start_date: ProgrammeIdentifier,
    end_date: ProgrammeIdentifier,
    types_pari: Sequence[str] = ("E_SIMPLE_GAGNANT", "SIMPLE_GAGNANT"),
) -> pd.DataFrame:
    """Déplie les lignes de dividendes pour une sélection de types de paris."""
    return load_sql(DIVIDENDES_QUERY, start_date, end_date, types_pari=list(types_pari))
