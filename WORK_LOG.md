# WORK_LOG — журнал прогресса

Живой журнал работы по проекту Vlad rev1. Цель: после сброса контекста сессии любой Claude может открыть этот файл и за минуту понять где мы, что сделано, как проверить и что следующее.

**Для следующей сессии Claude:** прочти в таком порядке — `README.md` → этот файл → [`DECISIONS.md`](DECISIONS.md) (живые архитектурные компромиссы) → `handoff/04-roadmap.md` → текущий «Активный этап» ниже.

---

## Состояние на текущий момент

- **Дата:** 2026-05-05
- **Этап 9 ✅ завершён** (расширенный — треки A, D, E, B5, F1; B6/B7 отложены пользователем). Этап 10 (публичный бот) **заморожен** до отдельной отмашки.
- **Активный этап:** **9.5 — добивка данных и тестирование** (промежуточный между 9 и 10). Что делаем здесь: коллега тестирует инструмент на реальных гостьях, расширяет содержимое справочников (растения, оракулы), даёт фидбэк по PDF/UI. Я правлю по факту находок.
- **Что работает:** полный флоу `/intake` (с blur-валидацией места рождения через OSM + выбором кандидата) → `/expert/{id}` (с историей версий, per-plant заметками, кураторским режимом) → `/client/{id}` → PDF (без некрасивых разрывов на 2-й странице). Админка для эксперта-непрограммиста: структурные формы matcher, хелп-тексты, безопасный reseed (upsert), кнопка «Выгрузить в JSON». Бэк: **157/157 pytest зелёные**.
- **Блокеров:** нет.

## Как проверить, в каком состоянии проект сейчас

```bash
cd "/Users/maximlomaev/projects/Vlad rev1(1)/starter"
docker compose exec api pytest -q                                  # 117 passed

# демонстрация фильтров: тот же клиент, та же магия + чистка под участок
curl -s -X POST -H 'Content-Type: application/json' \
  -d '{"person":{"first_name":"Ева","birth_date":"2000-03-05","eye_color":"blue","garden_zone_usda":4}}' \
  http://localhost:8100/recommend/ | python3 -m json.tool
# pool:    willow (matches=3), apple (matches=1)
# excluded: fig (USDA 7 > 4), oak (дерево-враг)
```

Сравнение «сырой/фильтрованный»: добавить `?apply_filters=false` к URL.

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

### Этап 5 — Остальные оракулы ⚠️ частично

**Цель:** все 8 оракулов из MVP-набора работают.

**Сделано (3 оракула + расширены тесты):**
- [x] `oracles/numerology.py` + `data/seed/numerology.json` — 15 entries по
  таблице из `research/07`. Считает число имени по Пифагору в кириллице
  (helper `name_number`), редуцирует до 1..9.
- [x] `oracles/eye_color.py` + `data/seed/eye-color.json` — 8 entries по
  `research/07`. Покрыты blue/grey/brown/hazel/amber.
- [x] `oracles/name.py` + `data/seed/name.json` — 9 entries по `research/06`
  (этимологический подход A). Сравнение case-insensitive по `first_name`.
- [x] Все три зарегистрированы в `oracles/__init__.py`.
- [x] **+25 тестов (всего 105/105):**
  - `test_oracle_numerology.py` — параметризованный по 5 именам, edge-cases.
  - `test_oracle_eye_color.py` — параметризованный по 5 цветам.
  - `test_oracle_name.py` — case-insensitive, неизвестное имя, два plant'а
    для одного имени (Дарья → oak+ash).
  - `test_intersections.py` дополнен главным демонстрационным тестом этапа:
    Ева, 5.03.2000, голубые глаза → ива с match_count=3 от 3 оракулов.

**Отложено (3 оракула, см. DECISIONS.md §18):**
- ⏸ `druid_flower` — нужны 36 цветов/трав в `plants.json` (mak, лилия,
  ромашка, наперстянка…), расширение справочника требует эксперта.
- ⏸ `slavic` — research/05 сам неполный, нужен канонический источник.
- ⏸ `lunar` — research/07 пишет «источники не очень устойчивы», требует
  расчёта лунного дня через pyswisseph.

