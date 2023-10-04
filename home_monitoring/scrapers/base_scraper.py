from abc import ABC, abstractmethod
from home_monitoring.store.metrics_store import MetricRecord
from typing import List


class BaseScraper(ABC):
    def __init__(self, env: str = "prod"):
        self.env = env
        self.access_token = None

    @abstractmethod
    def scrape_metrics(self) -> List[MetricRecord]:
        pass
