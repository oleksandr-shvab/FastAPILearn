import enum


class ProjectRole(str, enum.Enum):
    owner = "owner"
    member = "member"
