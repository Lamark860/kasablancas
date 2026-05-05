# Контракт оракула + пример реализации

Это **самая важная архитектурная штука** в проекте. Если правильно зафиксировать контракт — добавление новых символических систем станет работой на 30 минут (один файл + один JSON), а не рефакторингом ядра.

## Контракт

Каждый оракул — это класс, наследующий `Oracle`. У него есть три части:

1. **Метаданные** (`id`, `name_ru`, `required_inputs`) — статически в классе
2. **Метод `run(person, db) -> list[OracleResult]`** — вся логика
3. **Регистрация** — добавление в `oracles/__init__.py`

### `oracles/base.py`

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar
from sqlalchemy.orm import Session

from vlad.models.person import Person


@dataclass
class OracleResult:
    """Один голос оракула за конкретное растение."""
    plant_slug: str
    weight: float                        # 0.0..1.0 — сила голоса внутри оракула
    role: str | None = None              # 'main' | 'companion' | 'accent' | None
    reason_for_expert: str = ''          # "1-10 марта, период 'Ива'"
    reason_for_client: str = ''          # "ваше дерево связано с водой"
    meta: dict | None = None             # любые доп. данные (напр., какой период попал)


class Oracle(ABC):
    # --- метаданные ---
    id: ClassVar[str]                    # 'druid_tree'
    name_ru: ClassVar[str]               # 'Кельтский гороскоп друидов'
    required_inputs: ClassVar[list[str]] # ['birth_date'] / ['first_name'] / ...
    
    # --- логика ---
    @abstractmethod
    def run(self, person: Person, db: Session) -> list[OracleResult]:
        """
        Получает Person и сессию БД (чтобы читать oracle_entries из таблицы).
        Возвращает список голосов. Может быть пустым, если для данного Person
        оракул ничего не выдал (например, неизвестный знак, нет имени).
        """
        ...
    
    # --- утилита: проверка что у Person есть всё нужное ---
    def can_run_for(self, person: Person) -> bool:
        for field in self.required_inputs:
            if getattr(person, field, None) in (None, '', []):
                return False
        return True
```

## Пример: `druid_tree.py`

Самый простой и наглядный оракул — кельтский гороскоп друидов. Берёт `birth_date`, ищет соответствующий период, возвращает дерево.

### Данные: `data/seed/druid-tree.json`

```json
[
  {
    "matcher": { "type": "date_range_yearly", "from": "12-24", "to": "01-20" },
    "plant_slug": "apple",
    "role": "main",
    "weight": 1.0,
    "reason_for_expert": "Друиды: 24.12–20.01 — Яблоня. Любовь, благополучие.",
    "reason_for_client": "Ваше дерево — Яблоня. Древний символ любви и заботы."
  },
  {
    "matcher": { "type": "date_range_yearly", "from": "01-21", "to": "02-17" },
    "plant_slug": "fir",
    "role": "main",
    "weight": 1.0,
    "reason_for_expert": "Друиды: 21.01–17.02 — Пихта.",
    "reason_for_client": "Ваше дерево — Пихта. Сила, благородство, стойкость."
  }
]
```

### Реализация: `oracles/druid_tree.py`

```python
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select

from vlad.models.person import Person
from vlad.models.oracle import OracleEntry
from .base import Oracle, OracleResult


class DruidTreeOracle(Oracle):
    id = 'druid_tree'
    name_ru = 'Кельтский гороскоп друидов'
    required_inputs = ['birth_date']
    
    def run(self, person: Person, db: Session) -> list[OracleResult]:
        if not self.can_run_for(person):
            return []
        
        bd: date = person.birth_date
        mmdd = bd.strftime('%m-%d')
        
        # тянем все entries этого оракула из БД
        entries = db.execute(
            select(OracleEntry).where(OracleEntry.oracle_id == self.id)
        ).scalars().all()
        
        results = []
        for e in entries:
            m = e.matcher  # уже распарсенный JSON
            if m.get('type') != 'date_range_yearly':
                continue
            
            if self._in_range(mmdd, m['from'], m['to']):
                results.append(OracleResult(
                    plant_slug=e.plant_slug,
                    weight=e.weight,
                    role=e.role,
                    reason_for_expert=e.reason_for_expert,
                    reason_for_client=e.reason_for_client,
                    meta={'period': f"{m['from']}–{m['to']}"},
                ))
        
        return results
    
    @staticmethod
    def _in_range(mmdd: str, start: str, end: str) -> bool:
        """Проверка попадания MM-DD в диапазон. Учитывает переход через год (24.12-20.01)."""
        if start <= end:
            return start <= mmdd <= end
        else:
            return mmdd >= start or mmdd <= end
