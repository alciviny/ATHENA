from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import List

from brain.domain.events.base import DomainEvent
from brain.domain.entities.performance_event import PerformanceMetric


@dataclass(frozen=True, kw_only=True, slots=True)
class PerformanceAnalyzed(DomainEvent):
    weak_metrics: List[PerformanceMetric]

    @staticmethod
    def create(student_id: UUID, weak_metrics: List[PerformanceMetric]):
        return PerformanceAnalyzed(
            aggregate_id=student_id,
            weak_metrics=weak_metrics,
        )
