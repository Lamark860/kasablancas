# WORK_LOG — журнал прогресса

Живой журнал работы по проекту Vlad rev1. Цель: после сброса контекста сессии любой Claude может открыть этот файл и за минуту понять где мы, что сделано, как проверить и что следующее.

**Для следующей сессии Claude:** прочти в таком порядке — `README.md` → этот файл → [`DECISIONS.md`](DECISIONS.md) (живые архитектурные компромиссы) → `handoff/04-roadmap.md` → текущий «Активный этап» ниже.

---

## Состояние на текущий момент

- **Дата:** 2026-05-05
- **Активный этап:** 4 завершён, переходим на 5 (остальные оракулы)
- **Что работает:** натальная карта через pyswisseph (Moshier), кеш в `natal_charts`, оракул `zodiac`, **реальные пересечения** (5.03.2000 → ива с match_count=2 от druid_tree+zodiac), геокодинг как best-effort при POST /persons. **80/80 pytest зелёные**.
- **Блокеров:** нет

## Как проверить, в каком состоянии проект сейчас

```bash
cd "/Users/maximlomaev/projects/Vlad rev1(1)/starter"
docker compose ps                                                  # vlad-api, vlad-web в Up
docker compose exec api pytest -q                                  # 80 passed

# пересечения вживую
curl -s -X POST -H 'Content-Type: application/json' \
  -d '{"person":{"first_name":"X","birth_date":"2000-03-05"}}' \
  http://localhost:8100/recommend/ | python3 -m json.tool
# pool[0]: willow, match_count=2, sources=[druid_tree, zodiac]
# pool[1]: fig,    match_count=1, sources=[zodiac]
```

Swagger: http://localhost:8100/docs · Админка: http://localhost:8100/admin/ (после первого `/recommend` через id — увидишь кеш в `/admin/natal-chart/list`).

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

### Этап 3 — Оркестратор и API ✅

**Цель:** есть эндпоинт `POST /recommend`, который возвращает пул растений.

**Сделано:**
- [x] `vlad/core/orchestrator.py` — `recommend(person, db)`: прогоняет все
  активные оракулы из `ORACLES` (фильтр по `oracles.active=1`), группирует
  голоса по `plant_slug`, считает `match_count` и `total_weight = vote_weight × oracle_global_weight`,
  обогащает `plant_name_ru` и `plant_short_story` из таблицы plants, сортирует
  по `(match_count desc, total_weight desc)`.
- [x] Pydantic-схемы:
  - `schemas/person.py`: `PersonBase`/`PersonCreate`/`PersonOut` с валидацией
    `birth_date` через regex `\d{4}-\d{2}-\d{2}` и Literal-типов для пола, цвета
    глаз и т.п. (даёт 422 раньше, чем до СheckConstraint).
  - `schemas/recommendation.py`: `RecommendInput` (либо `person_id`, либо inline
    `person`, валидация «ровно одно» через model_validator), `RecommendOutput`
    с `PoolEntry` и `OracleSource`.
- [x] Роуты:
  - `POST /persons/`, `GET /persons/`, `GET /persons/{id}`, `DELETE /persons/{id}`
  - `POST /recommend/` — оба режима (по id и inline)
  - `GET /plants/` — справочник 22 растений
  - `GET /oracles/` — 8 оракулов с пометкой `implemented` (есть ли класс в registry)
- [x] **19 новых тестов** через TestClient + dependency_overrides:
  - оркестратор: ива на 5.03, пустота при отсутствии birth_date, выключение
    оракула через `active=0`, применение глобального weight, обогащение story
  - `/persons` CRUD: create/list/get/delete, 404, валидация regex даты и enum eye_color
  - `/recommend`: inline-режим, по id, валидация «ровно одно», 404 на чужой id,
    пустой пул для непокрытой 21.12
  - `/plants`, `/oracles`: список и пометка implemented

**Заметки и компромиссы:**
- **Тонкий момент SQLite + TestClient:** TestClient гоняет хэндлеры через
  threadpool (anyio), и каждый поток получает свою connection. Для in-memory
  это значит «своя пустая БД». Решение — `StaticPool` в фикстуре `db_session`,
  одна общая connection на все потоки. Без этого роуты-тесты падали с
  `no such table: oracles`. Зафиксировано в `tests/conftest.py`.
- Эфемерный режим `/recommend` принимает inline-Person без сохранения в БД —
  пригодится для публичного бота (этап 10).
- Запись результата в таблицу `recommendations` пока **не делается** —
  history-фича вынесена в этап 9 (полировка). Сейчас оркестратор только считает.
- Пока активен один оракул, поэтому `match_count` всегда = 1. Реальные
  пересечения появятся на этапе 5; сортировка `(match_count, total_weight)`
  заработает «по-настоящему» тогда же.

