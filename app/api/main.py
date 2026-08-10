from fastapi import APIRouter
from strawberry.fastapi import GraphQLRouter

from app.api.routes import auth, projects, users
from app.graphql.context import get_graphql_context
from app.graphql.schema import schema

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(projects.router)
api_router.include_router(
    GraphQLRouter(schema, context_getter=get_graphql_context, path="/graphql")
)
