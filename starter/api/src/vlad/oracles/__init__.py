"""Регистр оракулов. Импортируй здесь все реализации, чтобы оркестратор их видел."""
from .base import Oracle, OracleResult
# from .druid_tree import DruidTreeOracle
# from .druid_flower import DruidFlowerOracle
# from .zodiac import ZodiacOracle


ORACLES: dict[str, Oracle] = {
    # DruidTreeOracle.id: DruidTreeOracle(),
    # DruidFlowerOracle.id: DruidFlowerOracle(),
    # ZodiacOracle.id: ZodiacOracle(),
}

__all__ = ["Oracle", "OracleResult", "ORACLES"]
