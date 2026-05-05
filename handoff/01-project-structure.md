# Структура проекта

Monorepo с двумя приложениями: FastAPI-бэк и Nuxt-фронт.

```
vlad-rev1/
├── docker-compose.yml             # api + web + postgres (опц.) + adminer (опц.)
├── docker-compose.dev.yml         # dev-overrides (volume mounts, hot reload)
├── .env.example
├── .gitignore
├── README.md
│
├── api/                           # FastAPI-бэкенд
│   ├── pyproject.toml             # uv + ruff + pytest
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/              # миграции
│   ├── data/
│   │   └── seed/                  # начальные JSON-данные
│   │       ├── plants.json
│   │       ├── oracles.json
│   │       ├── druid-tree.json
│   │       ├── druid-flower.json
│   │       ├── zodiac-plants.json
│   │       ├── slavic.json
│   │       ├── name-plants.json
│   │       ├── eye-color.json
│   │       └── lunar.json
│   ├── ephe/                      # Swiss Ephemeris-файлы (раз скачал — лежат)
│   ├── tests/
│   └── src/
│       └── vlad/
│           ├── __init__.py
│           ├── main.py            # FastAPI app, include_routers, sqladmin mount
│           ├── config.py          # pydantic-settings
│           ├── db.py              # engine, SessionLocal, Base
│           ├── models/            # SQLAlchemy ORM
│           │   ├── __init__.py
│           │   ├── person.py
│           │   ├── plant.py
│           │   ├── oracle.py      # Oracle (метаданные) + OracleEntry (соответствия)
│           │   └── recommendation.py
│           ├── schemas/           # Pydantic DTO (вход/выход API)
│           │   ├── person.py
│           │   ├── plant.py
│           │   └── recommendation.py
│           ├── routes/
│           │   ├── persons.py     # CRUD /persons
│           │   ├── plants.py      # CRUD /plants
│           │   ├── oracles.py     # GET /oracles, PATCH /oracles/{id}
│           │   ├── recommend.py   # POST /recommend → пул растений
│           │   ├── reports.py     # GET /reports/{person_id}.pdf
│           │   └── admin.py       # sqladmin mount
│           ├── core/
│           │   ├── orchestrator.py   # ⭐ ядро: запускает оракулы, сливает, фильтрует
│           │   ├── filters.py        # климатические + садовые фильтры
│           │   └── scoring.py        # формула финального ранжирования
│           ├── oracles/              # ⭐ КЛЮЧЕВАЯ ПАПКА
│           │   ├── __init__.py       # registry: id → Oracle subclass
│           │   ├── base.py           # абстрактный Oracle (контракт)
│           │   ├── druid_tree.py
│           │   ├── druid_flower.py
│           │   ├── zodiac.py
│           │   ├── slavic.py
│           │   ├── name.py
│           │   ├── eye_color.py
│           │   ├── lunar.py
│           │   └── numerology.py
│           ├── natal/
│           │   ├── swisseph_wrapper.py   # pyswisseph + кеш эфемерид
│           │   ├── geocode.py            # место рождения → широта/долгота
│           │   └── chart.py              # NatalChart dataclass
│           └── pdf/
│               ├── render.py             # WeasyPrint HTML → PDF
│               └── templates/
│                   └── client_report.html
│
├── web/                           # Nuxt 3 — фронт
│   ├── package.json
│   ├── nuxt.config.ts
│   ├── tsconfig.json
│   ├── Dockerfile
│   ├── public/
│   │   ├── fonts/                 # IM Fell, Cormorant Garamond и др.
│   │   ├── textures/              # пергамент, гербарий
│   │   └── icons/                 # SVG-иконки растений
│   ├── assets/
│   │   └── styles/
│   │       ├── victorian.css      # палитра, шрифты, переменные
│   │       └── globals.css
│   ├── composables/
│   │   ├── useApi.ts              # обёртка над $fetch
│   │   └── useRecommendation.ts
│   ├── components/
│   │   ├── PlantCard.vue
│   │   ├── OracleBadge.vue
│   │   ├── PersonForm.vue
│   │   ├── PoolView.vue           # эксперт-режим: пул с источниками
│   │   ├── ClientReport.vue       # клиент-режим: красивый отчёт
│   │   └── ...
│   ├── pages/
│   │   ├── index.vue              # обложка / выбор клиента
│   │   ├── intake.vue             # форма ввода
│   │   ├── expert/[id].vue        # пул растений (эксперт)
│   │   ├── client/[id].vue        # отчёт (клиент)
│   │   └── plants/index.vue       # справочник растений (опц.)
│   └── types/
│       └── api.ts                 # отзеркаленные с бэка типы
│
└── shared/                        # (опц.) общие JSON-схемы или OpenAPI-спека
    └── openapi.json               # генерируется FastAPI, потребляется Nuxt
```

## Принципы организации

### 1. Каждый оракул — отдельный файл

`api/src/vlad/oracles/druid_tree.py` — самодостаточный модуль. Наследует `Oracle` из `base.py`, реализует один метод `run(person) -> list[OracleResult]`, использует свою таблицу из `data/seed/druid-tree.json` (или из БД, если уже импортировано).

**Чтобы добавить новую систему**: создаёшь один файл, один JSON, регистрируешь в `oracles/__init__.py`. Больше нигде ничего не трогаешь. Это и есть та самая расширяемость.

Подробный пример — в `03-oracle-interface.md`.

### 2. Растения отдельно от соответствий

`seed/plants.json` — каноничный список растений с ботаникой, ценой, hierarchy_potential. Один источник истины.

`seed/druid-tree.json` — только пары `{date_range, plant_id, weight, reason}`. Никакой ботаники.

Это значит: справочник растений можно редактировать независимо от системы соответствий, и наоборот.

### 3. БД — два слоя моделей

- `models/` — **SQLAlchemy ORM** (как лежит в БД)
- `schemas/` — **Pydantic DTO** (как ходит по API)

Не смешивай. ORM-модели не выходят наружу (они тащат отношения, lazy-load и т.п.). API получает на вход и отдаёт наружу только Pydantic-схемы. Конвертация — в роутах.

### 4. Натальная карта изолирована

`natal/swisseph_wrapper.py` — **единственное место**, которое работает с pyswisseph напрямую. Снаружи он отдаёт чистый dataclass `NatalChart`. Если завтра решишь сменить движок — меняешь один файл.

### 5. Админка через sqladmin

`sqladmin` подключается к FastAPI на `/admin` и автоматически даёт CRUD для всех ORM-моделей. Это и есть "редактор соответствий" из требований — никакого отдельного UI не нужно для MVP.

### 6. Что в .gitignore

```
__pycache__/
*.pyc
.venv/
node_modules/
.nuxt/
.output/
dist/
.env
api/data/local.db
api/data/local.db-journal
api/ephe/*.se1     # эфемериды (большие, можно скачать заново)
```

## Что приходит из текущего HTML-прототипа

В корне проекта лежат `prototype-screens.jsx`, `victorian-styles.jsx`, `pergament.jsx` и т.д. Они написаны как inline-Babel JSX для одного HTML-файла.

**Не копируй один-в-один в Vue.** Используй как:
- эталон UX (какие экраны, какие переходы)
- источник стилевых констант (`victorian-styles.jsx` — вынеси переменные в `web/assets/styles/victorian.css`)
- источник SVG-иконок (`plant-icons.jsx` — переноси в `web/public/icons/` или в Vue-компоненты)
- источник копирайтинга

Production Vue-код пиши с нуля под нормальную структуру компонентов и pages-роутинг Nuxt.
