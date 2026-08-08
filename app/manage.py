import asyncio

import typer
from pydantic import SecretStr, ValidationError

from app.core.db import AsyncSessionLocal
from app.crud import user as user_crud
from app.exceptions import UserAlreadyExistsError
from app.schemas import UserCreate

app = typer.Typer(help="Management commands")


@app.callback()
def callback() -> None:
    pass


@app.command()
def createsuperuser(
    username: str = typer.Option(..., prompt=True),
    email: str = typer.Option(..., prompt=True),
    password: str = typer.Option(
        ..., prompt=True, hide_input=True, confirmation_prompt=True
    ),
) -> None:
    """Create an admin user."""
    try:
        payload = UserCreate(username=username, email=email, password=SecretStr(password))
    except ValidationError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1)

    async def _create():
        async with AsyncSessionLocal() as db:
            return await user_crud.create_superuser(db, payload)

    try:
        user = asyncio.run(_create())
    except UserAlreadyExistsError:
        typer.secho(
            f"User with username '{username}' or email '{email}' already exists.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    typer.secho(f"Superuser '{user.username}' created (id={user.id}).", fg=typer.colors.GREEN)


if __name__ == "__main__":
    app()
