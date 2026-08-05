from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from admin import init_admin
from database import Base, engine
from exceptions import UserNotFoundError
from rate_limit import limiter
from routers import auth, projects, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(lifespan=lifespan, swagger_ui_parameters={"persistAuthorization": True})

init_admin(app)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(request: Request, exc: UserNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": "User not found"})


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