```

### Регистрация: `oracles/__init__.py`

```python
from .base import Oracle, OracleResult
from .druid_tree import DruidTreeOracle
from .druid_flower import DruidFlowerOracle
from .zodiac import ZodiacOracle
# ...

ORACLES: dict[str, Oracle] = {
    o.id: o() for o in [
        DruidTreeOracle,
        DruidFlowerOracle,
        ZodiacOracle,
        # …
    ]
}

__all__ = ['Oracle', 'OracleResult', 'ORACLES']
```

## Оркестратор (использует все оракулы)

`core/orchestrator.py`:

```python
from collections import defaultdict
from sqlalchemy.orm import Session

from vlad.models.person import Person
from vlad.models.oracle import Oracle as OracleMeta
from vlad.oracles import ORACLES, OracleResult


def recommend(person: Person, db: Session) -> list[dict]:
    # 1. какие оракулы активны (флаг в БД)
    active_meta = {m.id: m for m in db.query(OracleMeta).filter_by(active=True).all()}
    
    # 2. собираем голоса
    all_votes: list[tuple[str, OracleResult]] = []  # (oracle_id, result)
    for oracle_id, oracle in ORACLES.items():
        if oracle_id not in active_meta:
            continue
        for res in oracle.run(person, db):
            all_votes.append((oracle_id, res))
    
    # 3. группируем по plant_slug
    pool: dict[str, dict] = defaultdict(lambda: {
        'plant_slug': None,
        'match_count': 0,
        'total_weight': 0.0,
        'sources': [],   # [{oracle_id, oracle_name, weight, reason_expert, reason_client, role}]
    })
    
    for oracle_id, r in all_votes:
        entry = pool[r.plant_slug]
        entry['plant_slug'] = r.plant_slug
        entry['match_count'] += 1
        entry['total_weight'] += r.weight * active_meta[oracle_id].weight
        entry['sources'].append({
            'oracle_id': oracle_id,
            'oracle_name': active_meta[oracle_id].name_ru,
            'weight': r.weight,
            'role': r.role,
            'reason_expert': r.reason_for_expert,
            'reason_client': r.reason_for_client,
        })
    
    # 4. сортировка: по match_count, потом по total_weight
    result = sorted(
        pool.values(),
        key=lambda x: (x['match_count'], x['total_weight']),
        reverse=True,
    )
    
    # 5. (фильтры участка — отдельным шагом, см. core/filters.py)
    return result
```

## Как добавить новый оракул

Допустим, хочешь добавить **огам** (древний кельтский алфавит, у каждой буквы — дерево, и каждая буква = период года).

1. **Создай данные**: `data/seed/ogham.json` — таблица `(period, plant_slug, weight, reasons)`
2. **Создай файл**: `oracles/ogham.py` — наследник `Oracle`, реализует `run()`
3. **Зарегистрируй**: добавь в `ORACLES` в `__init__.py`
4. **Добавь метаданные**: `INSERT INTO oracles (...)` или через миграцию
5. **Готово.** Оркестратор подхватит автоматически.

Никаких других файлов трогать не нужно. Это и есть та "расширяемость", о которой шла речь с самого начала.

## Тесты

Каждый оракул должен иметь юнит-тест:

```python
# tests/test_oracles/test_druid_tree.py
def test_druid_tree_apple_period():
    person = Person(first_name='Test', birth_date=date(2000, 1, 1))
    results = DruidTreeOracle().run(person, db)
    assert len(results) == 1
    assert results[0].plant_slug == 'apple'
```

Это страховка на тот случай, когда через полгода ты забудешь, что и как считается.
