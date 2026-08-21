from pmu.types.types import CourseIdentifier


def course_id_to_course_identifier(course_id: str) -> CourseIdentifier:
    course_num = int(course_id.split('/')[-1].split('C')[1])
    reunion_num = int(course_id.split('/')[-2].split('R')[1])
    programme = course_id.split('/')[0]
    return CourseIdentifier(course_num, reunion_num, programme)