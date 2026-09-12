"""Jeu tabulaire pour étudier la faisabilité d'une prédiction.

Assemble participants, courses et réunions à partir des chargeurs existants.
Seuls les partants des courses arrivées sont conservés. Les champs post-course
(chrono, écart, réduction kilométrique) ne sont pas repris.
"""

import pandas as pd

from dataset.load_courses import load_courses
from dataset.load_participants import load_participants
from dataset.utils import DATE_WINDOW, load_sql
from pmu.types.types import ProgrammeIdentifier

REUNIONS_QUERY = f"""
select id, raw
from reunion
where {DATE_WINDOW}
"""

COURSES_ARRIVEES = {
    "ARRIVEE_DEFINITIVE_COMPLETE",
    "FIN_COURSE",
    "ARRIVEE_DEFINITIVE",
}


def load_jeu_modelisation(
    start_date: ProgrammeIdentifier, end_date: ProgrammeIdentifier
) -> pd.DataFrame:
    """Charge une ligne par partant, prête pour corrélations et modèles simples."""
    participants = load_participants(start_date, end_date)
    courses = load_courses(start_date, end_date)
    reunions = load_sql(REUNIONS_QUERY, start_date, end_date)

    contexte_reunions = pd.json_normalize(reunions.dropna(subset=["raw"])["raw"].tolist())
    contexte_reunions["reunion_id"] = reunions.dropna(subset=["raw"])["id"].to_numpy()
    contexte = contexte_reunions.reindex(
        columns=[
            "reunion_id",
            "hippodrome.libelleLong",
            "pays.libelle",
            "nature",
            "meteo.temperature",
        ]
    ).rename(
        columns={
            "hippodrome.libelleLong": "hippodrome",
            "pays.libelle": "pays",
            "nature": "nature_reunion",
            "meteo.temperature": "temperature",
        }
    )

    epreuves = courses.loc[
        courses["statut"].isin(COURSES_ARRIVEES),
        [
            "id",
            "reunion_id",
            "discipline",
            "specialite",
            "statut",
            "distance",
            "nombre_declares_partants",
            "montant_prix",
            "corde",
            "type_piste",
            "condition_sexe",
            "penetrometre_valeur",
        ],
    ].rename(
        columns={
            "id": "course_id",
            "statut": "statut_course",
            "nombre_declares_partants": "nombre_partants",
            "penetrometre_valeur": "penetrometre",
        }
    )
    epreuves = epreuves.merge(contexte, on="reunion_id", how="left")

    partants = participants.loc[
        participants["statut"] == "PARTANT",
        [
            "id",
            "course_id",
            "date_programme",
            "nom",
            "num_pmu",
            "statut",
            "ordre_arrivee",
            "incident",
            "age",
            "sexe",
            "race",
            "driver",
            "driver_change",
            "entraineur",
            "nombre_courses",
            "nombre_victoires",
            "nombre_places",
            "gains_carriere",
            "cote_reference",
            "cote_directe",
            "favori",
            "place_corde",
            "handicap_poids",
            "handicap_distance",
            "handicap_valeur",
            "deferre",
            "oeilleres",
            "inedit",
            "musique",
        ],
    ]
    return partants.merge(epreuves, on="course_id", how="inner")
