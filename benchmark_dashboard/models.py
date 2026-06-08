from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


Status = Literal["ok", "partial", "failed"]


@dataclass
class BenchmarkRow:
    rank: int
    model: str
    organization: str | None
    score: float
    score_unit: str
    date: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BenchmarkSnapshot:
    id: str
    name: str
    category: str
    description: str
    source_url: str
    methodology_url: str | None
    authenticity: str
    update_strategy: str
    fetched_at: str
    status: Status
    rows: list[BenchmarkRow] = field(default_factory=list)
    warning: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["rows"] = [row.to_dict() for row in self.rows]
        return data


@dataclass
class DashboardData:
    generated_at: str
    benchmarks: list[BenchmarkSnapshot]
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "notes": self.notes,
            "benchmarks": [benchmark.to_dict() for benchmark in self.benchmarks],
        }
