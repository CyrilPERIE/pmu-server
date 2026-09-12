"""Chargement des participants sous forme tabulaire.

C'est la table la plus volumineuse de la base : les clés sont projetées en SQL et
les montants sont laissés dans leur unité d'origine (centimes d'euro côté PMU).
"""

import pandas as pd

from dataset.utils import DATE_WINDOW, PROGRAMME_DATE, load_sql
from pmu.types.types import ProgrammeIdentifier

PARTICIPANTS_QUERY = f"""
select
    id,
    course_id,
    substring(id, 1, 8) as programme_id,
    ({PROGRAMME_DATE})::timestamp as date_programme,
    (raw ->> 'numPmu')::int as num_pmu,
    raw ->> 'nom' as nom,
    raw ->> 'statut' as statut,
    (raw ->> 'ordreArrivee')::int as ordre_arrivee,
    raw ->> 'incident' as incident,
    (raw ->> 'age')::int as age,
    raw ->> 'sexe' as sexe,
    raw ->> 'race' as race,
    raw ->> 'allure' as allure,
    raw -> 'robe' ->> 'libelleCourt' as robe,
    raw ->> 'driver' as driver,
    coalesce((raw ->> 'driverChange')::boolean, false) as driver_change,
    raw ->> 'entraineur' as entraineur,
    raw ->> 'proprietaire' as proprietaire,
    raw ->> 'eleveur' as eleveur,
    raw ->> 'nomPere' as nom_pere,
    raw ->> 'nomMere' as nom_mere,
    (raw ->> 'nombreCourses')::int as nombre_courses,
    (raw ->> 'nombreVictoires')::int as nombre_victoires,
    (raw ->> 'nombrePlaces')::int as nombre_places,
    (raw -> 'gainsParticipant' ->> 'gainsCarriere')::float as gains_carriere,
    (raw -> 'gainsParticipant' ->> 'gainsAnneeEnCours')::float as gains_annee_en_cours,
    (raw -> 'gainsParticipant' ->> 'gainsVictoires')::float as gains_victoires,
    (raw -> 'dernierRapportReference' ->> 'rapport')::float as cote_reference,
    (raw -> 'dernierRapportDirect' ->> 'rapport')::float as cote_directe,
    coalesce((raw -> 'dernierRapportDirect' ->> 'favoris')::boolean, false) as favori,
    raw -> 'dernierRapportDirect' ->> 'indicateurTendance' as tendance_cote,
    (raw ->> 'reductionKilometrique')::int as reduction_kilometrique,
    (raw ->> 'tempsObtenu')::int as temps_obtenu,
    (raw ->> 'handicapPoids')::float as handicap_poids,
    (raw ->> 'handicapDistance')::int as handicap_distance,
    (raw ->> 'handicapValeur')::float as handicap_valeur,
    (raw ->> 'placeCorde')::int as place_corde,
    raw -> 'distanceChevalPrecedent' ->> 'identifiant' as ecart_cheval_precedent,
    raw ->> 'deferre' as deferre,
    raw ->> 'oeilleres' as oeilleres,
    coalesce((raw ->> 'jumentPleine')::boolean, false) as jument_pleine,
    coalesce((raw ->> 'indicateurInedit')::boolean, false) as inedit,
    coalesce((raw ->> 'engagement')::boolean, false) as engagement,
    (raw ->> 'supplement')::float as supplement,
    raw ->> 'musique' as musique,
    (raw ->> 'avisEntraineur') is not null as avis_entraineur_present,
    created_at,
    updated_at
from participant
where {DATE_WINDOW}
order by id
"""


def load_participants(
    start_date: ProgrammeIdentifier, end_date: ProgrammeIdentifier
) -> pd.DataFrame:
    """Charge les participants de la fenêtre, une ligne par partant déclaré."""
    return load_sql(PARTICIPANTS_QUERY, start_date, end_date)
