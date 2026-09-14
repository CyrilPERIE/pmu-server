from datetime import date, datetime
from typing import List, TYPE_CHECKING

from pmu.types.api_types import Course
if TYPE_CHECKING:
    from pmu.types.types import ProgrammeIdentifier

def date_to_programme_date(_date: date) -> str:
    return _date.strftime("%d%m%Y")

def programme_date_to_date(programme_date: str) -> date:
    return datetime.strptime(programme_date, "%d%m%Y")

def is_arrivee_definitive(course: Course) -> bool:
    return "arriveeDefinitive" in course.keys() and course["arriveeDefinitive"] == True

def is_course_annulee(course: Course) -> bool:
    return "statut" in course.keys() and course["statut"] == "COURSE_ANNULEE"

def programme_dates_between_dates(start_date: "ProgrammeIdentifier", end_date: "ProgrammeIdentifier") -> "List[ProgrammeIdentifier]":    
    programmes = []
    current_date = start_date
    while current_date <= end_date:
        programmes.append(str(current_date))
        current_date = current_date.increment()
    return programmes