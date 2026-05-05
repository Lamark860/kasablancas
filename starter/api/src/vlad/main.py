"""Точка входа FastAPI."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from vlad.admin import setup_admin
from vlad.config import settings
from vlad.db import engine
from vlad.routes import geocode, oracles, persons, plants, recommend, reports

# Регистрация ORM в Base.metadata. Тревога — sqladmin без этого импорта
# не увидит модели; alembic тоже импортирует vlad.models в env.py.
import vlad.models  # noqa: F401


app = FastAPI(
    title="Vlad rev1 API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(persons.router, prefix="/persons", tags=["persons"])
app.include_router(plants.router, prefix="/plants", tags=["plants"])
app.include_router(oracles.router, prefix="/oracles", tags=["oracles"])
app.include_router(recommend.router, prefix="/recommend", tags=["recommend"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(geocode.router, prefix="/geocode", tags=["geocode"])

setup_admin(app, engine)


@app.get("/")
def root():
    return {"name": "vlad-api", "version": "0.1.0"}


@app.get("/ping")
def ping():
    return {"ok": True}
