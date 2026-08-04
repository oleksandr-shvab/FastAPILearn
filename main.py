from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import Base, engine
from routers import auth, projects, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