**Заметки и компромиссы:**
- §16: eye_color и numerology покрывают только наши 22 растения; «зелёные»,
  «чёрные» глаза и число 7 — без полного покрытия.
- §17: name-оракул — стартовая выборка из 9 имён, расширяется по факту
  обращений клиентов (как и предлагает research/06).

**Как продолжить с нуля:**
```bash
cd "/Users/maximlomaev/projects/Vlad rev1(1)/starter"
docker compose up -d
docker compose exec api python -m vlad.seed   # 5 оракулов поднимут entries
docker compose exec api pytest -q             # 105 passed
```

### Этап 6 — Фильтры эксперта ✅

**Цель:** учёт климата и условий участка.

**Сделано:**
- [x] `vlad/core/filters.py` — 5 фильтров:
  - **USDA-зона**: если `Plant.min_zone_usda > Person.garden_zone_usda` —
    выкидываем (для южанина в зоне 4 фигу не предлагаем).
  - **`sun`**: совместимость `Plant.sun` (sun / part_shade / shade /
    sun_or_part_shade / any) c `Person.garden_sun` (sun / part_shade / shade /
    mixed). `mixed` означает «у меня есть и солнце и тень — подходит всё».
  - **`soil_moisture`**: dry / normal / wet, плюс растения с `any`.
  - **«Дерево-враг»**: алгоритмически считается из druid_tree. Берётся
    окно ±40 дней от `birth_date`, любое дерево друидов, чей период
    пересекается с этим окном (кроме своего) — исключается. Для Евы
    05.03 это: cypress, poplar, cedar, pine, linden, oak, hazel, rowan,
    maple — 9 деревьев.
  - **`is_weed_like`**: не выкидываем (символическое попадание ценно), но
    `total_weight × 0.5` и пометка в `notes`.
- [x] `apply_filters_flag` в `core/orchestrator.recommend()` (default True).
- [x] `?apply_filters=false` query-параметр у `POST /recommend` — для
  «сырого» взгляда.
- [x] В `RecommendOutput` добавлены `filters_applied: bool` и
  `excluded: list[Exclusion {plant_slug, reason}]` — UI этапа 7 покажет
  отсеянные растения с причиной.
- [x] **+12 тестов (всего 117/117):**
  - `test_filters.py` — каждый из 5 фильтров изолированно, граничные
    случаи (нет данных у Person → no-op, битый birth_date → no-op,
    `sun_or_part_shade` совместим с обоими, `is_weed_like` пере-сортирует
    пул после понижения веса).
  - `test_intersections.py` дополнен парой sirye/filtered.
  - `test_routes_recommend.py` — оба режима `?apply_filters` через
    TestClient.

**Заметки и компромиссы:**
- §19: фильтры sun и soil код-уровне реализованы, но в `data/seed/plants.json`
  поля не заполнены — без эксперта-ландшафтника. Сейчас оба фильтра no-op
  для наших 22 растений; станут активными как только сиды дополнят.
- §20: `apply_filters=true` — дефолт. Эксперт обычно хочет видеть
  практическую рекомендацию; «сырой» режим есть как вариант.

**Как продолжить с нуля:**
```bash
cd "/Users/maximlomaev/projects/Vlad rev1(1)/starter"
docker compose up -d
docker compose exec api python -m vlad.seed
docker compose exec api pytest -q                       # 117 passed
```

### Этап 7 — UI эксперта ✅

**Цель:** UI этапа 1 — эксперт может ввести клиента и увидеть пул.

**Сделано:**
- [x] `web/assets/styles/victorian.css` — токены и утилиты из
  `victorian-styles.jsx` (палитра, шрифты, рамки, кнопки, формы, таблицы,
  «бумажная» зернистость). `globals.css` свёрнут до базовых сбросов.
- [x] Шрифты IM Fell English + UnifrakturCook + EB Garamond + Cormorant
  Garamond + IBM Plex Mono подключены через Google Fonts CDN в `app.head`
  (формула из `Prototype.html`, добавлен Cormorant Garamond).
- [x] `composables/useApi.ts` — типизированная обёртка: `Person`, `PersonInput`,
  `PoolEntry`, `OracleSource`, `Exclusion`, `RecommendOutput`, методы
  `listPersons / getPerson / createPerson / deletePerson / recommend / listOracles`.
