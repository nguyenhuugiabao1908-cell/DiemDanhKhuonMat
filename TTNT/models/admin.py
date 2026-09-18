from dataclasses import dataclass


@dataclass
class Admin:
    id: int | None
    username: str
    password: str