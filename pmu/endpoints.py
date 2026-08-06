from typing import List
from pmu.types.api_types import CombinaisonResponse, Course, ParticipantsResponse, ProgrammeResponse, Pronostics, PronosticsDetailles, Rapport, RapportDefinitif, Reunion
from pmu.types.enum import BetType
from pmu.types.types import CourseIdentifier, ProgrammeIdentifier, ReunionIdentifier
from pmu.client import fetch_pmu_api

def get_course(course_identifier: CourseIdentifier) -> Course | None:
    response = fetch_pmu_api(str(course_identifier))
    return response

def get_reunion(reunion_identifier: ReunionIdentifier) -> Reunion | None:
    response = fetch_pmu_api(str(reunion_identifier))
    return response

def get_programme(programme_identifier: ProgrammeIdentifier) -> ProgrammeResponse | None:
    response = fetch_pmu_api(str(programme_identifier))
    return response

def get_participants(course_identifier: CourseIdentifier) -> ParticipantsResponse | None:
    response = fetch_pmu_api(f"{str(course_identifier)}/participants?specialisation=INTERNET")
    return response

def get_pronostics(course_identifier: CourseIdentifier) -> Pronostics | None:
    response = fetch_pmu_api(f"{str(course_identifier)}/pronostics?commentaire=true")
    return response

def get_pronostics_détaillés(course_identifier: CourseIdentifier) -> PronosticsDetailles | None:
    response = fetch_pmu_api(f"{str(course_identifier)}/pronostics-detailles")
    return response

def get_combinaisons(course_identifier: CourseIdentifier) -> CombinaisonResponse | None:
    response = fetch_pmu_api(f"{str(course_identifier)}/combinaisons?specialisation=INTERNET")
    return response

def get_rapport_par_bet_type(course_identifier: CourseIdentifier, bet_type: BetType) -> Rapport | None:
    response = fetch_pmu_api(f"{str(course_identifier)}/rapports/{bet_type}")
    return response

def get_rapports_definitifs(course_identifier: CourseIdentifier) -> List[RapportDefinitif] | None:
    response = fetch_pmu_api(f"{str(course_identifier)}/rapports-definitifs?specialisation=INTERNET&combinaisonEnTableau=true")
    return response

def get_rapports_definitifs_par_bet_type(course_identifier: CourseIdentifier, bet_type: BetType) -> List[RapportDefinitif] | None:
    response = fetch_pmu_api(f"{str(course_identifier)}/rapports-definitifs/{bet_type}")
    return response