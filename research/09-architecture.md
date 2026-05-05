# Архитектура: модель данных и алгоритм

Цель: спроектировать систему так, чтобы **добавлять новые символические системы** (огам, аюрведу, новые имена) можно было **без переписывания** ядра.

## Ключевая идея

Не "одна большая таблица соответствий", а **набор независимых "оракулов"**, каждый из которых:
- знает свой принцип (друид-деревья / друид-цветы / зодиак / имя / ...)
- умеет на вход взять `Person { дата, время, место, имя, пол, цвет глаз, ... }`
- на выход даёт **список взвешенных растений с пояснением**: `[{ plant_id, weight, reason }]`

Ядро потом **сливает результаты всех оракулов** в один пул, считает совпадения, ранжирует.

## Сущности

```
Person {
  id
  birth_date            # обязательно
  birth_time            # опц., для натальной карты
  birth_place           # опц., для натальной карты
  full_name             # имя, отчество, фамилия (отдельно)
  gender
  eye_color             # blue/grey/green/brown/dark/amber
  
  # параметры участка (вторичные)
  garden_zone_usda
  garden_region
  garden_soil           # сухо/влажно
  garden_sun            # солнце/полутень/тень
  garden_size_m2
  garden_style          # формальный/природный/японский/...
  
  notes                 # для эксперта: что важно знать
}
```

```
Plant {
  id
  name_ru               # "Берёза повислая"
  name_lat              # "Betula pendula"
  category              # tree / shrub / perennial / annual / grass / water / vine
  
  # ботаника
  min_zone_usda
  shelter_friendly      # можно ли укрытием расширять зону
  height_max_m
  width_max_m
  growth_speed          # slow/medium/fast
  
  # условия
  sun                   # sun/part_shade/shade
  soil_moisture         # dry/normal/wet
  soil_type             # sand/loam/clay/acid/...
  
  # символика (универсальная склейка между системами)
  element               # fire/earth/air/water (или несколько)
  gender_energy         # masculine/feminine/neutral
  planet                # Солнце/Луна/Меркурий/...
  chakra                # 1-7 или null
  
  # визуал/эстетика
  bloom_months
  bloom_color
  autumn_color
  evergreen
  
  # практическое
  is_weed_like          # true для осины, клёна ясенелистного и т.п. — не "титульное"
  hierarchy_potential   # how good as a centerpiece tree (1-5)
  availability_ru       # easy/medium/rare
  approx_price_rub
  
  # для рассказа клиенту
  short_story           # 1-2 предложения мифологии
  long_story            # абзац для интерпретации
}
```

```
Oracle {
  id           # 'druid_tree' | 'druid_flower' | 'zodiac' | 'slavic' | 'name' | 'eye_color' | ...
  name_ru
  active       # включён ли в MVP
  weight       # глобальный вес этого оракула в финальной формуле
}
```

```
OracleResult {
  oracle_id
  person_id
  results: [
    { plant_id, weight, reason_for_expert, reason_for_client }
  ]
  meta: { ... }       # например, для друидов — какой период попал
}
```

## Алгоритм пересечений

```
function findPlants(person):
  results = []
  for oracle in active_oracles:
    results += oracle.run(person)  # каждый возвращает свой список

  # 1. Группируем по plant_id
  pool = group_by(results, 'plant_id')
  
  # 2. Для каждого растения считаем
  for entry in pool:
    entry.match_count = unique_oracles_that_voted_for_it
    entry.total_weight = sum(weight × oracle.weight)
    entry.sources = [список оракулов с reasons]
  
  # 3. Применяем фильтры участка
  pool = filter(pool, by climate_zone)
  pool = filter(pool, by garden_conditions: sun/moisture/size)
  
  # 4. Применяем фильтр "дерево-враг" (40 дней до/после)
  pool = remove(pool, enemy_tree(person.birth_date))
  
  # 5. Сортировка
  pool.sort_by(match_count desc, total_weight desc, hierarchy_potential desc)
  
  # 6. Возвращаем top-N (10-15)
  return pool[:15]
```

## Что видит эксперт vs клиент

**Эксперт-режим:**
```
1. ИВА (matches: 4)
   - Друиды-деревья: 1-10 марта, "меланхолия, артистичность"
   - Зодиак (Рак): главное дерево
   - Цвет глаз (голубые): водные
   - Стихия (вода): склейка ×3
   - hierarchy_potential: 4/5
   - Зона: 4 (растёт везде)
   - reason_for_client: "ваше дерево связано с водой и поэтической натурой"

2. РОЗА (matches: 2)
   - Имя (Маргарита → роза через "цветок"): 1.0
   - Цветочный гороскоп друидов (22.06-01.07): главный цветок
   ...

3. ПИОН (matches: 2)
   ...
```

**Клиент-режим (PDF/слайд):**
```
🌿 ВАШИ РАСТЕНИЯ

Главное дерево вашего сада — ИВА.
[красивая иллюстрация / фото]
"Тихая вода, в которой видны звёзды. Это дерево людей, 
которые чувствуют тонко и видят больше, чем говорят."

Сопровождающие растения:
🌹 Роза — цветок имени "Маргарита"
🌸 Пион — символ полноты, цветёт в июне (ваш месяц)
...

Композиция "Место силы" (рекомендация эксперта):
[схема: ива у воды + группа пионов + почвопокровные]
```

Источники (имена оракулов) **не показываются** клиенту. Нет упоминания "по календарю друидов" или "по нумерологии". Это просто "ваше растение".

## Расширение

Чтобы добавить новую систему (например, "огам"):
1. Добавить запись в таблицу `oracles`
2. Заполнить таблицу её соответствий (даты → растения)
3. Реализовать функцию `oracle_ogam.run(person) → [results]`
4. Включить флаг `active=true`
5. Готово — ядро уже её подхватит и начнёт использовать в пересечениях.

## Технологии (предложение)

- **MVP:** одностраничное веб-приложение, БД в JSON-файлах (без сервера). Достаточно для тебя+коллеги.
- **Этап 2 (бот):** перенос в SQLite/Postgres + Telegram-бот.
- **Frontend:** простой React/HTML, форма ввода → результат на одной странице.

Решение по стеку — после того как утрясём содержание.
