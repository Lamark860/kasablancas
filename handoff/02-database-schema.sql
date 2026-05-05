-- ============================================================================
-- Схема БД для проекта Vlad-rev1
-- ----------------------------------------------------------------------------
-- Этот файл — источник истины по структуре. Когда будешь писать SQLAlchemy-
-- модели в api/src/vlad/models/, отталкивайся от него. После того как ORM-
-- модели готовы, генерируй миграции через Alembic — этот файл больше не нужен,
-- он остаётся как документация.
--
-- Совместим с SQLite и PostgreSQL. Различия в типах помечены комментариями.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- ЛЮДИ (клиенты или сам пользователь, для которого делаем подбор)
-- ----------------------------------------------------------------------------
CREATE TABLE persons (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,    -- в Postgres: SERIAL
    
    -- основные данные
    first_name      TEXT NOT NULL,
    middle_name     TEXT,
    last_name       TEXT,
    gender          TEXT CHECK(gender IN ('female', 'male', 'other')),
    
    -- рождение
    birth_date      TEXT NOT NULL,        -- ISO 'YYYY-MM-DD'
    birth_time      TEXT,                 -- ISO 'HH:MM'  (опц.)
    birth_place     TEXT,                 -- 'г. Краснодар, Россия'
    birth_lat       REAL,                 -- заполняется геокодером
    birth_lon       REAL,
    birth_tz        TEXT,                 -- 'Europe/Moscow'
    
    -- внешность (для оракулов "цвет глаз" и т.п.)
    eye_color       TEXT CHECK(eye_color IN ('blue','grey','green','hazel','brown','dark','amber')),
    
    -- участок
    garden_zone_usda    INTEGER,          -- 3..9
    garden_region       TEXT,             -- 'Краснодарский край'
    garden_soil         TEXT CHECK(garden_soil IN ('dry','normal','wet')),
    garden_sun          TEXT CHECK(garden_sun IN ('sun','part_shade','shade','mixed')),
    garden_size_m2      REAL,
    garden_style        TEXT,             -- 'природный' / 'формальный' / 'японский' / ...
    
    -- произвольное
    notes           TEXT,                 -- заметки эксперта
    
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);