- [x] `components/OracleBadge.vue` — мини-бейдж «источник» с tooltip-`reason_for_expert`.
- [x] `components/PlantCard.vue` — карточка растения: иконка, имя+slug,
  лента OracleBadge, краткая история, причины-цитаты от каждого оракула,
  правый блок со звёздами + match_count + total_weight + notes (например
  «is_weed_like — вес 0.5»).
- [x] `pages/index.vue` — реестр клиентов (GET /persons/ + кнопка «новая гостья»,
  кнопка «↻ обновить»).
- [x] `pages/intake.vue` — форма ввода (имя × 3, дата/время/место, пол, взгляд,
  fieldset «Сад» = регион + USDA-зона + свет + почва). Отправка POST /persons,
  после успеха — редирект на `/expert/{id}`. Ошибки бэка — в красную плашку.
- [x] `pages/expert/[id].vue` — экспертный лист: masthead с гостьей, основная
  колонка `PlantCard[]`, правая колонка с `fontes` (active_oracles),
  чек-боксом `apply_filters` (re-fetch на тогглинге через `watch` в
  `useAsyncData`) и блоком `exclusi`.
- [x] **Браузерный smoke** через Chrome DevTools MCP: `/` → `/intake` →
  заполнил Еву 5.03.2000 (Москва, blue, USDA 4) → `/expert/2` рендерит
  Иву (3 пересечения, вес 2.45) + Яблоню (от имени, 0.60), исключены fig
  и oak. Тоггл фильтров переключает на сырой пул (4 растения с инжиром и
  дубом). Консоль чистая.

**Зачищенные грабли:**
- **CORS-блокер:** SSR ходил из docker-сети на `http://api:8000` и работал,
  но клиентский CSR-fetch к `http://localhost:8100` падал на CORS — pydantic-settings
  не парсит `CORS_ORIGINS=http://localhost:3100` из `.env` как список (ждёт
  JSON). Чинится валидатором в `Settings`: принимаем CSV. Дефолт обновлён на
  `http://localhost:3100`. См. DECISIONS.md §21.

**Заметки и компромиссы:**
- §21: иконки растений — пока заглушка (стилизованный SVG-кружок с веточкой)
  вместо набора `Botanical kind="willow|peony|…"` из `victorian-styles.jsx`.
  В `plants.json` поле `image_url`/`icon` не заведено. На этапе 8 (клиент-режим
  + PDF) понадобится. Пока упорядочено через единый стиль карточек.
- Шрифт `IM Fell English SC` для display-заголовков заменён на
  `UnifrakturCook` (как в Prototype.html) — он лучше читается и отдаётся
  с Google Fonts стабильно.

**Как продолжить с нуля:**
```bash
cd "/Users/maximlomaev/projects/Vlad rev1(1)/starter"
docker compose up -d
docker compose exec api python -m vlad.seed
docker compose exec api pytest -q                 # 117 passed
open http://localhost:3100/                       # реестр гостий
# /intake → форма; /expert/{id} → пул с фильтрами
```

### Этап 8 — Клиент-режим + PDF ✅

**Цель:** красивый отчёт, который можно показать клиенту или распечатать.

**Сделано:**
- [x] `schemas/curated.py` — `CuratedSave` (вход PUT) + `RecommendationOut`.
- [x] Роуты в `routes/persons.py`:
  - `PUT /persons/{id}/recommendation` — пересчитывает оркестратор и
    сохраняет/обновляет одну Recommendation на Person (последняя
    побеждает; повторный PUT не плодит строк, см. DECISIONS.md §11).
    Сохраняет `input_snapshot` (срез ключевых полей Person), `active_oracles`,
    `raw_pool`, `curated_pool`, `title_plant_slug`, `expert_notes`.
  - `GET /persons/{id}/recommendation` — последняя сохранённая.
- [x] `vlad/pdf/__init__.py` — `render_client_report()` через Jinja2-шаблон
  + `weasyprint`. Берёт `Plant.name_lat` из БД, `name_ru/short_story` из
  `rec.raw_pool`. Если `title_plant_slug` есть, ставит его первым.
