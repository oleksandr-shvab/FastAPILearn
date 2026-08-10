import enum


class ProjectPermission(str, enum.Enum):
    MEMBERS_MANAGE = "project.members.manage"
