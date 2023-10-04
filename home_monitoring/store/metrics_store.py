from abc import ABC
from typing import List

from home_monitoring.models.metrics import MetricRecord


class MetricsStore(ABC):
    def write_metric(self, record: MetricRecord) -> None:
        pass

    def write_metrics(self, records: List[MetricRecord]) -> None:
        pass
