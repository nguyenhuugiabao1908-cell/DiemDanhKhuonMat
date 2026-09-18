from dataclasses import dataclass

@dataclass
class Student:
    id: int | None
    student_id: str
    full_name: str
    class_name: str
    faculty: str
    email: str
    phone: str