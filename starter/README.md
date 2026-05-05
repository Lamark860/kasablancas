# Vlad-rev1 — стартовый шаблон

Скелет проекта по архитектуре из `handoff/`. Запускается из коробки, дальше наполняется по `handoff/04-roadmap.md`.

## Что внутри

```
starter/
├── docker-compose.yml      # api + web одной командой
├── .env.example
├── .gitignore
│
├── api/                    # FastAPI + SQLAlchemy
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── src/vlad/
│       ├── main.py         # FastAPI app
│       ├── config.py       # настройки (pydantic-settings)
│       ├── db.py           # SQLAlchemy engine + Base
│       ├── models/         # ORM (Person, Plant, Oracle, OracleEntry)
│       ├── routes/         # роуты-заглушки (persons, plants, oracles, recommend, reports)
│       └── oracles/        # контракт оракула + registry
│
└── web/                    # Nuxt 3
    ├── Dockerfile
    ├── package.json
    ├── nuxt.config.ts
    ├── app.vue
    ├── pages/index.vue     # пинг к API
    ├── composables/useApi.ts
    └── assets/styles/globals.css
```

## Первый запуск

```bash
cp .env.example .env
docker compose up --build
```

- API: http://localhost:8100/docs
- Web: http://localhost:3100

> Порты сдвинуты с дефолтных 3000/8000 на 3100/8100, чтобы не конфликтовать с другими локальными проектами разработчика.

## Что делать дальше

Открой `handoff/04-roadmap.md` и иди по этапам:
- **Этап 0** ✅ — всё запускается через docker compose
- **Этап 1** ✅ — ORM-модели, alembic, sqladmin, сидинг oracles, pytest
- **Этап 2** — `data/seed/plants.json` + `data/seed/druid-tree.json` + `oracles/druid_tree.py`
- ...

## Полезные команды (внутри контейнера)

```bash
# миграции
docker compose exec api alembic revision --autogenerate -m "msg"
docker compose exec api alembic upgrade head
docker compose exec api alembic downgrade -1

# сидинг справочников из data/seed/*.json (идемпотентно)
docker compose exec api python -m vlad.seed

# тесты
docker compose exec api pytest               # все
docker compose exec api pytest tests/test_seed.py -v   # один файл

# заглянуть в БД
docker compose exec api sqlite3 /app/data/local.db ".tables"
```

При старте api контейнер автоматически прогоняет `alembic upgrade head`, поэтому
схема в БД всегда соответствует моделям. **Сидинг — ручной**, чтобы не затирать
правки эксперта по неосторожности (см. roadmap, принцип reseed).

## Что добавлено сверх изначального скелета (этап 1)

- `api/alembic/` + `api/alembic.ini` — миграции, DSN берётся из `vlad.config.settings`.
- `api/src/vlad/admin.py` — sqladmin views для всех 6 моделей, `/admin/` подключён в main.
- `api/src/vlad/seed.py` — CLI-сидинг из `data/seed/*.json`, идемпотентный.
- `api/data/seed/oracles.json` — 8 системных оракулов (метаданные).
- `api/tests/` — pytest, 17 тестов: схема, CRUD, сидинг, smoke /admin.
- В `docker-compose.yml`: автоматический `alembic upgrade head` при старте api.

## На потом (по roadmap)

- pyswisseph + ephe/ — этап 4
- WeasyPrint — этап 8
- Реальные растения и oracle_entries — этапы 2 и 5
