"""Chargement des courses sous forme tabulaire.

Le JSON brut d'une course pèse plusieurs kilo-octets ; sur la fenêtre étudiée il
y a plus de 30 000 courses. Les clés utiles sont donc projetées directement en
SQL plutôt que rapatriées puis aplaties côté pandas.
"""

import pandas as pd

from dataset.utils import DATE_WINDOW, PROGRAMME_DATE, load_sql
from pmu.types.types import ProgrammeIdentifier

COURSES_QUERY = f"""
select
    id,
    reunion_id,
    substring(id, 1, 8) as programme_id,
    ({PROGRAMME_DATE})::timestamp as date_programme,
    (raw ->> 'numReunion')::int as num_reunion,
    (raw ->> 'numExterne')::int as num_course,
    (raw ->> 'numOrdre')::int as num_ordre,
    raw ->> 'libelle' as libelle,
    raw ->> 'discipline' as discipline,
    raw ->> 'specialite' as specialite,
    raw ->> 'statut' as statut,
    raw ->> 'categorieStatut' as categorie_statut,
    raw ->> 'categorieParticularite' as categorie_particularite,
    raw ->> 'conditionAge' as condition_age,
    raw ->> 'conditionSexe' as condition_sexe,
    -- l'hippodrome n'est pas porté par la course : il se lit sur la réunion
    (raw ->> 'distance')::int as distance,
    raw ->> 'distanceUnit' as distance_unite,
    raw ->> 'corde' as corde,
    raw ->> 'typePiste' as type_piste,
    raw ->> 'parcours' as parcours,
    (raw ->> 'montantPrix')::float as montant_prix,
    (raw ->> 'montantTotalOffert')::float as montant_total_offert,
    (raw ->> 'montantOffert1er')::float as montant_offert_premier,
    (raw ->> 'nombreDeclaresPartants')::int as nombre_declares_partants,
    (raw ->> 'dureeCourse')::float as duree_course_ms,
    to_timestamp((raw ->> 'heureDepart')::bigint / 1000.0) at time zone 'UTC'
        as heure_depart_utc,
    -- `timezoneOffset` porte le décalage de l'hippodrome : on l'ajoute pour
    -- obtenir l'heure locale de départ, seule pertinente pour l'analyse horaire.
    to_timestamp(
        ((raw ->> 'heureDepart')::bigint + (raw ->> 'timezoneOffset')::bigint) / 1000.0
    ) at time zone 'UTC' as heure_depart_locale,
    (raw ->> 'timezoneOffset')::int as timezone_offset_ms,
    coalesce((raw ->> 'arriveeDefinitive')::boolean, false) as arrivee_definitive,
    coalesce((raw ->> 'rapportsDefinitifsDisponibles')::boolean, false)
        as rapports_definitifs_disponibles,
    coalesce((raw ->> 'courseExclusiveInternet')::boolean, false) as exclusive_internet,
    coalesce((raw ->> 'pariMultiCourses')::boolean, false) as pari_multi_courses,
    coalesce((raw ->> 'replayDisponible')::boolean, false) as replay_disponible,
    raw -> 'penetrometre' ->> 'intitule' as penetrometre_intitule,
    -- le pénétromètre est renseigné à la main, avec une virgule décimale
    nullif(replace(raw -> 'penetrometre' ->> 'valeurMesure', ',', '.'), '')::float
        as penetrometre_valeur,
    json_array_length(raw -> 'paris') as nombre_paris,
    json_array_length(raw -> 'ordreArrivee') as nombre_places_arrivee,
    json_array_length(raw -> 'incidents') as nombre_incidents,
    is_over,
    created_at,
    updated_at
from course
where {DATE_WINDOW}
order by id
"""


def load_courses(
    start_date: ProgrammeIdentifier, end_date: ProgrammeIdentifier
) -> pd.DataFrame:
    """Charge les courses de la fenêtre, une ligne par course."""
    return load_sql(COURSES_QUERY, start_date, end_date)
