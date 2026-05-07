from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True)
class Outcome:
    description: str
    callback: Callable[["JobResult"], None]
    status: str | None = None
    output_files: list[str] | None = None


def effective_status(outcome: Outcome, index: int) -> str:
    return outcome.status if outcome.status is not None else str(index)


@dataclass(frozen=True)
class JobResult:
    job_id: str
    status: str
    target: str
    duration_seconds: float
    files: dict[str, bytes]
    stdout: str
