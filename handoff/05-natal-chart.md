# Натальная карта через pyswisseph

## Что это и зачем

Натальная карта — снимок неба в момент рождения. Для нашего проекта она нужна чтобы:
1. Получить **знак Солнца** (зодиакальный) — основной вход для оракула `zodiac`
2. Получить **знак Луны** — эмоции, "женское" дерево
3. Получить **асцендент** (восходящий знак) — "внешнее" дерево, для образа сада
4. Распределение по **стихиям** (огонь/земля/воздух/вода) — для подбора растений по доминирующей стихии
5. (Позже, опционально) дома, аспекты, транзиты — для углублённой версии

## Установка

```bash
# через uv
uv add pyswisseph

# или через pip
pip install pyswisseph
```

Для точного расчёта Swiss Ephemeris нужны **файлы эфемерид** (`*.se1`). Скачай один раз с [astro.com/ftp/swisseph/ephe](https://www.astro.com/ftp/swisseph/ephe/) — нужны `seas_18.se1`, `semo_18.se1`, `sepl_18.se1` (это покроет 1800–2400 годы). Положи в `api/ephe/`.

Если файлы не скачать — pyswisseph переключится на встроенные **Moshier-эфемериды** (точность ~3 секунды дуги, для астрологии достаточно). То есть строго говоря необязательно, но лучше с файлами.

## Геокодирование места рождения

Натальная карта требует **широту и долготу** места рождения. Пользователь вводит "Краснодар" — нужно превратить в `lat=45.04, lon=38.97, tz=Europe/Moscow`.

Варианты:
1. **Nominatim** (OpenStreetMap) — бесплатно, без ключа, но требует User-Agent и лимит ~1 запрос/сек. Для внутреннего инструмента отлично.
2. **Yandex Geocoder** — бесплатный лимит, нужен API-ключ.
3. **Готовый GeoNames-дамп** — 11 МБ JSON со всеми городами мира, оффлайн. Самое надёжное.

Для timezone: библиотека `timezonefinder` (получает tz по lat/lon).

```python
# api/src/vlad/natal/geocode.py
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

geocoder = Nominatim(user_agent='vlad-rev1')
tf = TimezoneFinder()

def geocode(place: str) -> tuple[float, float, str]:
    loc = geocoder.geocode(place)
    if not loc:
        raise ValueError(f"Не удалось определить место: {place}")
    tz = tf.timezone_at(lat=loc.latitude, lng=loc.longitude)
    return loc.latitude, loc.longitude, tz
```

## Расчёт карты

```python
# api/src/vlad/natal/swisseph_wrapper.py
import swisseph as swe
from dataclasses import dataclass, asdict
from datetime import datetime
import zoneinfo
from pathlib import Path

# указать путь к эфемеридам один раз при старте
swe.set_ephe_path(str(Path(__file__).parent.parent.parent.parent.parent / 'ephe'))

SIGNS = ['aries','taurus','gemini','cancer','leo','virgo',
         'libra','scorpio','sagittarius','capricorn','aquarius','pisces']

ELEMENTS = {
    'fire':  ['aries','leo','sagittarius'],
    'earth': ['taurus','virgo','capricorn'],
    'air':   ['gemini','libra','aquarius'],
    'water': ['cancer','scorpio','pisces'],
}

PLANETS = [
    ('sun',     swe.SUN),
    ('moon',    swe.MOON),
    ('mercury', swe.MERCURY),
    ('venus',   swe.VENUS),
    ('mars',    swe.MARS),
    ('jupiter', swe.JUPITER),
    ('saturn',  swe.SATURN),
    ('uranus',  swe.URANUS),
    ('neptune', swe.NEPTUNE),
    ('pluto',   swe.PLUTO),
]


@dataclass
class NatalChart:
    sun_sign: str
    moon_sign: str
    ascendant_sign: str | None       # None если не задано время
    
    # позиции всех планет: { 'sun': {'sign': 'cancer', 'lon_deg': 105.3}, ... }
    planets: dict
    
    # распределение
    fire_count: int
    earth_count: int
    air_count: int
    water_count: int


def calc_chart(
    birth_date,            # date
    birth_time,            # time | None
    lat: float | None,
    lon: float | None,
    tz: str | None,
) -> NatalChart:
    # 1. собираем datetime в UTC
    if birth_time and tz:
        local = datetime.combine(birth_date, birth_time)
        local = local.replace(tzinfo=zoneinfo.ZoneInfo(tz))
        utc = local.astimezone(zoneinfo.ZoneInfo('UTC'))
    else:
        # время неизвестно — берём 12:00 UTC (Солнце/большие планеты не сильно зависят)
        utc = datetime(birth_date.year, birth_date.month, birth_date.day, 12, 0,
                       tzinfo=zoneinfo.ZoneInfo('UTC'))
    
    # 2. юлианский день
    jd = swe.julday(utc.year, utc.month, utc.day,
                    utc.hour + utc.minute/60 + utc.second/3600)
    
    # 3. позиции планет
    planets = {}
    elem_count = {'fire': 0, 'earth': 0, 'air': 0, 'water': 0}
    for name, code in PLANETS:
        result = swe.calc_ut(jd, code)
        # result — кортеж; первый элемент содержит долготу в [0]
        lon_deg = result[0][0]
        sign_idx = int(lon_deg // 30)
        sign = SIGNS[sign_idx]
        planets[name] = {'sign': sign, 'lon_deg': lon_deg}
        for elem, lst in ELEMENTS.items():
            if sign in lst:
                elem_count[elem] += 1
                break
    
    # 4. асцендент — только если есть точное время и место
    asc_sign = None
    if birth_time and lat is not None and lon is not None:
        # 'P' — система домов Плацидус (самая распространённая)
        houses = swe.houses(jd, lat, lon, b'P')
        asc_lon = houses[1][0]   # ASC
        asc_sign = SIGNS[int(asc_lon // 30)]
    
    return NatalChart(
        sun_sign=planets['sun']['sign'],
        moon_sign=planets['moon']['sign'],
        ascendant_sign=asc_sign,
        planets=planets,
        fire_count=elem_count['fire'],
        earth_count=elem_count['earth'],
        air_count=elem_count['air'],
        water_count=elem_count['water'],
    )
```

## Использование в оракулах

`zodiac` оракул:

```python
# oracles/zodiac.py
class ZodiacOracle(Oracle):
    id = 'zodiac'
    name_ru = 'Знаки зодиака'
    required_inputs = ['birth_date']
    
    def run(self, person, db):
        # лезем за натальной картой (с кешированием)
        chart = get_or_calc_chart(person, db)
        
        # ищем все entries с matcher = {"type": "zodiac_sign", "sign": chart.sun_sign}
        entries = db.query(OracleEntry).filter_by(oracle_id=self.id).all()
        results = []
        for e in entries:
            if e.matcher.get('type') == 'zodiac_sign' and e.matcher.get('sign') == chart.sun_sign:
                results.append(OracleResult(...))
        return results
```

## Кеширование

Расчёт натальной карты — несколько миллисекунд, не критично, но лучше кешировать в таблице `natal_charts` (см. SQL-схему). При первом обращении — считаем и сохраняем, при повторных — берём из БД.

```python
def get_or_calc_chart(person, db):
    cached = db.query(NatalChartModel).filter_by(person_id=person.id).first()
    if cached:
        return NatalChart(**json.loads(cached.full_chart))
    
    chart = calc_chart(person.birth_date, person.birth_time,
                       person.birth_lat, person.birth_lon, person.birth_tz)
    db.add(NatalChartModel(
        person_id=person.id,
        sun_sign=chart.sun_sign,
        moon_sign=chart.moon_sign,
        ascendant_sign=chart.ascendant_sign,
        fire_count=chart.fire_count,
        earth_count=chart.earth_count,
        air_count=chart.air_count,
        water_count=chart.water_count,
        full_chart=json.dumps(asdict(chart)),
    ))
    db.commit()
    return chart
```

## Что точно работает, что нет

| Параметр | Без времени рождения | С временем |
|----------|---------------------|------------|
| Знак Солнца | ✓ (точно) | ✓ |
| Знак Луны | ⚠ Луна сдвигается на знак за ~2.5 суток. Если родился на стыке — может быть неверно. | ✓ |
| Знаки остальных планет | ✓ для медленных (Марс+) | ✓ |
| Асцендент | ✗ (вообще нельзя) | ✓ |
| Дома | ✗ | ✓ |
| Аспекты | ⚠ для близких к стыку | ✓ |

В UI: если время не введено, прячь блок "асцендент" и показывай дисклеймер "для точного расчёта Луны желательно знать время".

## Расширение в будущее

Когда захочешь углубить астрологию:
- **Аспекты** — `swe.calc_ut` дай позиции, считай угловые расстояния, вытаскивай соединения/трины/квадратуры
- **Транзиты** — пересчитай карту на сегодня, сравни с натальной → "сегодня Венера в трине к вашей натальной Луне → можно сажать цветы"
- **Прогрессии, дирекции** — те же функции, другая дата

Всё это — внутри `swisseph_wrapper.py`. Снаружи — расширяешь dataclass `NatalChart` новыми полями.