- [x] `vlad/pdf/templates/client_report.html` — A4-шаблон в стиле
  `ScreenClient` прототипа: овальная плашка с буквой главного дерева,
  заголовок UnifrakturCook, italic-цитата, грид «сопровождающих»,
  фрейм с заметкой эксперта.
- [x] `routes/reports.py` — `GET /reports/{person_id}.pdf`. RFC 5987
  кодирование кириллического имени файла в Content-Disposition (см.
  DECISIONS.md §23).
- [x] **+6 тестов (всего 123):** `test_curated.py` — PUT создаёт строку,
  повторный PUT обновляет (id не меняется), 404 пока не сохранено и
  для unknown person, PDF возвращает application/pdf, начинается с `%PDF`,
  >4 КБ.
- [x] Frontend: `useApi.ts` дополнен `saveCurated/getCurated/reportPdfUrl`;
  `PlantCard.vue` принимает `curatable/curated/isTitle` и эмитит
  `toggle-curated/set-title`; `pages/expert/[id].vue` обзавёлся блоком
  «collectio» с textarea для заметок и кнопкой «сохранить и открыть лист
  гостьи»; новая `pages/client/[id].vue` рендерит лист без источников и
  весов, кнопка «скачать pdf» → `<a href target=_blank>` на `/reports/{id}.pdf`.
- [x] **End-to-end smoke через curl:** Ева 5.03.2000, USDA 4 →
  PUT с `curated=[willow,apple,birch], title=willow, notes="вокруг ивы…"`
  → GET PDF: 18 КБ, magic `%PDF`, заголовок
  `filename*=UTF-8''hortus-animae-%D0%95%D0%B2%D0%B0-3.pdf`. Сохранил в
  `uploads/eva-report.pdf`.

**Заметки и компромиссы:**
- §22: иконки растений в PDF — единая «инициала-в-овале» (первая буква
  главного дерева в круглой плашке). Полный набор `Botanical` SVG из
  `victorian-styles.jsx` пока не перенесён.
- §23: имя файла в Content-Disposition закодировано по RFC 5987
  (`filename* + ASCII-fallback`) — иначе кириллица в `first_name`
  ломает HTTP-заголовок.
- §24: WeasyPrint работает с системными засечками, без подгрузки IM Fell
  из Google Fonts. CSS-шаблон ссылается на UnifrakturCook + Cormorant
  Garamond; если их нет в контейнере, fallback идёт на Garamond/Georgia
  (для PDF этого достаточно, ничего не «ломается»).

**Как продолжить с нуля:**
```bash
cd "/Users/maximlomaev/projects/Vlad rev1(1)/starter"
docker compose up -d
docker compose exec api python -m vlad.seed
docker compose exec api pytest -q                    # 123 passed

# end-to-end smoke
PID=$(curl -s -X POST -H 'Content-Type: application/json' \
  -d '{"first_name":"Ева","birth_date":"2000-03-05","eye_color":"blue","garden_zone_usda":4}' \
  http://localhost:8100/persons/ | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
curl -s -X PUT -H 'Content-Type: application/json' \
  -d '{"curated_slugs":["willow","apple"],"title_plant_slug":"willow"}' \
  http://localhost:8100/persons/$PID/recommendation > /dev/null
curl -s -o eva.pdf http://localhost:8100/reports/$PID.pdf && head -c 4 eva.pdf
# ожидание: "%PDF"
```

### Этап 9 (расширенный) — наполнение и шлифовка ✅

**Цель:** инструмент готов к ежедневной работе коллеги-эксперта без участия программиста.

Этап разделён на треки (см. `DECISIONS.md` приложение «Этап 9»):
- **Трек A — админка для эксперта** ✅ закрыт.
- **Трек B5 — шрифты и центрирование PDF** ✅ закрыт.
  - **B6 (локальные .woff2 для PDF)** и **B7 (SVG-иконки растений)** — пользователь принял решение **не делать сейчас**. Остаются как кандидаты на этап 9.5/после, если коллега скажет что критично.
