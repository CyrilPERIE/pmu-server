from pmu.types.types import CourseIdentifier, ProgrammeIdentifier, ReunionIdentifier
from pmu.endpoints import *
import pandas as pd

PATH = "pmu/mock/data"
def save_to_csv(data: dict, filename: str):
    pd.DataFrame([data]).to_csv(f"{PATH}/{filename}", index=False)

course_functions = [
    get_course,
    get_participants,
    get_pronostics,
    get_pronostics_détaillés,
    get_combinaisons,
    get_rapports_definitifs,
]

course_bet_type_functions = [
    get_rapport_par_bet_type,
    get_rapports_definitifs_par_bet_type,
]

reunion_functions = [
    get_reunion
]

programme_functions = [
    get_programme,
]

def generate_mock_data():
    course_num = 1
    reunion_num = 1
    programme = "01012026"
    bet_type = BetType.E_SIMPLE_PLACE.value
    course_identifier = CourseIdentifier(course_num,reunion_num,programme)
    reunion_identifier = ReunionIdentifier(reunion_num,programme)
    programme_identifier = ProgrammeIdentifier(programme)

    for function in course_functions:
        data = function(course_identifier)
        save_to_csv(data, f"course_{function.__name__}.csv")

    for function in course_bet_type_functions:
        data = function(course_identifier, bet_type)
        save_to_csv(data, f"course_bet_type_{bet_type}_{function.__name__}.csv")

    for function in reunion_functions:
        data = function(reunion_identifier)
        save_to_csv(data, f"reunion_{function.__name__}.csv")

    for function in programme_functions:
        data = function(programme_identifier)
        save_to_csv(data, f"programme_{function.__name__}.csv")