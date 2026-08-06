from typing import List
from models.course import Course, CourseCreate
from pmu.types.types import CourseIdentifier


def create_course(course_create: CourseCreate) -> Course:
    pass

def get_daily_courses() -> List[CourseIdentifier]:
    return []

def get_active_courses() -> List[CourseIdentifier]:
    return []

def set_course_is_over(course_identifier: CourseIdentifier) -> Course:
    pass