-- ----------------------------------------------------------------------------
-- РАСТЕНИЯ (каноничный справочник)
-- ----------------------------------------------------------------------------
CREATE TABLE plants (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- идентификация
    slug            TEXT UNIQUE NOT NULL,         -- 'birch_pendula' — для ссылок из таблиц соответствий
    name_ru         TEXT NOT NULL,                -- 'Берёза повислая'
    name_lat        TEXT,                         -- 'Betula pendula'
    aka             TEXT,                         -- JSON: ["плакучая берёза", "берёза бородавчатая"]
    category        TEXT NOT NULL CHECK(category IN
                        ('tree','shrub','perennial','annual','grass','fern','vine','water','bulb','succulent','herb')),
    
    -- ботаника
    min_zone_usda       INTEGER,                  -- минимальная зимостойкость
    max_zone_usda       INTEGER,                  -- верхняя граница (южнее — плохо)
    shelter_friendly    INTEGER DEFAULT 0,        -- 0/1
    height_max_m        REAL,
    width_max_m         REAL,
    growth_speed        TEXT CHECK(growth_speed IN ('slow','medium','fast')),
    
    -- условия
    sun                 TEXT CHECK(sun IN ('sun','part_shade','shade','sun_or_part_shade','any')),
    soil_moisture       TEXT CHECK(soil_moisture IN ('dry','normal','wet','any')),
    soil_type           TEXT,                     -- 'sand,loam' (CSV) или JSON
    
    -- символика (универсальная склейка между системами — заполняется один раз)
    element             TEXT,                     -- 'fire' | 'earth' | 'air' | 'water' | 'fire,water'
    gender_energy       TEXT CHECK(gender_energy IN ('masculine','feminine','neutral')),
    planet              TEXT,                     -- 'Луна' | 'Венера' | …
    chakra              INTEGER CHECK(chakra BETWEEN 1 AND 7),
    
    -- эстетика
    bloom_months        TEXT,                     -- JSON: [4,5,6]
    bloom_color         TEXT,
    autumn_color        TEXT,
    evergreen           INTEGER DEFAULT 0,
    
    -- практическое (для фильтра эксперта)
    is_weed_like            INTEGER DEFAULT 0,    -- 1 = "сорнякообразное", не "титульное"
    hierarchy_potential     INTEGER CHECK(hierarchy_potential BETWEEN 1 AND 5),
    availability_ru         TEXT CHECK(availability_ru IN ('easy','medium','rare')),
    approx_price_rub        INTEGER,
    
    -- для рассказа клиенту
    short_story         TEXT,                     -- 1-2 предложения мифологии
    long_story          TEXT,                     -- абзац интерпретации
    image_url           TEXT,                     -- путь к иллюстрации
    
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_plants_slug ON plants(slug);
CREATE INDEX idx_plants_category ON plants(category);


-- ----------------------------------------------------------------------------
-- ОРАКУЛЫ (метаданные о системах привязки)
-- ----------------------------------------------------------------------------
CREATE TABLE oracles (
    id              TEXT PRIMARY KEY,             -- 'druid_tree', 'zodiac', 'name', …
    name_ru         TEXT NOT NULL,                -- 'Кельтский гороскоп друидов'
    description     TEXT,
    
    active          INTEGER DEFAULT 1,            -- 0/1 — включён ли в финальный пул
    weight          REAL DEFAULT 1.0,             -- глобальный множитель
    
    -- какие поля Person требует на вход (JSON-массив):
    required_inputs TEXT NOT NULL,                -- '["birth_date"]' / '["full_name","gender"]'
    
    sort_order      INTEGER DEFAULT 100,
    created_at      TEXT DEFAULT (datetime('now'))
);


-- ----------------------------------------------------------------------------
-- СООТВЕТСТВИЯ (одна таблица для всех "табличных" оракулов)
-- ----------------------------------------------------------------------------
-- Не каждый оракул использует эту таблицу. Например, "нумерология имени" и
-- "натальная карта" могут вычислять результат алгоритмически. Но "друид-
-- деревья", "цветочный гороскоп", "знаки зодиака → растения" — все они
-- по сути таблицы вида (период/категория) → (растение).
--
-- Универсальная форма: matcher описывает условие срабатывания (JSON), 
-- plant_slug указывает результат, weight — насколько сильное соответствие.
-- ----------------------------------------------------------------------------
CREATE TABLE oracle_entries (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    oracle_id       TEXT NOT NULL REFERENCES oracles(id) ON DELETE CASCADE,
    
    -- условие срабатывания: гибкий JSON, формат зависит от оракула
    -- примеры:
    --   { "type": "date_range", "from": "03-01", "to": "03-10" }      -- друид-дерево
    --   { "type": "zodiac_sign", "sign": "cancer" }                    -- зодиак
    --   { "type": "name_match", "name": "Маргарита" }                  -- имя
    --   { "type": "eye_color", "color": "blue" }                       -- глаза
    --   { "type": "lunar_day", "day": 15 }                             -- лунный
    matcher         TEXT NOT NULL,                -- JSON
    
    plant_slug      TEXT NOT NULL REFERENCES plants(slug),
    
    weight          REAL DEFAULT 1.0,             -- 0.0..1.0 — сила соответствия
    role            TEXT,                         -- 'main' | 'companion' | 'accent' (опц.)
    
    -- "почему" — текстовое объяснение
    reason_for_expert   TEXT,                     -- "1-10 марта, главное дерево, период 'Ива'"
    reason_for_client   TEXT,                     -- "ваше дерево связано с водой и поэтической натурой"
    
    sort_order      INTEGER DEFAULT 0
);

CREATE INDEX idx_oracle_entries_oracle ON oracle_entries(oracle_id);
CREATE INDEX idx_oracle_entries_plant ON oracle_entries(plant_slug);


-- ----------------------------------------------------------------------------
-- РЕКОМЕНДАЦИИ (история подборов, для повторного открытия и сравнения)
-- ----------------------------------------------------------------------------
CREATE TABLE recommendations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id       INTEGER NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
    
    -- что было на входе (snapshot — на случай если Person потом отредактируют)
    input_snapshot  TEXT NOT NULL,                -- JSON всего, что подавали
    active_oracles  TEXT NOT NULL,                -- JSON: ['druid_tree','zodiac',...]
    
    -- что на выходе (полный пул, до экспертной фильтрации)
    raw_pool        TEXT NOT NULL,                -- JSON: [{plant_slug, matches, sources, ...}]
    
    -- что эксперт оставил (после ручной правки) — опц.
    curated_pool    TEXT,                         -- JSON
    expert_notes    TEXT,
    
    -- метаданные
    title_plant_slug    TEXT REFERENCES plants(slug),  -- "место силы" — главное дерево
    
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_recommendations_person ON recommendations(person_id);


-- ----------------------------------------------------------------------------
-- НАТАЛЬНАЯ КАРТА (кеш результатов pyswisseph)
-- ----------------------------------------------------------------------------
-- Расчёт натальной карты — относительно дорогой. Кешируем результат на Person.
-- ----------------------------------------------------------------------------
CREATE TABLE natal_charts (
    person_id       INTEGER PRIMARY KEY REFERENCES persons(id) ON DELETE CASCADE,
    
    -- основное (для упрощённой астрологии достаточно)
    sun_sign        TEXT,                         -- 'cancer'
    moon_sign       TEXT,
    ascendant_sign  TEXT,
    
    -- стихии и качества (распределение планет)
    fire_count      INTEGER,
    earth_count     INTEGER,
    air_count       INTEGER,
    water_count     INTEGER,
    
    -- полный JSON-дамп — на случай, если позже понадобятся аспекты, дома и т.п.
    full_chart      TEXT NOT NULL,                -- JSON
    
    calculated_at   TEXT DEFAULT (datetime('now'))
);


-- ============================================================================
-- НАЧАЛЬНЫЕ ДАННЫЕ
-- ============================================================================

-- список оракулов (заполняется один раз при первом старте — импортируется из
-- data/seed/oracles.json)
INSERT INTO oracles (id, name_ru, description, required_inputs, weight) VALUES
  ('druid_tree',   'Кельтский гороскоп друидов (деревья)', 'Период рождения → дерево', '["birth_date"]', 1.0),
  ('druid_flower', 'Цветочный гороскоп друидов',           'Период рождения → цветок', '["birth_date"]', 0.8),
  ('zodiac',       'Знаки зодиака → растения',             'Знак Солнца → планетарные растения', '["birth_date"]', 1.0),
  ('slavic',       'Славянский древесный гороскоп',        'Период рождения → дерево по славянской традиции', '["birth_date"]', 0.7),
  ('name',         'Имя → растение',                       'Этимология/святцы/символика имени', '["first_name"]', 0.6),
  ('eye_color',    'Цвет глаз → стихия → растения',        'Авторская привязка через стихию', '["eye_color"]', 0.5),
  ('lunar',        'Лунный день рождения → растение',      'Лунный календарь', '["birth_date"]', 0.7),
  ('numerology',   'Нумерология имени → стихия',           'Число имени по Пифагору', '["first_name"]', 0.4);

-- (растения и oracle_entries наполняются из JSON-сидов)