- **Трек C — контент** ⏸ ждёт фидбэк коллеги (цветы/травы в plants.json, sun/soil_moisture, канон для slavic/lunar/druid_flower) — переезжает в этап 9.5.
- **Трек D — история и заметки** ✅ закрыт.
- **Трек E — точечные улучшения UX** ✅ закрыт (E1 разрывы PDF, E2 удаление гостьи).
- **Трек F — валидация ввода** ✅ закрыт (F1 blur-геокод).

#### Трек A — админка для эксперта ✅

**Что сделано:**
- [x] **A1+A2:** в `/admin/oracle-entry/{create,edit}` сырое JSON-поле `matcher` заменено на структурные виртуальные поля. Под каждый из 5 типов матчера — свой UI:
  - `date_range_yearly`: «с (MM-DD)» + «по (MM-DD)» + Regexp-валидатор
  - `zodiac_sign`: dropdown 12 знаков
  - `name_pythagorean_number`: integer 1..9
  - `eye_color`: dropdown 7 цветов
  - `name_match`: текстовое поле
  Реализовано через `scaffold_form` → подкласс с виртуальными полями + override `process` (prefill из `obj.matcher` при edit) + `validate` (проверяет sub-поле под выбранный тип) + `on_model_change` (собирает обратно `data["matcher"]`, удаляет виртуальные ключи). FK поля `oracle_id`, `plant_slug` — отдельные SelectField со списком из БД (sqladmin сам их выкидывает как FK columns).
  Описания (form_args description) проставлены на ключевых полях `Plant` (slug, hierarchy_potential, min_zone_usda, sun, soil_moisture, is_weed_like, ...), `Oracle` (active, weight, sort_order), `OracleEntry` (vote_weight, role, reason_*).
- [x] **A3:** `vlad/seed.py` переведён на **безопасный upsert по составному ключу** `(oracle_id, plant_slug, json.dumps(matcher, sort_keys=True))`. Ручные правки эксперта в `/admin` больше не теряются при reseed. Старое жёсткое поведение доступно по флагу `--prune-missing`. **Отменяет §3** в `DECISIONS.md`, см. §26.
- [x] **A4:** `vlad/dump_seed.py` + кнопка «Выгрузить в JSON» в `/admin` (`SeedDumpView`, sqladmin BaseView). Эксперт правит данные через UI, программист потом запускает `python -m vlad.dump_seed` или коллега жмёт кнопку — JSON-файлы перезаписываются, можно зафиксировать в git.

**Тестов добавлено:** +20 (10 — admin matcher form, 4 — seed upsert/prune, 6 — dump round-trip + view smoke). Всего **143 passed**.

**Заметки и компромиссы:**
- §25: matcher через виртуальные поля Form, не через нативный JSONField. Цена возврата минимальная.
- §26: reseed теперь upsert, а не truncate. Отменяет §3.
- §27: страница seed-dump в `/admin` рендерится без sqladmin layout (standalone-HTML). Операция редкая, кнопка есть в боковом меню.

**Как продолжить с нуля:**
```bash
cd "/Users/maximlomaev/projects/Vlad rev1(1)/starter"
docker compose up -d
docker compose exec api python -m vlad.seed                 # безопасный upsert
docker compose exec api pytest -q                           # 143 passed
open http://localhost:8100/admin/oracle-entry/create        # структурный matcher
open http://localhost:8100/admin/seed-dump                  # кнопка выгрузки
```

#### Трек D — история и заметки на растение ✅

**Что сделано:**
- [x] **D9 (заметки эксперта на каждое растение):**
  - В `Recommendation.curated_pool` хранится новый формат `list[{plant_slug, expert_note}]`. Старые записи `list[str]` нормализуются на чтении (см. §28).
  - `CuratedSave` принимает `curated: [{plant_slug, expert_note}]`. Поле `curated_slugs: list[str]` оставлено для backward compat — превращается в `curated` без заметок через `model_validator`.
  - На `/expert/{id}` под каждой PlantCard в curated-режиме теперь есть `<textarea>` с заметкой. State хранится как `Map<slug, note>`.
  - В `/client/{id}` и в PDF — заметка курсивом в плашке `border-left:terra` под коротким описанием растения. Главное дерево получает свой блок `main-tree__note`.
