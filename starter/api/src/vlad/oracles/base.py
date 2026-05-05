"""Контракт оракула. См. handoff/03-oracle-interface.md."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import ClassVar

from sqlalchemy.orm import Session


@dataclass
class OracleResult:
    plant_slug: str
    weight: float = 1.0
    role: str | None = None
    reason_for_expert: str = ""
    reason_for_client: str = ""
    meta: dict = field(default_factory=dict)


class Oracle(ABC):
    id: ClassVar[str]
    name_ru: ClassVar[str]
    required_inputs: ClassVar[list[str]]
    
    @abstractmethod
    def run(self, person, db: Session) -> list[OracleResult]:
        ...
    
    def can_run_for(self, person) -> bool:
        for f in self.required_inputs:
            v = getattr(person, f, None)
            if v in (None, "", []):
                return False
        return True
