# WORK_LOG — журнал прогресса

Живой журнал работы по проекту Vlad rev1. Цель: после сброса контекста сессии любой Claude может открыть этот файл и за минуту понять где мы, что сделано, как проверить и что следующее.

**Для следующей сессии Claude:** прочти в таком порядке — `README.md` → этот файл → `handoff/04-roadmap.md` → текущий «Активный этап» ниже.

---

## Состояние на текущий момент

- **Дата:** 2026-05-05
- **Активный этап:** 2 завершён, переходим на 3 (оркестратор + `POST /recommend`)
- **Что работает:** БД, sqladmin, первый оракул `druid_tree` со всеми 40 entries из research/02, **31/31 pytest зелёные**
- **Блокеров:** нет

## Как проверить, в каком состоянии проект сейчас

```bash
cd "/Users/maximlomaev/projects/Vlad rev1(1)/starter"
docker compose ps                                            # vlad-api, vlad-web в Up
docker compose exec api pytest -q                            # 31 passed
docker compose exec api python -m vlad.seed                  # 8 oracles + 22 plants + 40 entries
docker compose exec api python -c "
from vlad.db import SessionLocal
from vlad.oracles.druid_tree import DruidTreeOracle
from vlad.models import Person
with SessionLocal() as s:
    r = DruidTreeOracle().run(Person(first_name='X', birth_date='2000-03-05'), s)
    print(r[0].plant_slug, '|', r[0].reason_for_client)
"   # должен напечатать: willow | Ваше дерево — Ива. ...
```

В `/admin/plant/list` — 22 строки. В `/admin/oracle-entry/list` — 40 строк (все для `druid_tree`).

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

### Этап 2 — Сиды и первый оракул ✅

**Цель:** есть база растений и первый работающий оракул (друид-деревья).

**Сделано:**
- [x] `data/seed/plants.json` — 22 растения по таблице из `research/02`
  (apple, fir, elm, cypress, poplar, cedar, pine, willow, linden, oak, hazel,
  rowan, maple, walnut, jasmine, chestnut, ash, hornbeam, fig, birch, olive, beech).
  Поля: slug, name_ru, name_lat, category, min_zone_usda, hierarchy_potential,
  short_story (1–2 предложения для клиентского отчёта).
- [x] `data/seed/druid-tree.json` — **40 entries** (18 деревьев × 2 периода + 4
  одиночных знака), формат matcher = `{type: 'date_range_yearly', from: 'MM-DD', to: 'MM-DD'}`.
  Reason_for_expert указывает период и пометку про замену для южных видов.
- [x] `oracles/druid_tree.py` — реализация. Парсит `birth_date` как 'YYYY-MM-DD',
  обходит entries своего id из БД, поддерживает обёрнутый диапазон (12-23..01-01).
- [x] Зарегистрирован в `oracles/__init__.py` (ORACLES dict).
- [x] **14 новых тестов:** параметризованный по 9 ключевым датам (включая 4 одиночных
  знака и обёрнутый Новый год), проход по всем 365 дням года (доказательство, что
  интервалы не пересекаются и не имеют дыр кроме намеренной 21.12), пустота при
  отсутствии/битом birth_date, проверка структуры OracleResult и наличия в registry.

**Заметки и компромиссы:**
- **День 21.12 не покрыт ни одним знаком в research/02** (Инжир до 20.12, Бук
  только 22.12). Оставил как есть — оракул возвращает `[]`. Зафиксировано тестом
  `test_each_date_resolves_to_exactly_one_tree`. Если эксперт скажет «должен быть
  Бук на 21.12 тоже» — добавим entry, тест предупредит о расхождении.
- 29.02 включено в период Сосны (`02-19..02-29`).
- USDA-зоны для южных видов (cypress=7, walnut=6, fig=7, olive=8, beech=6) —
  приближённые. Эксперт уточнит в этапе 6 (фильтры участка). Пока влияет только
  на отображение, фильтрация ещё не подключена.
- «Дерево-враг» (40 дней до/после) и поправка по дате зачатия из research/02 —
  не реализованы, это этап 6 (фильтры).

**Как продолжить с нуля:**
```bash
cd "/Users/maximlomaev/projects/Vlad rev1(1)/starter"
docker compose up -d                                    # alembic upgrade head
docker compose exec api python -m vlad.seed             # 8 oracles + 22 plants + 40 entries
docker compose exec api pytest -q                       # 31 passed
```

### Этап 3 — Оркестратор и API *(следующий)*

См. `handoff/04-roadmap.md` → «Этап 3» и `handoff/03-oracle-interface.md` (там
готовый код оркестратора).

**План:**
1. `core/orchestrator.py` — `recommend(person, db) -> list[dict]`: прогон по
   `ORACLES`, группировка по `plant_slug`, подсчёт `match_count` и `total_weight`,
   сбор `sources[]` для UI эксперта.
2. Pydantic-схемы в `schemas/recommendation.py`: `RecommendInput`, `RecommendOutput`,
   `PoolEntry { plant, match_count, sources[] }`.
3. Роут `POST /recommend` в `routes/recommend.py` — принимает `person_id` или
   прямые поля, вызывает оркестратор, возвращает JSON.
4. Тесты: прогнать оркестратор на тестовом Person, убедиться что в пуле есть
   ожидаемое дерево от `druid_tree`. Сейчас оракул один, так что пул из 1 элемента —
   ОК; станет интереснее когда добавим остальные на этапе 5.

### Этапы 4–10 *(не начаты)*

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
