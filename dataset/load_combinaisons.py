"""Chargement des relevés de paris (table `combinaison`).

Chaque ligne est une photographie du marché à un instant : type de pari, masse
d'enjeux, et liste des combinaisons les plus jouées. La table ne couvre pas
tout l'historique : elle n'existe que pour les courses suivies en direct.
"""

from dataset.utils import load_query

RELEVES_QUERY = """
select
    id,
    course_id,
    to_date(substring(id, 1, 8), 'DDMMYYYY') as date_programme,
    raw ->> 'pariType' as type_pari,
    (raw ->> 'totalEnjeu')::float as masse,
    (raw ->> 'updateTime')::bigint as update_time,
    to_timestamp((raw ->> 'updateTime')::bigint / 1000.0) at time zone 'UTC' as instant,
    json_array_length(raw -> 'listeCombinaisons') as nombre_lignes,
    created_at
from combinaison
"""

MARCHE_SIMPLE_QUERY = """
select
    course_id,
    to_date(substring(id, 1, 8), 'DDMMYYYY') as date_programme,
    (raw ->> 'updateTime')::bigint as update_time,
    to_timestamp((raw ->> 'updateTime')::bigint / 1000.0) at time zone 'UTC' as instant,
    (raw ->> 'totalEnjeu')::float as masse,
    (ligne ->> 'totalEnjeu')::float as enjeu,
    (ligne -> 'combinaison' ->> 0)::int as num_pmu
from combinaison
cross join lateral json_array_elements(raw -> 'listeCombinaisons') as ligne
where raw ->> 'pariType' = 'E_SIMPLE_GAGNANT'
"""

ARRIVEES_QUERY = """
select
    participant.course_id,
    (participant.raw ->> 'numPmu')::int as num_pmu,
    (participant.raw ->> 'ordreArrivee')::int as ordre_arrivee,
    participant.raw ->> 'nom' as nom
from participant
where participant.course_id in (select distinct course_id from combinaison)
    and participant.raw ->> 'statut' = 'PARTANT'
"""

COURSES_QUERY = """
select
    id as course_id,
    raw ->> 'discipline' as discipline,
    raw ->> 'libelle' as libelle,
    (raw ->> 'nombreDeclaresPartants')::int as nombre_partants,
    (raw ->> 'montantPrix')::float as montant_prix,
    to_timestamp((raw ->> 'heureDepart')::bigint / 1000.0) at time zone 'UTC'
        as heure_depart_utc
from course
where id in (select distinct course_id from combinaison)
"""


def load_releves():
    """Un enregistrement par photographie de marché (tous types de paris)."""
    return load_query(RELEVES_QUERY)


def load_marche_simple():
    """Enjeux du simple gagnant, une ligne par cheval et par instant."""
    return load_query(MARCHE_SIMPLE_QUERY)


def load_arrivees_marche():
    """Partants et places des courses pour lesquelles un relevé existe."""
    return load_query(ARRIVEES_QUERY)


def load_courses_marche():
    """Cadre des courses suivies en direct."""
    return load_query(COURSES_QUERY)
