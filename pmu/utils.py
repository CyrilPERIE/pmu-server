from datetime import date, datetime

from pmu.types.api_types import Course

def date_to_programme_date(_date: date) -> str:
    return _date.strftime("%d%m%Y")

def programme_date_to_date(programme_date: str) -> date:
    return datetime.strptime(programme_date, "%d%m%Y")

def is_arrivee_definitive(course: Course) -> bool:
    return "arriveeDefinitive" in course.keys() and course["arriveeDefinitive"] == True

def is_course_annulee(course: Course) -> bool:
    return "statut" in course.keys() and course["statut"] == "COURSE_ANNULEE"