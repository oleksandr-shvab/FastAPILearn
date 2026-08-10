import enum


class ProjectPermission(str, enum.Enum):
    MEMBERS_MANAGE = "project.members.manage"
    MEMBERS_ADD = "project.members.add"
