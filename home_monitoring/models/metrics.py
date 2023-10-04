from dataclasses import dataclass, field
from typing import List


@dataclass
class MetricRecord:
    name: str
    time: int
    value: float
    dimensions: List[dict[str, str]] = field(default_factory=list)

    def add_dimension(self, name: str, value: str):
        self.dimensions.append({"Name": name, "Value": value})
