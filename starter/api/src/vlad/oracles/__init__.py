"""Регистр оракулов.

Чтобы добавить новый оракул:
1. Создать файл oracles/<id>.py с классом-наследником Oracle.
2. Импортировать его здесь и добавить в ORACLES.
3. Убедиться, что в data/seed/oracles.json есть метаданные с тем же id.
4. Если оракул табличный — положить data/seed/<id>.json (с дефисами вместо _).
5. Написать юнит-тест в tests/test_oracle_<id>.py.

Оркестратор (этап 3) автоматически прогоняет все ORACLES.values() для Person.
"""
from .base import Oracle, OracleResult
from .druid_tree import DruidTreeOracle
from .eye_color import EyeColorOracle
from .name import NameOracle
from .numerology import NumerologyOracle
from .zodiac import ZodiacOracle


ORACLES: dict[str, Oracle] = {
    DruidTreeOracle.id: DruidTreeOracle(),
    ZodiacOracle.id: ZodiacOracle(),
    NumerologyOracle.id: NumerologyOracle(),
    EyeColorOracle.id: EyeColorOracle(),
    NameOracle.id: NameOracle(),
}

__all__ = ["Oracle", "OracleResult", "ORACLES"]
