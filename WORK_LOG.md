# WORK_LOG — журнал прогресса

Живой журнал работы по проекту Vlad rev1. Цель: после сброса контекста сессии любой Claude может открыть этот файл и за минуту понять где мы, что сделано, как проверить и что следующее.

**Для следующей сессии Claude:** прочти в таком порядке — `README.md` → этот файл → `handoff/04-roadmap.md` → текущий «Активный этап» ниже.

---

## Состояние на текущий момент

- **Дата:** 2026-05-05
- **Активный этап:** 1 завершён, переходим на 2
- **Что работает:** docker compose, БД с 6 таблицами + 8 оракулами, sqladmin на `/admin`, 17/17 pytest зелёные
- **Блокеров:** нет

## Как проверить, в каком состоянии проект сейчас

```bash
cd "/Users/maximlomaev/projects/Vlad rev1(1)/starter"
docker compose ps                                                  # vlad-api, vlad-web в Up
curl -fsS http://localhost:8100/                                   # {"name":"vlad-api",...}
curl -fsS -o /dev/null -w "admin %{http_code}\n" http://localhost:8100/admin/   # admin 200
docker compose exec api alembic current                            # текущая ревизия
docker compose exec api sqlite3 /app/data/local.db ".tables"       # 7 таблиц (+alembic_version)
docker compose exec api pytest -q                                  # 17 passed
```

Если pytest зелёный и в `/admin/oracle/list` видно 8 строк — этап 1 пройден.

---

## Договорённости с пользователем

- **Стек:** уже выбран в `handoff/00-stack.md` — FastAPI + Nuxt 3 + SQLite, всё через Docker.
- **Git:** локальный, без удалённого репо. Главная ветка `main`. Коммиты в conventional-style (`chore:`, `feat:`, `fix:`).
- **Docker:** всё поднимаем через `docker compose` для изоляции, в систему ничего не ставим.
- **MCP:** дополнительные не подключаем до этапа 5–6, тогда смотрим, нужен ли браузерный (Chrome DevTools / Playwright) для верификации UI против `Prototype.html`.
- **Документация:** этот файл (`WORK_LOG.md`) ведём всегда, после каждого значимого шага. Тесты пишем по ходу (pytest для бэка, smoke-curl/браузерные проверки для фронта).

---

## Журнал по этапам

### Этап 0 — Подготовка ✅

**Цель из roadmap:** окружение готово, проект собирается, оба сервиса отвечают.

**Сделано:**
- [x] Инициализирован git в корне проекта (`main`), baseline-коммит.
- [x] Создан корневой `.gitignore` (Python, Node, .env, БД, эфемериды).
- [x] Скопирован `starter/.env.example` → `starter/.env`.
- [x] **Порты сдвинуты с 3000/8000 → 3100/8100** (хост-3000 занят чужим `ai-generator-frontend`, хост-8000 — `ai-generator-api`). Внутри контейнеров порты остались стандартные.
- [x] Прошёл первый `docker compose up --build` (~3 мин, ставит pyswisseph, weasyprint, Nuxt-зависимости).
- [x] **Починен SSR-вызов фронт → бэк:** Nuxt SSR внутри контейнера использует `http://api:8000` (имя docker-сервиса), браузер — `http://localhost:8100`. Разделено через `NUXT_API_BASE_SERVER` + `NUXT_PUBLIC_API_BASE`. Композабл `useApi.ts` переключается через `import.meta.server`.
- [x] Smoke-тесты: api `/`, `/docs`, `/openapi.json` → 200; web рендерит `{"ok": true}` от `/ping`; в логах api видны хиты от web по docker-сети `172.26.0.3 → /ping`.

**Как продолжить с нуля:**
```bash
cd "/Users/maximlomaev/projects/Vlad rev1(1)/starter"
docker compose up -d
# подождать ~20 сек
curl -fsS http://localhost:8100/        # должен вернуть {"name":"vlad-api",...}
curl -fsS -o /dev/null -w "%{http_code}\n" http://localhost:3100/    # 200
docker logs vlad-api | grep /ping | tail -3   # видны SSR-хиты
```

---

### Этап 1 — БД и модели ✅

**Цель:** схема БД накачена, есть пустая админка.

**Сделано:**
- [x] ORM-модели в `api/src/vlad/models/__init__.py` по `handoff/02-database-schema.sql`:
  Person, Plant, Oracle, OracleEntry, Recommendation, NatalChart — с CheckConstraint,
  индексами, relationships, TimestampMixin (`created_at` / `updated_at`).
