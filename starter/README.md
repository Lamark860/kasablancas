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

- API: http://localhost:8000/docs
- Web: http://localhost:3000

## Что делать дальше

Открой `handoff/04-roadmap.md` и иди по этапам:
- **Этап 0** уже сделан этим шаблоном (всё запускается)
- **Этап 1** — допиши Alembic-миграции, прогони `alembic upgrade head`
- **Этап 2** — наполни `data/seed/`, реализуй первый оракул
- ...

## Заметка

Это **минимальный** скелет, не всё-в-одном. Сознательно убраны:
- Alembic — настроишь руками, чтобы понимать что происходит
- sqladmin — добавишь когда модели стабилизируются
- pyswisseph — на этапе 4
- WeasyPrint — на этапе 8
- Все сиды и реальные оракулы — это твоя работа

Это не пробел, а конструкция. Каждое добавление — осознанный шаг.
