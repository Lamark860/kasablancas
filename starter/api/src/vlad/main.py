"""Точка входа FastAPI."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from vlad.config import settings
from vlad.db import engine, Base
from vlad.routes import persons, plants, oracles, recommend, reports
# from vlad.admin import setup_admin   # включить когда модели готовы


@asynccontextmanager
async def lifespan(app: FastAPI):
    # стартовый код (создание таблиц для разработки — в проде через Alembic)
    Base.metadata.create_all(bind=engine)
    yield
    # код завершения


app = FastAPI(
    title="Vlad rev1 API",
    version="0.1.0",
    lifespan=lifespan,
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

# setup_admin(app, engine)


@app.get("/")
def root():
    return {"name": "vlad-api", "version": "0.1.0"}


@app.get("/ping")
def ping():
    return {"ok": True}
