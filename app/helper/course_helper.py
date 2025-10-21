from typing import Tuple
from enum import Enum


class Grade(Enum):
    G10 = "g10"
    G11 = "g11"
    G12 = "g12"
    TEST = "existing"


class Subject(Enum):
    PHYSICS = "phys"
    CHEMISTRY = "chem"
    BIOLOGY = "bio"
    TEST = "course_one"


def assemble_course_id(grade: Grade, subject: Subject) -> str:
    if not isinstance(grade, Grade) or not isinstance(subject, Subject):
        raise TypeError("Parameters have to be of enum of Grade or Subject.")

    return f"{grade.value}_{subject.value}"


def parse_course_id(course_id: str) -> Tuple[Grade, Subject]:
    try:
        grade_str, subject_str = course_id.split("_")
        grade = Grade(grade_str)
        subject = Subject(subject_str)

        return grade, subject
    except ValueError as e:
        raise ValueError(f"Cannot parse course id {course_id}: {e}")
