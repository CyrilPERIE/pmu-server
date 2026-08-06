from datetime import date

from pmu.types.api_types import Course

def date_to_programme_date(_date: date) -> str:
    return _date.strftime("%d%m%Y")

def is_course_terminée(course: Course) -> bool:
    return course.isArriveeDefinitive == True