- [x] Alembic поднят: `api/alembic.ini` + `api/alembic/env.py` (DSN берётся из
  `vlad.config.settings`, не из ini), первая миграция `init schema` сгенерирована
  через autogenerate.
- [x] CMD api-контейнера теперь делает `alembic upgrade head` перед стартом uvicorn —
  схема всегда актуальна.
- [x] sqladmin подключён на `/admin`, 6 ModelView с поиском/сортировкой/иконками.
- [x] `vlad/seed.py` (CLI: `python -m vlad.seed`) — идемпотентный сидинг из
  `data/seed/*.json`. `data/seed/oracles.json` — 8 системных оракулов.
- [x] pytest 17/17 зелёные:
  - `test_schema.py` — наличие таблиц, FK, unique
  - `test_models_crud.py` — CRUD, cascade-delete, CheckConstraint срабатывает
  - `test_seed.py` — сидинг идемпотентен и подтягивает все 8 оракулов
  - `test_admin_smoke.py` — `/admin/` и каждый ModelView отвечают 200
- [x] Dockerfile теперь ставит `-e ".[dev]"` — pytest, ruff, httpx и т.д.

**Заметки и компромиссы:**
- Сидинг намеренно ручной (`docker compose exec api python -m vlad.seed`), не
  автостартом. Принцип reseed-безболезненно из roadmap: эксперт может править
  JSON и знает, что reseed затрёт `oracle_entries` и `plants`, но не Person.
- `Plant.slug` ссылочная (FK от `oracle_entries.plant_slug` и
  `recommendations.title_plant_slug`), не `id` — slug стабильный человекочитаемый
  ключ из JSON-сидов.
- Тесты используют SQLite in-memory + `Base.metadata.create_all` для скорости,
  а не пере-прогон alembic. Корректность миграций косвенно проверяется тем, что
  app в admin-smoke использует реальную БД, накаченную через alembic.

**Как продолжить с нуля:**
```bash
cd "/Users/maximlomaev/projects/Vlad rev1(1)/starter"
docker compose up -d                                          # alembic upgrade head выполнится сам
docker compose exec api python -m vlad.seed                   # 8 оракулов в БД
docker compose exec api pytest -q                             # 17 passed
open http://localhost:8100/admin/oracle/list                  # должно быть 8 строк
```

### Этап 2 — Сиды и первый оракул *(следующий)*

См. `handoff/04-roadmap.md` → «Этап 2».

**План:**
1. `data/seed/druid-tree.json` — 22 периода друидского календаря деревьев из
   `research/02-druid-tree-calendar.md` в формате `{matcher: {type:'date_range',from,to}, plant_slug, weight, reason_for_expert}`.
2. `data/seed/plants.json` — 20–30 растений (минимум те, что встречаются у друидов):
   `slug`, `name_ru`, `name_lat`, `category`, `min_zone_usda`, `hierarchy_potential`,
   опционально `element` / `planet`.
3. Реализовать контракт `oracles/base.py` (Oracle + OracleResult — см. `handoff/03-oracle-interface.md`).
4. `oracles/druid_tree.py`: на вход Person → читает `oracle_entries` для
   `oracle_id='druid_tree'` → возвращает соответствие даты рождения.
5. Зарегистрировать в `oracles/__init__.py` (registry).
6. Pytest: дата `2000-03-05` → должна выпасть `willow` (ива).

**Smoke после завершения:**
```bash
docker compose exec api pytest tests/test_oracle_druid_tree.py -v
# в /admin/oracle-entry/list — десятки строк для druid_tree
```

### Этапы 3–10 — *(не начаты)*

Полный план — в `handoff/04-roadmap.md`.

---

## Стратегия тестирования

- **Бэкенд:** `pytest` внутри контейнера `api` — `docker compose exec api pytest`. Каждый оракул должен иметь юнит-тест с известным «золотым» примером.
- **Smoke-тесты по этапам:** короткие `curl`-сценарии в этом журнале (см. «Как продолжить» под каждым этапом).
- **Фронтенд:** до этапа 7 не пишем (фронта по сути нет). С этапа 7 — ручная проверка в браузере + опционально Chrome DevTools MCP.
- **БД:** `sqladmin` на `/admin` — визуальная проверка после миграций и сидинга.

## Известные особенности окружения

- Каталог проекта содержит пробел и скобки: `Vlad rev1(1)`. В Bash всегда оборачивать в кавычки.
- В домашней директории `/Users/maximlomaev/` инициализирован посторонний git без коммитов — НЕ наш, не трогаем. Наш git живёт строго в `Vlad rev1(1)/.git`.
- Docker Desktop версии 27.4.0, compose 2.31 (на момент 2026-05-05) — всё актуально.
