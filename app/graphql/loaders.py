from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.dataloader import DataLoader

from app.models import ProjectMember, User
from app.models.role import Role


def make_member_loader(db: AsyncSession) -> DataLoader[int, list[ProjectMember]]:
    async def batch_load(project_ids: list[int]) -> list[list[ProjectMember]]:
        result = await db.execute(
            select(ProjectMember).where(ProjectMember.project_id.in_(project_ids))
        )
        by_project: dict[int, list[ProjectMember]] = defaultdict(list)
        for member in result.scalars().all():
            by_project[member.project_id].append(member)
        return [by_project.get(project_id, []) for project_id in project_ids]

    return DataLoader(load_fn=batch_load)


def make_user_loader(db: AsyncSession) -> DataLoader[int, User]:
    async def batch_load(user_ids: list[int]) -> list[User]:
        result = await db.execute(select(User).where(User.id.in_(user_ids)))
        by_id = {user.id: user for user in result.scalars().all()}
        return [by_id[user_id] for user_id in user_ids]

    return DataLoader(load_fn=batch_load)


def make_role_loader(db: AsyncSession) -> DataLoader[int, Role]:
    async def batch_load(role_ids: list[int]) -> list[Role]:
        result = await db.execute(select(Role).where(Role.id.in_(role_ids)))
        by_id = {role.id: role for role in result.scalars().all()}
        return [by_id[role_id] for role_id in role_ids]

    return DataLoader(load_fn=batch_load)