**Как продолжить с нуля:**
```bash
cd "/Users/maximlomaev/projects/Vlad rev1(1)/starter"
docker compose up -d
docker compose exec api python -m vlad.seed
docker compose exec api pytest -q                        # 50 passed
# и потом — http://localhost:8100/docs, потыкать в Swagger
```

### Этап 4 — Натальная карта + zodiac ✅

**Цель:** автоматический расчёт астропараметров → используется оракулом zodiac.

**Сделано:**
- [x] `vlad/natal/swisseph_wrapper.py` — `calc_chart(birth_date, birth_time, lat, lon, tz)`
  считает позиции 10 планет (Sun…Pluto), назначает знак по эклиптической долготе,
  считает счётчики стихий fire/earth/air/water, асцендент через систему домов
  Плацидус (только если есть time + lat + lon).
- [x] `vlad/natal/cache.py` — `get_or_calc_chart(person, db)`. Для сохранённого
  Person кеширует в таблицу `natal_charts`, для эфемерного — считает без записи.
- [x] `vlad/natal/geocode.py` — best-effort через `geopy + timezonefinder`.
  Сбой не блокирует POST /persons, эксперт может заполнить `birth_lat/lon/tz`
  руками через `/admin`.
- [x] `vlad/oracles/zodiac.py` — берёт `chart.sun_sign`, ищет в БД entries
  с matcher=`{type:'zodiac_sign', sign:...}`. Зарегистрирован в `ORACLES`.
- [x] `data/seed/zodiac.json` — 22 entries (только те растения, что есть в
  `plants.json`; aries и часть дополнений из research/04 пока без записей).
- [x] `POST /persons` — если задан `birth_place` и не заданы `birth_lat/lon`,
  тихо подкачивает геокодом (с graceful-fallback на None при ошибках сети).
- [x] **22 новых теста (всего 80/80):**
  - `test_natal_chart.py` — sun_sign на 5 хорошо изученных дат, асцендент с
    временем+местом, кеширование (повторный вызов не пишет вторую строку).
  - `test_oracle_zodiac.py` — параметризованный по 11 ключевым датам
    (taurus→apple, cancer→willow/ash, leo→oak/cedar, libra→maple/beech,
    sagittarius→rowan/hornbeam/cedar, capricorn→pine), валидность всех
    sign'ов и plant_slug'ов в JSON, наличие в registry.
  - `test_intersections.py` — главный тест архитектуры: 5.03 → willow с
    match_count=2 от druid_tree+zodiac впереди инжира; 25.04 → walnut+apple
    без пересечения; выключение druid через `active=0` оставляет только zodiac.

**Заметки и компромиссы:**
- **Используются Moshier-эфемериды** (`swe.FLG_MOSEPH`), без `.se1` файлов.
  Точность ~3 угловых секунды — с большим запасом для назначения знаков.
  Если позже потребуются прогрессии или близкие аспекты — положим эфемериды
  в `api/ephe/` и снимем флаг.
- Без `birth_time` берём 12:00 UTC. Sun и медленные планеты от этого почти
  не зависят, но Луна на стыке знаков может ошибиться (документировано в
  handoff/05). UI этапа 7 должен предупреждать об этом.
- Геокодинг — сетевой запрос к Nominatim (OSM). При сбое (нет интернета,
  лимит, неизвестное место) Person сохраняется без `birth_lat/lon/tz` —
  это намеренно, не блокирует поток.
- Zodiac покрывает не все знаки и не все растения из `research/04`. Aries
  пуст (барбарис, боярышник, лиственница и т.п. не входят в наши 22
  растения). Цветы и травы тоже отсутствуют. Когда расширим `plants.json` —
  добавим entries без переписывания оракула.
- При POST /recommend через `person_id` оракул автоматически кеширует
  `NatalChart` для этого person; видно в `/admin/natal-chart/list`.

**Как продолжить с нуля:**
```bash
cd "/Users/maximlomaev/projects/Vlad rev1(1)/starter"
docker compose up -d
docker compose exec api python -m vlad.seed             # +zodiac.json (22)
docker compose exec api pytest -q                       # 80 passed
```

### Этап 5 — Остальные оракулы *(следующий)*

См. `handoff/04-roadmap.md` → «Этап 5». По одному оракулу за подход:
1. `druid_flower` — цветочный гороскоп друидов (research/03).
2. `slavic` — славянский древесный гороскоп (research/05).
3. `name` — растение по имени (research/06).
4. `eye_color` — авторская привязка через стихию (research/07).
5. `lunar` — лунный день рождения (research/07).
6. `numerology` — число имени по Пифагору → стихия (research/07).

Для каждого: data/seed/<id>.json + класс-наследник Oracle + регистрация +
тест с известным «золотым» примером.

### Этапы 6–10 *(не начаты)*

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
