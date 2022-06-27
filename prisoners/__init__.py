from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from prisoners.config import settings
from tortoise import Tortoise


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, docs_url="/")

    register_tortoise(
        app,
        db_url=get_db_url(
            user=settings.POSTGRESQL_USERNAME,
            password=settings.POSTGRESQL_PASSWORD,
            hostname=settings.POSTGRESQL_HOSTNAME,
            db=settings.POSTGRESQL_DATABASE
        ),
        modules={"models": ["prisoners.src.models"]},
        generate_schemas=True,
        add_exception_handlers=True,
    )
    register_views(app=app)

    return app


def get_db_url(user, password, hostname, db):
    return f"postgres://{user}:{password}@{hostname}:5432/{db}"


def register_views(app: FastAPI):
    from prisoners.src.users import users_views
    from prisoners.src.prisoners import prisoners_views
    from prisoners.src.auth import auth_views
    from prisoners.src.bases import bases_views
    from prisoners.src.requests import requests_views
    from prisoners.src.statistics import statistics_views
    app.include_router(users_views, prefix="/users", tags=['users'])
    app.include_router(prisoners_views, prefix="/prisoners", tags=['prisoners'])
    app.include_router(auth_views, prefix="/auth", tags=['auth'])
    app.include_router(bases_views, prefix="/military-bases", tags=['military-bases'])
    app.include_router(requests_views, prefix="/requests", tags=['requests'])
    app.include_router(statistics_views, prefix="/statistics", tags=['statistics'])
    
    
Tortoise.init_models(["prisoners.src.models"], "models")