- [x] **D8 (история рекомендаций):**
  - `PUT /persons/{id}/recommendation` теперь **плодит новую строку** при каждом вызове (раньше обновлял in-place — отменено §29 относительно §11).
  - Новые эндпоинты: `GET /persons/{id}/recommendations` (список, новейшая первая, без тяжёлого `raw_pool`) и `GET /persons/{id}/recommendations/{rec_id}` (конкретная версия).
  - На `/expert/{id}` боковая панель «historiae · Версии подбора» появляется при ≥2 версиях. У каждой строки — дата, главное дерево, размер пула, кнопка «загрузить» (заполняет local state из выбранной версии, эксперт жмёт «сохранить» — создаётся новая версия из этой).
  - `GET /persons/{id}/recommendation` (сингулярный) и PDF продолжают использовать последнюю версию по `id`.

**Тестов добавлено:** +7 (1 unit на legacy-нормализацию pdf, 2 — per-plant notes API + PDF render, 4 — история: list/empty/404, конкретная версия, плодит новые).
Всего **150 passed**.

**Заметки и компромиссы:**
- §28: формат `curated_pool` в БД — теперь `list[{plant_slug, expert_note}]`. Старые `list[str]` нормализуются на чтении в `pdf._normalize_curated` и `RecommendationOut._normalize`. Цена возврата минимальная.
- §29: PUT `/recommendation` теперь плодит новую строку. Отменяет §11. Эксперт может вернуть прошлую версию через UI; миграция БД не нужна (UNIQUE на person_id никогда не было).

**Как продолжить с нуля:**
```bash
cd "/Users/maximlomaev/projects/Vlad rev1(1)/starter"
docker compose up -d
docker compose exec api python -m vlad.seed
docker compose exec api pytest -q                           # 150 passed

# end-to-end smoke с историей и заметками
PID=$(curl -s -X POST -H 'Content-Type: application/json' \
  -d '{"first_name":"Аня","birth_date":"1992-07-15","eye_color":"brown","garden_zone_usda":5}' \
  http://localhost:8100/persons/ | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
curl -s -X PUT -H 'Content-Type: application/json' \
  -d '{"curated":[{"plant_slug":"willow","expert_note":"у пруда"},{"plant_slug":"apple","expert_note":"карлик"}],"title_plant_slug":"willow"}' \
  http://localhost:8100/persons/$PID/recommendation > /dev/null
curl -s -X PUT -H 'Content-Type: application/json' \
  -d '{"curated_slugs":["willow","apple","birch"],"title_plant_slug":"willow"}' \
  http://localhost:8100/persons/$PID/recommendation > /dev/null
curl -fsS http://localhost:8100/persons/$PID/recommendations | python3 -m json.tool   # 2 версии
open http://localhost:3100/expert/$PID                                                 # боковая панель «historiae»
```

#### Трек B (частично) — шрифты и разрывы PDF ✅ B5+E1

**B5:** font-size +2px на сайте по ступеням (11→13, 12→14, 13→15, 14→16); +1pt в PDF (10→11, 11→12, 13→14). Mono-eyebrow 8-9px и display-заголовки не трогали. Затронуты `victorian.css` + 6 страниц/компонентов (43 правила) + `client_report.html`.
Иконка-инициал главного дерева в `/client/{id}` и в PDF: `position:absolute + flex` срывал центрирование в WeasyPrint — переведено на `inline-flex` без absolute.

**E1 (PDF, разрывы при 3+ растениях):** добавлены `page-break-inside: avoid` на `.main-tree`, `.other`, `.notes`; `page-break-after: avoid` на `.others__eyebrow` (заголовок не висит отдельно от карточек). Главное дерево, отдельные карточки-спутники и общая заметка не рвутся пополам — PDF разбивается по разумным границам.

**B6 (локальные .woff2) и B7 (SVG Botanical) — отложены пользователем.**

#### E2 — удаление гостьи на главной ✅

На `/index.vue` рядом с кнопкой «пул растений →» добавлена кнопка «× удалить»: `window.confirm` → `DELETE /persons/{id}` (cascade удаляет все Recommendation + NatalChart) → `refresh`. Ошибки показываются в плашке под списком.

#### F1 — blur-валидация места рождения ✅

