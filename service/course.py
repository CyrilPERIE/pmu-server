from typing import List
from models.course import Course, CourseCreate
from pmu.types.types import CourseIdentifier
from pmu.utils import date_to_programme_date
from sqlmodel import Session, select, func
import datetime


def create_course(course_create: CourseCreate, session: Session) -> Course:
    course = Course.model_validate(course_create)
    session.merge(course)
    session.commit()
    return course

def get_active_courses_identifiers(session: Session) -> List[CourseIdentifier]:
    courses = session.exec(select(Course.id).where(Course.is_over == False)).all()
    return [CourseIdentifier(course_id) for course_id in courses]

def set_course_is_over(course_identifier: CourseIdentifier, session: Session) -> Course:
    course_id = str(course_identifier)
    course = session.get(Course, course_id)
    course.is_over = True
    session.merge(course)
    session.commit()
    return course