До этого `birth_place` геокодился на бэке best-effort: опечатка → молча null, неоднозначность → молча первый кандидат. Эксперт не видел расхождений с реальностью, асцендент тихо не считался.

**Бэк:** новый эндпоинт `GET /geocode/?q=...&limit=5` (роут `routes/geocode.py`). `natal/geocode.py` расширен функцией `search_places` (`Nominatim.geocode(exactly_one=False)` + `tz` через `timezonefinder`), `GeoResult` получил поле `label`. Старый `geocode_place` оставлен как backward-compat для POST `/persons` без явных координат.

**Фронт `/intake.vue`:** поле «Место» имеет blur-handler. Состояния:
- `idle` — пусто, ничего не показано
- `searching` — серая плашка «ищу координаты…»
- `one` (1 кандидат) — зелёный блок с label + координаты (auto-select)
- `many` (2+) — radio-список с label и координатами
- `not_found` (0) — красная плашка «место не найдено»
- `error` — красная плашка о недоступности геокодера

Кнопка «↻ найти заново» рядом с лейблом — на случай повторной проверки. `submit` блокируется если `birth_place` введён, но кандидат не выбран (`placeNeedsResolution`). Если эксперт оставил поле пустым — submit идёт без координат, как раньше.

**Тестов добавлено:** +7 на route + search_places (моки geopy через monkeypatch). Реальный Nominatim не дёргаем в тестах. Всего **157/157 passed**.

**Заметки и компромиссы:**
- §30: search_places вызывается на blur, не на ввод. Nominatim имеет rate limit 1 req/sec, debounced-автокомплит лёгко ловит 429. Для редкой формы (одна гостья за сессию) blur — оптимальный трейдофф.
- §31: бэк по-прежнему делает best-effort geocode при POST `/persons` без координат — для admin/curl-сценариев и backward-compat.

### Этап 9.5 — добивка данных и тестирование (промежуточный) ⚠️ в работе

**Цель:** прогнать инструмент на 5-10 реальных гостьях коллеги, найти что не сходится с её ожиданиями, дополнить справочники, отполировать места по факту.

**Природа этого этапа:** не код, а **обкатка**. Большая часть работы — у коллеги (тестировать, давать фидбэк, заполнять данные). Мои действия — реактивные, по её находкам.

**Что входит:**
- [ ] **Контент (трек C):** дополнить `plants.json` цветами/травами (разблокирует `druid_flower` и закроет дыры zodiac/eye_color/numerology), заполнить `sun`/`soil_moisture` для 22 деревьев (оживит §19), канонический набор для `slavic`/`lunar`. Делается **через админку** коллегой.
- [ ] **Тестирование на реальных гостьях:** проверить, что подбор «звучит» эксперту, что заметки удобно вводить, что PDF читается клиентом.
- [ ] **Правки по фидбэку коллеги:**
  - возможно вернуться к B6 (локальные .woff2) если шрифты в PDF критично выпадают на тех машинах, куда отправляется PDF
  - возможно вернуться к B7 (SVG-иконки растений) если коллега решит что иконки-«заглушки» неприемлемы для клиента
  - другие точечные UX-правки
- [ ] **Дополнительные кандидаты на работу** (моё предложение, не зафиксировано):
  - `ADMIN-GUIDE.md` — короткая инструкция коллеге «как добавить запись через админку»
  - удаление версии из истории (DELETE на конкретный rec_id + крестик в блоке historiae)
  - поиск по имени и индикатор «есть рекомендация» в реестре
  - импорт CSV (упростит коллеге расширение `plants.json` через Excel)

**Когда завершён:** когда коллега довольна инструментом, прогнала ≥5 гостей, дала добро на этап 10 (или решила оставить этап 9.5 «навсегда» — это тоже валидный финал, см. memory: «продукт ближайшее время и возможно навсегда не на поток, а как инструмент для эксперта»).

### Этап 10 — заморожен ⏸

Telegram-бот, переезд на Postgres, ЮKassa, лендинг (см. roadmap). Запускается **не как продолжение этапа 9.5**, а отдельной темой когда метод обкатан на ≥20 клиентах. См. `feedback_stage10_frozen.md` в памяти.

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
